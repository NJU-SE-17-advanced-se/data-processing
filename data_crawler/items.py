# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DataCrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class IEEEPaperItem(scrapy.Item):
    title = scrapy.Field()
    authors = scrapy.Field()
    abstract = scrapy.Field()
    publicationTitle = scrapy.Field()
    doi = scrapy.Field()
    publicationYear = scrapy.Field()
    metrics = scrapy.Field()
    contentType = scrapy.Field()

# ACM的paper.TODO:将ACM和IEEE paper的item统一.暂时保存各自的尽可能多的信息.
class ACMPaperItem(scrapy.Item):
    title = scrapy.Field() # 标题
    authors = scrapy.Field() # 作者
    month_year = scrapy.Field() # 月份和年份
    conference = scrapy.Field() # 会议/期刊
    doi = scrapy.Field()
    abstract = scrapy.Field()
    citations = scrapy.Field() # 引用该文章的文章
    references = scrapy.Field() # 该文章引用的文章
