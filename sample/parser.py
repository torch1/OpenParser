import bs4
import requests

class Webpage:
    def __init__(self, html):
        self.html = html
        _parse()

    def _parse():
        pass
        # todo

def webpage_from_url(url):
    return Webpage(requests.get(url).text)

# simple alias for constructor
def webpage_from_text(html):
    return Webpage(html)
