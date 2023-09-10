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
    DOWNLOADS_DIR,
)
from outputs import control_output
from utils import find_tag, cook_soup


NOT_FOUND_ERROR_FORMAT = (
    'При поиске по ссылке {url} в ' 'теге <{tag_name}> ничего не нашлось'
)
DOWNLOAD_COMPLETE_FORMAT = 'Архив был загружен и сохранён: {archive_path}'
LOGS_ARGS_FORMAT = 'Аргументы командной строки {args}'
INCONGRUITY_STATUSES_FORMAT = (
    '{packet_url}'
    ' Статус в карточке: {card_status} '
    'Ожидаемые статусы: {expected}'
)
START_PARSING = 'Парсер запущен!'
END_PARSING = 'Парсер завершил работу.'


def whats_new(session):
    logs = []
    soup = cook_soup(session, WHATS_NEW_URL)
    sections = soup.select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1 > a'
    )
    result = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for a_tag in tqdm(sections, colour='GREEN'):
        version_link = urljoin(WHATS_NEW_URL, a_tag['href'])
        try:
            soup = cook_soup(session, version_link)
            result.append(
                (
                    version_link,
                    find_tag(soup, 'h1').text,
                    find_tag(soup, 'dl').text.replace('\n', ' '),
                )
            )
        except ValueError as error:
            logs.append(error)
    for log in logs:
        logging.error(log)
    return result


def latest_versions(session):
    soup = cook_soup(session, MAIN_DOC_URL)
    a_tags = soup.select(
        'div.sphinxsidebarwrapper ul:-soup-contains("All versions") a'
    )
    if a_tags is None:
        raise KeyError(
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
    downloads_dir = BASE_DIR / DOWNLOADS_DIR
    downloads_dir.mkdir(exist_ok=True)
    with open(downloads_dir / filename, 'wb') as file:
        file.write(response.content)
    logging.info(DOWNLOAD_COMPLETE_FORMAT.format(archive_path=downloads_dir))


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
        try:
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
                    INCONGRUITY_STATUSES_FORMAT.format(
                        packet_url=packet_url,
                        card_status=card_status,
                        expected=expected,
                    )
                )
            packet_status = (
                packet_info.find(text=re.compile('Status.*'))
                .parent.find_next_sibling()
                .text
            )
            results[packet_status] += 1
        except ValueError as error:
            logs.append(error)
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
    logging.info(START_PARSING)
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
        logging.exception(
            error,
            f'Неизвестное значение mode - {parser_mode}',
            stack_info=True,
        )
    logging.info(END_PARSING)


if __name__ == '__main__':
    main()
