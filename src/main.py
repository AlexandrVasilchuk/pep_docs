import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests_cache import CachedSession
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (
    BASE_DIR,
    MAIN_DOC_URL,
    PEP_TABLE_URL,
    EXPECTED_STATUS,
    WHATS_NEW_URL,
    DOWNLOADS_URL,
)
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):
    response = get_response(session, WHATS_NEW_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections = div_with_ul.find_all('li', class_='toctree-l1')
    result = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections, colour='GREEN'):
        version_a_tag = section.find('a')
        href = version_a_tag['href']
        version_link = urljoin(WHATS_NEW_URL, href)
        response = get_response(session, version_link)
        if response is None:
            return
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        result.append((version_link, h1.text, dl.text.replace('\n', ' ')))
    return result


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не нашлось')
    result = []
    for a_tag in a_tags:
        link = a_tag['href']
        match = re.search(
            r'Python (?P<version>\d.\d+) \((?P<status>.*)\)', a_tag.text
        )
        if match:
            result.append((link,) + match.groups())
        else:
            result.append((link, a_tag.text))
    return result


def download(session):
    response = get_response(session, DOWNLOADS_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    table = find_tag(soup, 'table', attrs={'class': 'docutils'})
    pdf_a4_link = find_tag(
        table, 'a', attrs={'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    archive_url = urljoin(DOWNLOADS_URL, pdf_a4_link.get('href'))
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    response = session.get(archive_url)
    archive_path = downloads_dir / filename
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    response = get_response(session, PEP_TABLE_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    section_block = find_tag(soup, 'section', attrs={'id': 'numerical-index'})
    table = find_tag(section_block, 'tbody')
    result = {}
    for table_line in tqdm(table.find_all('tr')):
        main_table_status = find_tag(table_line, 'td').text[1:]
        url = find_tag(table_line, 'a').get('href')
        packet_url = urljoin(PEP_TABLE_URL, url)
        packet_response = get_response(session, packet_url)
        if packet_response is None:
            return
        packet_soup = BeautifulSoup(packet_response.content, features='lxml')
        packet_info = find_tag(
            packet_soup, 'dl', attrs={'class': 'rfc2822 field-list simple'}
        )
        card_status = (
            packet_info.find(text=re.compile('Status.*'))
            .parent.find_next_sibling()
            .text
        )
        expected = EXPECTED_STATUS.get(main_table_status)
        if card_status not in expected:
            logging.info(
                f'{packet_url}'
                f' Статус в карточке: {card_status} '
                f'Ожидаемые статусы: {expected}'
            )
        packet_status = (
            packet_info.find(text=re.compile('Status.*'))
            .parent.find_next_sibling()
            .text
        )
        result[packet_status] = result.setdefault(packet_status, 0) + 1
    return [
        ('Статус', 'Количество'),
        *result.items(),
        ('Total', sum(result.values())),
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки {args}')
    session = CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
