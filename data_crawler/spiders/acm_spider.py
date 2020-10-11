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

class ACMSpider(scrapy.Spider):
    name = "ACM_Paper"
    allowed_domains = ["dl.acm.org"]
    start_urls = get_project_settings().get('ACM_URL')

    def __init__(self):
        super(ACMSpider, self).__init__()
        self.startPage = 0
        self.pageSize = 20 # ACM advanced search默认每页显示20篇文章。也许以后会变动
        self.startTime = get_project_settings().get('START_TIME')

    def parse(self, response):
        print('爬取第', self.startPage, '页')

        # 搜索结果中的文章总数
        results_num = response.xpath('//span[@class="hitsLength"]/text()').get()

        # 对应url没有发现文章时报错
        if(results_num == 0):
            logging.error("no paper found for this url")
            raise scrapy.exceptons.CloseSpider("no_paper")
        logging.info("{} ACM paper found".format(results_num))

        # 所有paper的selector
        papers = response.xpath('//div[@class="issue-item__content-right"]')
        # 所需要的field的对应的xpath
        xpaths = {
            'abstract': './div[contains(@class, "issue-item__abstract")]/p/text()',
            'authors': './/ul[@aria-label="authors"]/li/a/span/text()',
            'citation': './/span[@class="citation"]/span/text()',
            'doi': './/a[@class="issue-item__doi dot-separator"]/text()',
            'month_year': './/span[@class="dot-separator"]',
            'title': './/span[@class="hlFld-Title"]/a/text()',
            'typex': './/span[@class="epub-section__title"]/text()'
            
        }

        # 依次爬取每篇paper的页面
        for paper in papers:
            paper_url = paper.xpath('.//span[@class="hlFld-Title"]/a/@href').get()
            paper_url = 'https://dl.acm.org' + paper_url
            yield scrapy.Request(url=paper_url, callback=self.parse_paper)

        logging.warning('$ ACM_Spider已爬取：' + str((self.startPage + 1) * self.pageSize))
        
        # 搜索结果多页时，依次爬完所有页
        if (self.startPage + 1) * self.pageSize < int(results_num) and self.startPage < 1:
            self.startPage += 1
            next_url = self.start_urls[0] + '&startPage=' + str(self.startPage) + '&pageSize=' + str(self.pageSize)
            yield scrapy.Request(
                next_url,
                callback=self.parse,
            )
    def parse_paper(self, response):
        # 结果的对象
        result = ACMPaperItem()
        paper = response.xpath('//article')

        result['title'] = paper.xpath('.//div[@class="citation"]//h1[@class="citation__title"]/text()').get()

        # 所有的作者名
        author_names = paper.xpath('.//div[@class="citation"]//div[@id="sb-1"]/ul/li[@class="loa__item"]//span[@class="loa__author-name"]/span/text()').getall()

        # 所有的作者的主页地址（不包含域"dl.acm.org"），TODO:可以用于后续爬取作者主页
        author_profiles = paper.xpath('.//div[@class="citation"]//div[@id="sb-1"]/ul/li[@class="loa__item"]//div[@class="author-info"]//div[@class="author-info__body"]/a/@href').getall()
        if len(author_names) != len(author_profiles):
            # 作者名和作者主页数量不统一时warning TODO: 改为先找个每个作者的xpath
            logging.warning('different length between author names and author profiles in %s' % result['title'])
        else:
            result['authors'] = [{'author_name': author_names[i], 'author_profile': 'dl.acm.org' + author_profiles[i]} for i in range(0, len(author_names))]

        # 获得发表的相关信息
        publication = paper.xpath('.//div[@class="issue-item__detail"]')

        # 会议名和会议doi
        try:
            conference = {
                'conference_title': publication.xpath('./a/@title').get(), 
                'conference_doi': remove_prefix(publication.xpath('./a/@href').get(), '/doi/proceedings/')
            }
        except NoPrefixException as e:
            # conference的doi如果不包含这个前缀的话，全部保存并发出warning。
            logging.warning('conference doi without prefix \'/doi/proceedings/\', got %s, saved as doi instead' % e.args[0])
            conference = {
                'conference_title': publication.xpath('./a/@title').get(), 
                'conference_doi': publication.xpath('./a/@href').get()
            }
        result['conference'] = conference

        # paper发表年月
        result['month_year'] = publication.xpath('.//span[@class="epub-section__date"]/text()').get()

        # paper doi
        try:
            result['doi'] = remove_prefix(publication.xpath('.//a[@class="issue-item__doi"]/@href').get(), 'https://doi.org/')
        except NoPrefixException as e:
            logging.warning('paper doi without prefix \'/doi/proceedings/\', got %s, saved as doi instead' % e.args[0])
            result['doi'] = publication.xpath('.//a[@class="issue-item__doi"]/@href').get()

        # paper abstract
        result['abstract'] = paper.xpath('.//div[@class="abstractSection abstractInFull"]/p/text()').get()
        
        # paper references
        references_selectors = paper.xpath('.//div[contains(@class, "article__references")]/ol[contains(@class, "references__list")]/li/span[@class="references__note"]')
        result['references'] = [
            {
                'reference_citation': reference.xpath('./text()').get(),
                'reference_links': [{
                        'link_type': link.xpath('./span[@class="visibility-hidden"]/text()').get(),
                        'link_url': link.xpath('./@href').get()
                    }
                    for link in reference.xpath('./span[@class="references__suffix"]/a')
                ]
            } for reference in references_selectors
        ]
        yield result
    
    def remove_html(self, string):
        pattern = re.compile(r'<[^>]+>')
        return (re.sub(pattern, '', string).replace('\n', '').replace('  ', '')).strip()

    def remove4year(self, string):
        return string.split(', ')[0]

    def merge_authors(self, au_list):
        au_str = ''
        for i in au_list:
            au_str += i + ','
        return au_str.strip(',')