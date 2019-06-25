'''
    Задание:
        Реализовать простой http-прокси-сервер,
        запускаемый локально (порт на ваше усмотрение),
        который показывает содержимое страниц Хабра.
        Прокси должен модицифировать текст на страницах следующим образом:
        после каждого слова из шести букв должен стоять значок «™».

    Примечание:
        Код размещен в urls.py сугубо по причинам максимальной лаконичности.
        Как минимум должны быть выделены отдельные сущности:
            views, core, helpers, constants, tests, ...
'''


import requests
import bs4
import re
from urllib.parse import urlparse, urlunparse

from django.urls import re_path
from django.http import HttpResponse


SOURCE_HOST = 'habr.com'
TRADE_MARK = '™'
SIX_LENGTHED_WORD_PATTERN = re.compile(r'\b([\w\’]{6})\b')


def complete_content(content):
    '''

    >>> complete_content('We were late, although it didn’t matter.')
    'We were late, although it didn’t™ matter™.'

    '''

    return re.sub(SIX_LENGTHED_WORD_PATTERN, r'\1' + TRADE_MARK, content)


def complete_tag(tag, host):
    if tag.name == 'a' and 'href' in tag.attrs:
        url_parts = urlparse(tag.attrs['href'])
        if url_parts.netloc == SOURCE_HOST:
            url_parts = url_parts._replace(scheme='http', netloc=host)
            tag.attrs['href'] = url_parts.geturl()

    for content in tag.contents:
        if isinstance(content, bs4.element.NavigableString):
            content.replaceWith(complete_content(content))


def complete_request_text(text, host):
    '''

    >>> complete_request_text( \
        '<a href="https://habr.com/ru/news/t/0/">It didn’t matter.</a>', \
        'local' \
    )
    '<html><body><a href="http://local/ru/news/t/0/">It didn’t™ matter™.\
</a></body></html>'
    >>> complete_request_text( \
        '<a href="https://ya.ru">Найдётся всё</a>', \
        'local' \
    )
    '<html><body><a href="https://ya.ru">Найдётся всё\
</a></body></html>'

    '''

    soup = bs4.BeautifulSoup(text, features='lxml')
    for tag in soup.findAll(None, recursive=True):
        complete_tag(tag, host)

    return str(soup)


def index(request):
    url = urlunparse(('https', SOURCE_HOST, request.path, None, None, None))
    try:
        req = requests.get(url)
    except Exception as e:
        return HttpResponse(
            'Exception ({}) was raised '.format(str(e)),
            status=500
        )

    if req.status_code != 200:
        return HttpResponse(req.text, status=req.status_code)

    content = complete_request_text(req.text, request.get_host())

    return HttpResponse(content)


urlpatterns = [
    re_path(r'^.*$', index, name='index'),
]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
