__author__ = 'ZiYuan'

from utils import get_doc_tree_from_url
import logging
import global_logger

_logger = logging.getLogger(__name__)


class PLOSArticle:
    __xpath = {
        "title": "//h1[@id='artTitle']",
        "abstract": "//div[@id='artText']/div[contains(@class,'abstract')]/*[self::p or self::h2]",
        "main_text": "//div[@id='artText']/div[contains(@class,'section') \
            and contains(@id, 'section')]/*[self::p or self::h2]"
        }

    SUCCESS = 0
    FAILURE = 1

    def __init__(self, url):
        self.title = None
        self.abstract = None
        self.main_text = None
        self.url = url

    @staticmethod
    def __combine_sections(nodes):
        if len(nodes) > 0:
            if nodes[-1].tag == "h2":
                nodes = nodes[:-1]
        return '\n'.join([node.text_content() for node in nodes])

    def parse_url(self):
        page_tree = get_doc_tree_from_url(self.url)

        if page_tree is not None:
            title_nodes = page_tree.xpath(PLOSArticle.__xpath['title'])
            if len(title_nodes) == 1:
                self.title = title_nodes[0].text_content()
                abstract_nodes = page_tree.xpath(PLOSArticle.__xpath['abstract'])
                self.abstract = PLOSArticle.__combine_sections(abstract_nodes)
                if self.abstract is None:
                    self.abstract = ""
                main_text_nodes = page_tree.xpath(PLOSArticle.__xpath['main_text'])
                self.main_text = PLOSArticle.__combine_sections(main_text_nodes)
            else:
                _logger.warning("Found %d title(s) in %s" % (len(title_nodes), self.url))
                return PLOSArticle.FAILURE
        else:
            _logger.warning("Cannot download %s. Skipped." % self.url)
            return PLOSArticle.FAILURE

        return PLOSArticle.SUCCESS

    def __str__(self):
        return "\n".join([self.abstract, self.main_text])