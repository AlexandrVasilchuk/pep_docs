from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException


REQUEST_ERROR_FORMAT = 'Возникла ошибка при загрузке страницы {url}. {error}'
TAG_NOT_FOUND_FORMAT = 'Не найден тег {tag} {attrs}'


def get_response(session, url, encoding='UTF-8'):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException as error:
        raise ConnectionError(REQUEST_ERROR_FORMAT.format(url=url, error=error))


def cook_soup(session, url, encoding='UTF-8', features='lxml'):
    return BeautifulSoup(
        get_response(session, url, encoding).text, features=features
    )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs if attrs is not None else {}))
    if searched_tag is None:
        raise ParserFindTagException(
            TAG_NOT_FOUND_FORMAT.format(tag=tag, attrs=attrs)
        )
    return searched_tag
