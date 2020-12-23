# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DataCrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class PaperItem(scrapy.Item):
    """
    IEEE和ACM统一的PaperItem
    """
    title = scrapy.Field()
    authors = scrapy.Field() # author list; author: dictionary, keys: id, name, order
    abstract = scrapy.Field()
    publication_id = scrapy.Field()
    publicationTitle = scrapy.Field()
    doi = scrapy.Field()
    publicationYear = scrapy.Field()
    references = scrapy.Field() # 引用的文章的doi（可以获得doi的）
    keywords = scrapy.Field() # keyword list
    ref_ieee_document = scrapy.Field() # IEEE document id, stored to be crawled later
    ref_title = scrapy.Field() # reference title, stored to be crawled later. Store this beacause citation that IEEE gives is weired.
    ref_citation = scrapy.Field()
    citation = scrapy.Field() # 被引量
    id = scrapy.Field() # id
    url = scrapy.Field()

class IEEEPaperItem(scrapy.Item):
    title = scrapy.Field()
    authors = scrapy.Field()
    abstract = scrapy.Field()
    publication_number = scrapy.Field() # publication 标识某届会议
    issue_number = scrapy.Field() # IEEE 内部 issue id。issue 表示某届会议的某个出版物
    articleNumber = scrapy.Field() # IEEE 内部文章 id
    publicationTitle = scrapy.Field()
    doi = scrapy.Field()
    publicationYear = scrapy.Field()
    metrics = scrapy.Field()
    contentType = scrapy.Field()
    references = scrapy.Field()
    keywords = scrapy.Field()
    url = scrapy.Field()

# ACM的paper.TODO:将ACM和IEEE paper的item统一.暂时保存各自的尽可能多的信息.
class ACMPaperItem(scrapy.Item):
    title = scrapy.Field() # 标题
    authors = scrapy.Field() # 作者
    year = scrapy.Field() # 年份
    # conference = scrapy.Field() # 会议/期刊
    publication_id = scrapy.Field() # ACM 内部 id，对于会议来说是会议 publication doi，对于期刊（每一个 issue 都没有 doi）来说是一个内部id，如'/toc/tosem/2015/25/1',表示 tosem 2015年 volume 25 issue 1,可以唯一确定一个 issue。
    publication_title = scrapy.Field()
    doi = scrapy.Field() # 同时也是 ACM 的 “内部” id。也就是说，有的这个看似是 doi，其实并未在 doi.org 注册。
    abstract = scrapy.Field()
    citation = scrapy.Field() # paper citation
    references = scrapy.Field() # 该文章引用的文章
    index_term_tree = scrapy.Field() # ACM index term tree
    url = scrapy.Field()
