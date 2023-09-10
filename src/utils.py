import logging

from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException


REQUEST_ERROR_FORMAT = 'Возникла ошибка при загрузке страницы {url}'
FAILED_URL_FORMAT = 'Сбойный url - {url}. В ответ ничего не пришло!'
TAG_NOT_FOUND_FORMAT = 'Не найден тег {tag} {attrs}'


def cook_soup(session, url, encoding='UTF-8', features='lxml'):
    try:
        response = session.get(url)
        response.encoding = encoding
        if response is None:
            logging.exception(FAILED_URL_FORMAT.format(url=url))
            return
        return BeautifulSoup(response.text, features=features)
    except RequestException:
        raise RequestException(REQUEST_ERROR_FORMAT.format(url=url))


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        raise RequestException(REQUEST_ERROR_FORMAT.format(url=url))


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs if attrs is not None else {}))
    if searched_tag is None:
        raise ParserFindTagException(
            TAG_NOT_FOUND_FORMAT.format(tag=tag, attrs=attrs)
        )
    return searched_tag
