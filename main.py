__author__ = 'ZiYuan'


from urllib.parse import urlsplit
from utils import get_doc_tree_from_url
from plosarticle import PLOSArticle
import logging
import re
import pathlib


_logger = logging.getLogger("main")
_logger.setLevel(logging.INFO)
_logger.addHandler(logging.StreamHandler())


def parse_article_urls(issue_url):
    doc_tree = get_doc_tree_from_url(issue_url)
    div_nodes = doc_tree.xpath("//div[@class='section']")
    url_base = "http://" + urlsplit(issue_url).netloc
    article_urls = {}
    for div in div_nodes:
        section_name = ""
        for elem in div.iter("h2"):
            section_name = elem.text

        assert section_name != ""
        a_nodes = div.xpath(".//a[@title='Read Open Access Article']")
        a_nodes = [a_node for a_node in a_nodes if a_node.getparent().tag != "li"]
        hrefs = [node.get("href") for node in a_nodes]
        for href in hrefs:
            assert not href.startswith("http")
        urls = [url_base + href for href in hrefs]
        article_urls[section_name] = urls
    return article_urls


def parse_issue_urls(archive_url):
    url_base = "http://" + urlsplit(archive_url).netloc
    doc_tree = get_doc_tree_from_url(archive_url)
    li_year_nodes = doc_tree.xpath("//li[contains(@class, 'slide')]")
    issue_urls = {}
    for year_node in li_year_nodes:
        a_nodes = year_node.xpath(".//a")
        span_nodes = [a_node[1] for a_node in a_nodes]
        for span_node in span_nodes:
            assert span_node.tag == "span"
        issue_urls[year_node.get("id")] = \
            [(span_node.text, url_base + a_node.get("href")) for a_node, span_node in zip(a_nodes, span_nodes)]
    return issue_urls


def grab_all_and_save(archive_url, save_to_folder):
    # current_folder == root
    current_folder = pathlib.Path(save_to_folder)
    if not current_folder.exists():
        current_folder.mkdir()
    issue_urls_dict = parse_issue_urls(archive_url)
    for year, issue_urls_list in issue_urls_dict.items():
        # current_folder == root/year
        current_folder = current_folder / year
        if not current_folder.exists():
            current_folder.mkdir()
        for month, issue_url in issue_urls_list:
            article_urls_dict = parse_article_urls(issue_url)
            # current_folder == root/year/month
            current_folder = current_folder / month
            if not current_folder.exists():
                current_folder.mkdir()
            for section, article_urls_list in article_urls_dict.items():
                # current_folder == root/year/month/section
                current_folder = current_folder / section
                if not current_folder.exists():
                    current_folder.mkdir()
                articles = [PLOSArticle(url) for url in article_urls_list]
                for article in articles:
                    status = article.parse_url()
                    if status == PLOSArticle.SUCCESS:
                        file_name = (re.sub(r"[\\/:\*\?\"\<\>\|]", "_", article.title) + ".txt").strip()
                        try:
                            with open(str(current_folder / file_name), "w", encoding="utf8") as f:
                                f.write("\n".join([article.abstract, article.main_text]))
                        except FileNotFoundError as e:
                            _logger.error(str(e))
                        msg = "Saved %s to %s/%s." % (article.title, current_folder, file_name)
                        _logger.info(msg)
                # current_folder == root/year/month
                current_folder = current_folder.parent
            # current_folder == root/year
            current_folder = current_folder.parent
        # current_folder == root
        current_folder = current_folder.parent


if __name__ == "__main__":
    grab_all_and_save("http://www.ploscompbiol.org/article/browse/volume", "PLOS")
    # issue_url = "http://www.ploscompbiol.org/article/browse/issue/info%3Adoi%2F10.1371%2Fissue.pcbi.v04.i04"
    # article_urls_dict = parse_article_urls(issue_url)
    # for section, article_urls_list in article_urls_dict.items():
    #     articles = [Article(url) for url in article_urls_list]
    #     for article in articles:
    #         article.parse_url()
    #         if article.title is not None:
    #             print(article.title)


