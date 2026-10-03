"""Резерв для учебных страниц блока 3, если BeautifulSoup пока недоступен.

Это ограниченный разбор конкретной разметки каталога, не замена BeautifulSoup
для произвольного сайта. Использует только стандартную библиотеку Python.
"""
from html.parser import HTMLParser


class _CatalogParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.next_page = None
        self.current = None
        self.field = None
        self.field_tag = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article' and 'listing' in attrs.get('class', '').split():
            self.current = {'listing_id': attrs['data-id']}
        if tag == 'a' and 'next' in attrs.get('class', '').split():
            self.next_page = attrs.get('href')
        if self.current is not None and attrs.get('data-field'):
            self.field = attrs['data-field']
            self.field_tag = tag
            self.current[self.field] = ''
            if self.field == 'title':
                self.current['href'] = attrs.get('href')

    def handle_data(self, data):
        if self.current is not None and self.field:
            self.current[self.field] += data

    def handle_endtag(self, tag):
        if tag == self.field_tag and self.current is not None:
            self.current[self.field] = self.current[self.field].strip()
            self.field = self.field_tag = None
        if tag == 'article' and self.current is not None:
            self.rows.append(self.current)
            self.current = None


def parse_catalog_stdlib(html):
    """Возвращает (список карточек, ссылка «Следующая» либо None)."""
    parser = _CatalogParser()
    parser.feed(html)
    parser.close()
    return parser.rows, parser.next_page
