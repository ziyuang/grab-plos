from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
from lxml import html
import logging

_logger = logging.getLogger(__name__)


def get_doc_tree_from_url(url, max_attempts=20):
    attempt = 0
    page = None
    page_request = Request(url)
    while attempt < max_attempts:
        try:
            page = urlopen(page_request).read().decode('utf8')
            break
        except (TimeoutError, URLError, HTTPError, ConnectionError) as e:
            _logger.warning('Error: "%s". Retrying...' % str(e))
            attempt += 1

    if attempt == max_attempts:
        _logger.error('Number of attempts reached limit. Fail to open %s.' % page_request.full_url)
        return None

    assert page is not None
    page_tree = html.fromstring(page)
    return page_tree
