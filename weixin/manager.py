#coding:utf-8
import os
from time import sleep
from scrapy.crawler import CrawlerProcess
from scrapy.crawler import Crawler
from spiders.ratingdog import RatingdogSpider
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())

baseDir = os.path.dirname(__file__)
urlFilePath = os.path.join(baseDir,'url.txt')
count = 0


with open(urlFilePath,'r') as f:
    url_string = f.read()
url_list = url_string.split('\n') # 按照换行符分割
print '当前网址:\n',url_list[0]
for url in url_list:
    kwargs = {'start_url':url}
    process.crawl(RatingdogSpider,**kwargs) #传入配置,完成实例化
    process.start()
    count += 1
    print '公众号采集完成%s个'%count
    sleep(5)

