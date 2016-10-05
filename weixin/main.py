#!/usr/bin/env python
#coding:utf-8
"""
爬虫运行入口:
1、启动代理服务器;
2、监控微信公众号流量,并抓取网址到队列;
3、爬虫监控网址队列,从队列中取出一个网址,完成实例化,并运行
"""

import os
from time import sleep
from Queue import Queue
from threading import Thread

from mitmproxy import controller,proxy
from mitmproxy.proxy.server import ProxyServer
from scrapy.crawler import CrawlerProcess
from spiders.ratingdog import RatingdogSpider

baseDir  = os.path.dirname(__file__)

class WeixinProxy(controller.Master):
    """代理服务器,过滤微信公众号流量"""

    def __init__(self,server):
        """传入代理服务器及网址队列"""
        controller.Master.__init__(self,server) #非绑定方法调用父类
        self.urlFilePath = os.path.join(baseDir,'url.txt')

    def run(self):
        """覆盖run方法"""
        try:
            return controller.Master.run(self) #调用父类的run方法
        except KeyboardInterrupt:
            self.shutdown() #crtl+C则停止服务器

    def handle_request(self,flow):
        """处理请求"""

        if flow.request.host == 'mp.weixin.qq.com' and 'devicetype' in flow.request.url:
            """通过请求主机、查询参数过滤,只获取历史消息第一页网址"""
            with open(self.urlFilePath,'a') as f:
                f.write(flow.request.url+'\n') #注意换行符

        flow.reply() # 请求转发

    def handle_response(self,flow):
        """处理服务器响应"""
        flow.reply() #转发响应

if __name__ == '__main__':
    config = proxy.ProxyConfig(port=9527)
    server = ProxyServer(config)
    m = WeixinProxy(server)
    m.run()


