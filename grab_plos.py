from urllib.parse import urlsplit
from utils import get_doc_tree_from_url
from plos_article import PLOSArticle
import logging
import re
import pathlib
import os
from multiprocessing.pool import ThreadPool
import queue
from threading import Thread
import argparse
import time

_logger = logging.getLogger(__name__)
_article_queue = queue.Queue()


def parse_article_urls(issue_url, context=None):
    add_context = lambda article: article if context is None else (article, context)
    doc_tree = get_doc_tree_from_url(issue_url)
    if doc_tree is not None:
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
        return add_context(article_urls)
    else:
        _logger.error("Cannot parse the issue page. URL: %s" % issue_url)
        return add_context(None)


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
            [(url_base + a_node.get("href"), span_node.text) for a_node, span_node in zip(a_nodes, span_nodes)]
    return issue_urls


def crawl_article_urls(archive_url, save_to_folder):
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
        with ThreadPool(processes=len(issue_urls_list)) as pool:
            article_urls_dict_list = pool.starmap(parse_article_urls, issue_urls_list)
        for article_urls_dict, month in article_urls_dict_list:
            if article_urls_dict is not None:
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
                        _article_queue.put((article, current_folder))
                    # current_folder == root/year/month
                    current_folder = current_folder.parent
                # current_folder == root/year
                current_folder = current_folder.parent
            else:
                _logger.error("Issue: %s %s" % (year, month))
        # current_folder == root
        current_folder = current_folder.parent


def download_articles_and_save():
    while True:
        article, save_to = _article_queue.get()
        status = article.parse_url()
        if status == PLOSArticle.SUCCESS:
            file_name = (re.sub(r"[\\/:\*\?\"\<\>\|\n]", "_", article.title) + ".txt").strip()
            file_name = re.sub(r"[\t\s]+", " ", file_name)
            try:
                with open(str(save_to / file_name), "w", encoding="utf8") as f:
                    f.write(str(article))
            except FileNotFoundError as e:
                _logger.error("%s when fetching %s." % (str(e), article.url))
            msg = "Saved \"%s\" to \"%s%s%s\"." % (article.title, save_to, os.path.sep, file_name)
            _logger.info(msg)
        _article_queue.task_done()


if __name__ == "__main__":

    log_file_default = "%s.log" % time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())

    parser = argparse.ArgumentParser(description="Save the articles of a PLOS journal in .txt files",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--journal-url", metavar="URL",
                        help="the archive page the journal. "
                             "Example: http://www.ploscompbiol.org/article/browse/volume",
                        required=True, default=argparse.SUPPRESS)
    parser.add_argument("--save-to", metavar="FOLDER", help="the destination folder",
                        required=True, default=argparse.SUPPRESS)
    parser.add_argument("--threads", metavar="N", type=int, default=10, help="the number of threads for downloading")
    parser.add_argument("--log", default=log_file_default, help="the log file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        handlers=[logging.FileHandler(args.log, mode='w', encoding='utf8')])

    t_spider = Thread(target=crawl_article_urls,
                      args=(args.journal_url, args.save_to))

    t_spider.start()

    for i in range(args.threads):
        t_worker = Thread(target=download_articles_and_save, daemon=True)
        t_worker.start()
    t_spider.join()
    _article_queue.join()