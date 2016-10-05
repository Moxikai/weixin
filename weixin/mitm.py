#!/usr/bin/env python
#coding:utf-8
"""
This example builds on mitmproxy's base proxying infrastructure to
implement functionality similar to the "sticky cookies" option.

Heads Up: In the majority of cases, you want to use inline scripts.
"""
import os
from mitmproxy import controller, proxy
from mitmproxy.proxy.server import ProxyServer


class StickyMaster(controller.Master):
    def __init__(self, server):
        controller.Master.__init__(self, server)
        self.stickyhosts = {}
        #print 'i am running'

    def run(self):
        try:
            return controller.Master.run(self)
        except KeyboardInterrupt:
            self.shutdown()

    def handle_request(self, flow):
        print '这是请求网址:',flow.request.url,'\n','这是请求主机:',flow.request.host,'\n','这是请求的端口:',flow.request.port
        #print flow.request.host,flow.request.port
        flow.reply()

    def handle_response(self, flow):
        #print '这是响应主机:',flow.response.host,'\n','这是响应端口:',flow.response.port
        #print flow.response.url
        flow.reply()


config = proxy.ProxyConfig(port=9527)
server = ProxyServer(config)
m = StickyMaster(server)
m.run()