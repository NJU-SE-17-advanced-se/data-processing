import json
import re
import logging
import random

import scrapy

from data_crawler.spiders.utils import remove_prefix
from data_crawler.spiders.utils import NoPrefixException
from data_crawler.spiders.utils import save_byte_file
from data_crawler.spiders.utils import save_str_file

from scrapy.utils.project import get_project_settings

from data_crawler.items import ACMPaperItem

from data_crawler.spiders.acm_paper_parser import parse_acm_paper

from urllib.parse import urlencode

class ACMProceedingSpider(scrapy.Spider):
    name = "ACM_Proceedings_Journals"
    acm_base_url = 'https://dl.acm.org'
    allowed_domains = ['dl.acm.org']
    proceeding_urls = get_project_settings().get('ACM_PROCEEDING_URLS')
    journal_urls = get_project_settings().get('ACM_JOURNAL_URLS')
    journal_year = get_project_settings().get('ACM_JOURNAL_YEAR')
    
    def start_requests(self):
        for url in self.proceeding_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_proceedings,
                dont_filter=True
            )
        
        for url in self.journal_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_journals,
                dont_filter=True
            )
    
    def parse_journals(self, response):
        """
        由于 ACM journal 页面使用懒加载，需要
        1. 获取必要的用于模拟懒加载请求的，不知道什么意思的 request payload: pbContext.
        2. 目标组件的 widgetId 是一个固定的值(所有期刊对应展示历史期刊的组件 widget id 都是 'ece68bd8-5742-40fc-b952-a19a9548dc74')
        3. 获取 journal doi
        3. 按照设定的年份要求依次爬取。
        """
        pbContext = response.xpath('./head/meta/@content').get()
        widgetId = 'ece68bd8-5742-40fc-b952-a19a9548dc74'
        doi = response.xpath('.//div[@data-widget-id="ece68bd8-5742-40fc-b952-a19a9548dc74"]/@data-journal-doi').get()
        
        for year in range(self.journal_year['from'], self.journal_year['to'] + 1):
            query_string_param = {
                'widgetId': widgetId,
                'pbContext': pbContext,
                'doi': doi,
                'decadeRange': str(year - year % 10) + '-' + str(year - year % 10 + 9), # e.g. 2010-2019
                'yearParam': year
            }
            yield scrapy.Request(
                url='https://dl.acm.org/pb/widgets/loi/loiAjax?' + urlencode(query_string_param),
                callback=self.parse_journals_year
            )
        yield None
    
    def parse_journals_year(self, response):
        issue_urls = response.xpath('.//a[@class="loi__issue"]/@href').getall()
        for issue_url in issue_urls:
            yield scrapy.Request(
                url=self.acm_base_url + issue_url,
                callback=self.parse_journals_issue,
            )

    def parse_journals_issue(self, response):
        self.logger.info('start crawling journal issue: {}'.format(response.request.url))
        issues = response.xpath('.//div[@class="issue-item-container"]')
        for issue in issues:
            if(issue.xpath('.//div[@class="issue-item__citation"]/div[@class="issue-heading"]/text()').get() == 'research-article'):
                issue_url = issue.xpath('.//h5[@class="issue-item__title"]/a/@href').get()
                yield scrapy.Request(
                    url=self.acm_base_url + issue_url,
                    callback=self.parse_paper,
                    meta={
                        'publication_id': response.request.url[18:] # 例如 'https://dl.acm.org/toc/tosem/2015/25/1'，取'/toc/tosem/2015/25/1'
                    }
                )



    def parse_proceedings(self, response):
        """
        由于 ACM proceeding 页面使用懒加载，需要
        1. 获取必要的用于模拟懒加载请求的，不知道什么意思的request payload: pbContext.
        2. 获得目标组件（SESSIONS列表）的widgetId
        3. 获得ssession
        4. 对每个session，获取head id
        5. 依次请求每个session
        6. 对每个session的所有文章依次爬取文章界面。
        """
        # request payload for lazy loading
        pbContext = response.xpath('./head/meta/@content').get()
        doi =  response.request.url[35:] # proceeding url is https://dl.acm.org/doi/proceedings/ + doi
        widget = response.xpath('//div[@class="table-of-content table-of-content--lazy"]/..')
        widgetId = widget.xpath('./@data-widgetid').get()

        session_ids = widget.xpath('//div/a[contains(@class, "section__title")]/@id').getall()

        for session_id in session_ids:
            query_string_param = {
                'tocHeading': session_id,
                'widgetId': widgetId,
                'doi': doi,
                'pbContext': pbContext
            }
            yield scrapy.Request(
                url='https://dl.acm.org/pb/widgets/lazyLoadTOC?' + urlencode(query_string_param),
                callback=self.parse_session,
                meta={
                    # information just for logging
                    'proceeding_doi': doi,
                    'session_heading': session_id,
                    'session_num': len(session_ids)
                }
            )

    def parse_session(self, response):
        self.logger.info('crawled ACM proceeding {} session {} paper list, totoal {} sessions'.format(
            response.meta['proceeding_doi'], 
            response.meta['session_heading'][7:], 
            response.meta['session_num']))
        papers_dois = response.xpath('//div[@class="issue-item__content-right"]/h5/a/@href').getall()
        for paper_doi in papers_dois:
            yield scrapy.Request(
                url='https://dl.acm.org' + paper_doi,
                callback=self.parse_paper,
                meta={
                    'publication_id': response.meta['proceeding_doi'],
                }
            )
    
    def parse_paper(self, response):
        def parse_index_tree(selector):
            """传入一个树的select，返回树的json
            """
            # 前置条件：根节点存在（selector.get() != None）。对根结点没关系
            result = {}
            result['title'] = selector.xpath('./div/p/a/text()').get() or selector.xpath('./h6/text()').get()
            result['url'] = 'https://dl.acm.org/' + selector.xpath('./div/p/a/@href').get()
            child = []
            for child_html in selector.xpath('./ol[contains(@class, hasNodes)]/li').getall():
                child.append(parse_index_tree(scrapy.Selector(text=child_html).xpath('./body/li')))
            result['child'] = child
            return result

        # 结果的对象
        result = ACMPaperItem()
        paper = response.xpath('//article')

        result['title'] = paper.xpath('.//div[@class="citation"]//h1[@class="citation__title"]/text()').get()

        # authors
        result['authors'] = []
        authors = paper.xpath('.//div[@class="citation"]//div[@id="sb-1"]/ul/li[@class="loa__item"]')
        for author in authors:
            result_author = {
                'author_name': author.xpath('.//span[@class="loa__author-name"]/span/text()').get(),
                'author_profile': author.xpath('//div[@class="author-info"]//div[@class="author-info__body"]/a/@href').get(),
                'affiliation': author.xpath('.//div[@class="author-info__body"]/p/text()').getall()
            }
            result['authors'].append(result_author)

        # 获得发表的相关信息
        publication = paper.xpath('.//div[@class="issue-item__detail"]')

        # publication_id
        result['publication_id'] = response.meta['publication_id']

        # publication_title
        result['publication_title'] = publication.xpath('./a/@title').get()

        # paper发表年月
        result['month_year'] = publication.xpath('.//span[@class="epub-section__date"]/text()').get()

        # paper doi
        try:
            result['doi'] = remove_prefix(response.request.url, 'https://doi.org/doi/')
        except NoPrefixException as e:
            try:
                result['doi'] = remove_prefix(response.request.url, 'https://dl.acm.org/doi/')
            except NoPrefixException as e:
                self.logger.warning('paper url without prefix \'https://doi.org/doi/\', got %s instead, saved as doi instead' % e.args[0])
                result['doi'] = response.request.url

        # paper abstract
        result['abstract'] = paper.xpath('.//div[@class="abstractSection abstractInFull"]/p/text()').get()
        
        # paper references
        references_selectors = paper.xpath('.//div[contains(@class, "article__references")]/ol[contains(@class, "references__list")]/li')
        result['references'] = [
            {
                'order': int(reference.xpath('./@id').get().split('-')[1]), #id的样子大概是 ref-0001, 数字代表 order
                'reference_citation': reference.xpath('./span/text()').get(),
                'reference_links': [{
                        'link_type': link.xpath('./span[@class="visibility-hidden"]/text()').get(),
                        'link_url': link.xpath('./@href').get()
                    }
                    for link in reference.xpath('./span/span[@class="references__suffix"]/a')
                ]
            } for reference in references_selectors
        ]

        # index term
        root_selector = response.xpath('.//ol[@class="rlist organizational-chart"]/li')
        result['index_term_tree'] = {
            'title': root_selector.xpath('./h6/text()').get(),
            'url': None,
            'child': [parse_index_tree(scrapy.Selector(text=tree_html).xpath('./body/li')) for tree_html in root_selector.xpath('./ol/li').getall()]
        }

        # metric citation number
        result['citation'] = response.xpath('//span[@class="citation"]/span/text()').get()

        self.logger.info("paper crawled, doi: {}".format(result['doi']))
        yield result
