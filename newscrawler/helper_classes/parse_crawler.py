"""
This is a helper class for the crawler's parse methods
"""
import time
import re

import logging

import scrapy
from newscrawler.crawler.items import NewscrawlerItem


class ParseCrawler(object):
    """
    Helper class for the crawler's parse methods.
    """
    helper = None
    log = None

    def __init__(self, helper):
        self.helper = helper
        self.log = logging.getLogger(__name__)

    def pass_to_pipeline_if_article(
            self,
            response,
            source_domain,
            original_url,
            rss_title=None
    ):
        """
        Responsible for passing a NewscrawlerItem to the pipeline if the
        response contains an article.

        :param obj response: the scrapy response to work on
        :param str source_domain: the response's domain as set for the crawler
        :param str original_url: the url set in the json file
        :param str rss_title: the title extracted by an rssCrawler
        :return NewscrawlerItem: NewscrawlerItem to pass to the pipeline
        """
        if self.helper.heuristics.is_article(response, original_url):
            timestamp = time.strftime('%y-%m-%d %H:%M:%S',
                                      time.gmtime(time.time()))

            article = NewscrawlerItem()
            article['local_path'] = self.helper.savepath_parser \
                .get_savepath(response.url)
            article['abs_local_path'] = self.helper.savepath_parser \
                .get_abs_path(article['local_path'])
            article['modified_date'] = timestamp
            article['download_date'] = timestamp
            article['source_domain'] = source_domain.encode("utf-8")
            article['url'] = response.url
            article['html_title'] = response.selector.xpath('//title/text()') \
                .extract_first().encode("utf-8")
            if rss_title is None:
                article['rss_title'] = 'NULL'
            else:
                article['rss_title'] = rss_title.encode("utf-8")
            article['ancestor'] = 'NULL'
            article['descendant'] = 'NULL'
            article['version'] = '1'
            article['spider_response'] = response
            return article

    @staticmethod
    def recursive_requests(response, spider, ignore_regex='',
                           ignore_file_extensions='pdf'):
        """
        Manages recursive requests.
        Determines urls to recursivly crawl if they do not match certain file
        extensions and do not match a certain regex set in the config file.

        :param obj response: the response to extract any urls from
        :param obj spider: the crawler the callback should be called on
        :param str ignore_regex: a regex that should that any extracted url
                                 shouldn't match
        :param str ignore_file_extensions: a regex of file extensions that the
                                           end of any url may not match
        :return list: Scrapy Requests
        """
        # Recursivly crawl all URLs on the current page
        # that do not point to irrelevant file types
        # or contain any of the given ignore_regex regexes
        return [scrapy.Request(response.urljoin(href), callback=spider.parse)
                for href in response.css("a::attr('href')").extract()
                if re.match(r'.*\.' + ignore_file_extensions + r'$',
                            response.urljoin(href), re.IGNORECASE) is None and
                len(re.match(ignore_regex,
                             response.urljoin(href)).group(0)) == 0]

    def content_type(self, response):
        """
        Ensures the response is of type

        :param obj response: The scrapy response
        :return bool: Determines wether the response is of the correct type
        """
        if not re.match('text/html', response.headers.get('Content-Type')):
            self.log.warn("Dropped: %s's content is not of type "
                          "text/html but %s", response.url,
                          response.headers.get('Content-Type'))
            return False
        else:
            return True
