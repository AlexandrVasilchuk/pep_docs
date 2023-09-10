import logging
import re
from collections import defaultdict
from urllib.parse import urljoin

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
from utils import find_tag, cook_soup


NOT_FOUND_ERROR_FORMAT = (
    'При поиске по ссылке {url} в ' 'теге <{tag_name}> ничего не нашлось'
)
DOWNLOAD_COMPLETE_FORMAT = 'Архив был загружен и сохранён: {archive_path}'
LOGS_ARGS_FORMAT = 'Аргументы командной строки {args}'


def whats_new(session):
    soup = cook_soup(session, WHATS_NEW_URL)
    sections = soup.select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1'
    )
    result = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections, colour='GREEN'):
        version_a_tag = section.find('a')
        version_link = urljoin(WHATS_NEW_URL, version_a_tag['href'])
        soup = cook_soup(session, version_link)
        result.append(
            (
                version_link,
                find_tag(soup, 'h1'),
                find_tag(soup, 'dl').text.replace('\n', ' '),
            )
        )
    return result


def latest_versions(session):
    soup = cook_soup(session, MAIN_DOC_URL)
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise ValueError(
                NOT_FOUND_ERROR_FORMAT.format(url=MAIN_DOC_URL, tag_name='ul')
            )
    result = []
    for a_tag in a_tags:
        match = re.search(
            r'Python (?P<version>\d.\d+) \((?P<status>.*)\)', a_tag.text
        )
        if match:
            result.append((a_tag['href'],) + match.groups())
        else:
            result.append((a_tag['href'], a_tag.text))
    return result


def download(session):
    soup = cook_soup(session, DOWNLOADS_URL)
    pdf_a4_link = soup.select_one('table.docutils a[href$="pdf-a4.zip"]')[
        'href'
    ]
    archive_url = urljoin(DOWNLOADS_URL, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    response = session.get(archive_url)
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(DOWNLOAD_COMPLETE_FORMAT.format(archive_path=archive_path))


def pep(session):
    soup = cook_soup(session, PEP_TABLE_URL)
    section_block = find_tag(soup, 'section', attrs={'id': 'numerical-index'})
    table = find_tag(section_block, 'tbody')
    results = defaultdict(int)
    logs = []
    for table_line in tqdm(table.find_all('tr')):
        main_table_status = find_tag(table_line, 'td').text[1:]
        url = find_tag(table_line, 'a').get('href')
        packet_url = urljoin(PEP_TABLE_URL, url)
        packet_soup = cook_soup(session, packet_url)
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
            logs.append(
                f'{packet_url}'
                f' Статус в карточке: {card_status} '
                f'Ожидаемые статусы: {expected}'
            )
        packet_status = (
            packet_info.find(text=re.compile('Status.*'))
            .parent.find_next_sibling()
            .text
        )
        results[packet_status] += 1
    for log in logs:
        logging.info(log)
    return [
        ('Статус', 'Количество'),
        *results.items(),
        ('Итого', sum(results.values())),
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
    logging.info(LOGS_ARGS_FORMAT.format(args=args))
    session = CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    try:
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
    except Exception as error:
        logging.exception(error, stack_info=True)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
