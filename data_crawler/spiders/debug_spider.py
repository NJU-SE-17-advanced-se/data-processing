import json

import scrapy

class DebugSpider(scrapy.Spider):
    """
    用于debug，直接读取之前爬取的内容，然后作为item传给pipeline处理
    """
    name = "debug"

    def start_requests(self):
        yield scrapy.Request('http://quotes.toscrape.com/page/1/')
    
    def parse(self, response):
        with open('test_files/crawled_items_debug.json') as f:
            for line in f:
                item = json.loads(line)
                yield item
