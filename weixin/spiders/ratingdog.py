# -*- coding: utf-8 -*-

import re
import urlparse
import json
import sys
import random
reload(sys)
sys.setdefaultencoding('utf-8')

import scrapy
from bs4 import BeautifulSoup
from scrapy import Request
from scrapy import FormRequest



class RatingdogSpider(scrapy.Spider):
    name = "ratingdog"
    allowed_domains = ["mp.weixin.qq.com"]
    start_urls = (
        'https://mp.weixin.qq.com/mp/getmasssendmsg?__biz=MzIzODUwODYzMw==&uin=NTEwMTYzOTM1&key=79512945a1fcb0e2fb2e751b4b021ac43f1a2d142d7d9f3cb1ddde483fb6912b24a493f2e7e0936695d5763f11398d0c2ef5ff52859cab37&devicetype=iMac+MacBookAir7%2C2+OSX+OSX+10.11.6+build(15G31)&version=12000006&lang=zh_CN&nettype=WIFI&ascene=0&fontScale=100&pass_ticket=XPXQytn7hZ%2B6Du36l3e76AAoNm9cJWh3ch6t2%2BrYw2NlpRte1TJpa4hK0uhsFCqN',
    )
    pageNo = 1
    readAndLike_url = 'http://mp.weixin.qq.com/mp/getappmsgext'

    def __init__(self,start_url=None,*args,**kwargs):

        super(RatingdogSpider,self).__init__(*args,**kwargs) # 调用父类方法,绑定方法

        if not start_url:
            self.start_url = kwargs['start_url']
        else:
            self.start_url = start_url
        #self.start_url = start_url


    def start_requests(self):
        """SPIDER入口"""
        #url = self.start_urls[0]
        url = self.start_url
        print url
        data = urlparse.urlparse(url)
        print data
        url_data = {'scheme':data[0],
                    'netloc':data[1],
                    'path':data[2],
                    'params':data[3],
                    'query':data[4],
                    'fragment':data[5]
                    }
        #处理查询参数
        print url_data
        query_list = url_data['query'].split('&') # 按照&分割
        print query_list

        pattern = re.compile("=(?=\w)") #按照单个=分割
        query_dict = {}
        for item in query_list:
            data = re.split(pattern,item)
            print data[0],data[1],'\n'
            query_dict[data[0]] = data[1] # 更新词典

        query = {'__biz':query_dict['__biz'],
                      'uin':query_dict['uin'],
                      'key':query_dict['key'],
                      'f':'json',
                      'frommsgid':'',
                      'count':10,
                      'pass_ticket':query_dict['pass_ticket'],
                      'wxtoken':'',
                      'x5':0,
                      }

        yield Request(url=self.start_urls[0],
                      meta={'url_para':url_data,'query':query},
                      callback=self.parseList)


    def parseList(self,response):
        """解析公众号列表页"""
        if self.pageNo > 1:

            json_text = json.loads(response.body)

            general_msg_list = json_text['general_msg_list']
            general_msg_list = eval(general_msg_list) #编码
            list = general_msg_list['list']

        else:
            """正则取出json字符串,并做清洗工作"""
            try:
                pattern = re.compile("(?<=msgList = ').*(?=';)")
                # 获取内容字符串
                json_text = pattern.findall(response.body)
                # 清理转义字符
                json_text = json_text[0].replace("&quot;","'").replace("\\","").replace("amp;","").replace("&nbsp;","")
                # 转化为字典
                json_text = eval(json_text)
                list = json_text['list']
            except IndexError:
                print '获取json数据出错,以下是响应内容:\n',response.body

        topic_list = [{'id': item['comm_msg_info']['id'],
                       'title': item['app_msg_ext_info']['title'],
                       'author': item['app_msg_ext_info']['author'],
                       'content_url': item['app_msg_ext_info']['content_url']} \
                      for item in list \
                      if 'app_msg_ext_info' in item]
        for topic in topic_list:
            url = self.cleanUrl(topic['content_url'])
            topic['url'] = url
            # 转到详情页面
            yield Request(url=url, meta={'data': topic}, callback=self.parseDetail)

        # 页面自增
        self.pageNo += 1

        """获取下一页"""
        #当前页面id列表,字符串转化为数字
        id_list = [int(item['id']) for item in topic_list]
        #获取最小ID
        id_min = min(id_list)
        if id_min != 1000000001:
            #修改查询参数
            query = response.meta['query']
            query['frommsgid'] = id_min
            #查询参数转字符串,=联结
            query_string = self.dictToString(**query)
            #设置网址
            url_para = response.meta['url_para']
            url_para['query'] = query_string
            url_next = urlparse.urlunparse((url_para['scheme'],url_para['netloc'],
                                       url_para['path'],url_para['params'],
                                       url_para['query'],url_para['fragment']))
            yield Request(url=url_next,
                          meta={'url_para':url_para,'query':query},
                          callback=self.parseList)
        else:
            print '已到最后一页!'

    def parseDetail(self,response):
        """解析详细页面"""
        soup = BeautifulSoup(response.body,'html.parser')
        imgs = soup.find_all('img',attrs={"data-type":'png'})
        imgs = [img.get('data-src') for img in imgs]
        imgs = '\n'.join(imgs) # 转换成字符串
        p_list = soup.find('div',id="js_content").find_all('p') #搜索所有P节点
        p_text = [p.get_text() for p in p_list] #获取P节点的字符串
        ps = '\n'.join(p_text) #转换为字符串
        data = response.meta['data']
        data['ps'] = ps
        data['imgs'] = imgs
        yield data

    def parseDetail2(self,response):
        """更通用的详细信息"""
        groups = re.search(re.compile('(?<=nickname = ").*(?=")'),response.body)
        nickname = groups.group(0) #昵称
        groups = re.search(re.compile('(?<=ct = ").*(?=")'),response.body)
        ct = groups.group(0) #时间戳
        groups = re.search(re.compile('(?<=publish_time = ").*(?=")'),response.body)
        publish_time = groups.group(0) #推送时间
        groups = re.search(re.compile('(?<=fakeid = ").*(?=")'),response.body)
        fakeid = groups.group(0) # fakeid
        groups = re.search(re.compile('(?<=round_head_img = ").*(?=")'),response.body)
        round_head_img = groups.group(0) # 头像
        groups = re.search(re.compile('(?<=msg_title = ").*(?=")'),response.body)
        msg_title = groups.group(0) # 标题
        groups = re.search(re.compile('(?<=msg_desc = ").*(=")'),response.body)
        msg_desc = groups.group(0) # 文章总结
        groups = re.search(re.compile('(?<=msg_link = ").*(?=")'),response.body)
        msg_link = groups.group(0) # 文章链接
        groups = re.search(re.compile('(?<=req_id = ").*(?=")'),response.body)
        req_id = groups.group(0)
        groups = re.search(re.compile('(?<=appmsgid =)\d{1,}'),response.body)
        msg_id = groups.group(0) # 文章id
        groups = re.search(re.compile('(?<=appmsg_type = ").*(=")'),response.body)
        appmsg_type = groups.group(0) # 文章类型
        groups = re.search(re.compile('(?<=comment_id = ")\d{1}(?=")'),response.body)
        comment_id = groups.group(0) # 评论id
        groups = re.search(re.compile('(?<=is_need_reward = ")\d{1}(?=")'),response.body)
        is_need_reward = groups.group(0)
        groups = re.search(re.compile('(?<=msg_daily_idx = ")\d{1}(?=")'),response.body)
        msg_daily_idx = groups.group(0)
        groups = re.search(re.compile('(?<=window.wxtoken = ")\d{1,}(?=")'),response.body)
        wxtoken = groups.group(0)
        """解析version"""
        groups = re.search(re.compile('(?<="appmsg/index\.js":").*(?=")'),response.body)
        version = groups.group(0) # 取出链接
        version = urlparse.urlparse(version)[2] # 获取相对路径


        soup = BeautifulSoup(response.body, 'html.parser')
        #获取图片
        imgs = soup.find_all('img', attrs={"data-type": 'png'})
        imgs = [img.get('data-src') for img in imgs]
        imgs = '\n'.join(imgs)  # 转换成字符串
        #获取文字
        p_list = soup.find('div', id="js_content").find_all('p')  # 搜索所有P节点
        p_text = [p.get_text() for p in p_list]  # 获取P节点的字符串
        ps = '\n'.join(p_text)  # 转换为字符串

        """有效数据部分"""
        data = response.meta['data']
        data['nickname'] = nickname
        data['ct'] = ct
        data['publish_time'] = publish_time
        data['fakeid'] = fakeid
        data['round_head_img'] = round_head_img
        data['msg_title'] = msg_title
        data['msg_desc'] = msg_desc
        data['msg_link'] = msg_link
        data['msg_id'] = msg_id
        data['req_id'] = req_id
        data['imgs'] = imgs
        data['ps'] = ps

        #从当前网址获取查询参数
        url_data = urlparse.urlparse(response.url)
        query_string = url_data[4] # 获取查询参数
        query_dict = self.stringToDict(query_string) # 查询字符串转换成字典
        """设置查询参数部分"""
        new_query = {}
        new_query['__biz'] = query_dict['__biz']
        new_query['appmsg_type'] = appmsg_type
        new_query['mid'] = query_dict['mid']
        new_query['sn'] = query_dict['sn']
        new_query['idx'] = query_dict['idx']
        new_query['scence'] = query_dict['scence']
        new_query['title'] = msg_title
        new_query['ct'] = publish_time
        new_query['devicetype'] = query_dict['devicetype']
        new_query['version'] = version
        new_query['f'] = 'json'
        new_query['r'] = random.random() #获取随机数
        new_query['is_need_ad'] = '1'
        new_query['comment_id'] = comment_id
        new_query['is_need_reward'] = is_need_reward
        new_query['both_ad'] = '1'
        new_query['reward_uin_count'] = '0'
        new_query['ct1'] = publish_time
        new_query['msg_daily_idx'] = msg_daily_idx
        new_query['uin'] = query_dict['uin']
        new_query['key'] = query_dict['key']
        new_query['pass_ticket'] = query_dict['pass_ticket']
        new_query['wxtoken'] = wxtoken
        new_query['devicetype1'] = query_dict['devicetype']
        new_query['clientversion'] = query_dict['version']
        new_query['x5'] = '1'
        """查询参数，字典转字符串"""
        new_query_string = self.dictToString(**new_query)
        #重复参数处理
        new_query_string = re.sub(re.compile('ct1(?==)'),'ct',new_query_string)
        new_query_string = re.sub(re.compile('devicetype1(?==)'),'devicetype',new_query_string)

        #转到获取点赞
        formdata = {'is_only_read':1,
                    'req_id':req_id,
                    'is_temp_url':0}
        yield FormRequest(url=self.readAndLike_url,
                          formdata=formdata,
                          meta={'data':data},
                          dont_filter=True)


    def parseReadAndLike(self,response):
        """获取阅读数和点赞数"""
        json_text = json.loads(response.body)
        read_num = json_text['appmsgstat']['read_num']
        like_num = json_text['appmsgstat']['like_num']
        data = response.meta['data']
        data['read_num'] = read_num
        data['like_num'] = like_num
        yield data


    def cleanUrl(self,str):
        """清除网址中的反斜杠"""
        pattern = re.compile('\\\\(?=/)')
        str = re.sub(pattern,'',str)
        #清除其他字符
        str = str.replace('amp;','')
        return str

    def dictToString(self,**kwargs):
        """查询参数字典转成=和&连接的字符串"""
        string_list = [str(key)+ '='+ str(kwargs[key]) for key in kwargs]
        return '&'.join(string_list)

    def stringToDict(self,string):
        """网址查询参数转字典"""
        dict = {}
        for item in string.split('&'):
            if item:
                data = item.split('=')
                dict[data[0]] = data[1] # 列表转字典
        return dict





