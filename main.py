# encoding:utf-8
import re
import os
import json
import time
import aiohttp
import asyncio
from lxml import etree

class Crawler:

    def __init__(self, urls, max_workers=1):
        self.urls = urls
        self.fetching = asyncio.Queue()
        self.max_workers = max_workers
        self.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36'
        }
    async def crawl(self):
        # DON'T await here; start consuming things out of the queue, and
        # meanwhile execution of this function continues. We'll start two
        # coroutines for fetching and two coroutines for processing.
        all_the_coros = asyncio.gather(
            *[self._worker(i) for i in range(self.max_workers)])

        # place all URLs on the queue
        for url in self.urls:
            await self.fetching.put(url)

        # now put a bunch of `None`'s in the queue as signals to the workers
        # that there are no more items in the queue.
        for _ in range(self.max_workers):
            await self.fetching.put(None)

        # now make sure everything is done
        await all_the_coros

    async def _worker(self, i):
        while True:
            url = await self.fetching.get()
            if url is None:
                # this coroutine is done; simply return to exit
                return

            # print(f'Fetch worker {i} is fetching a URL: {url}')
            async with aiohttp.ClientSession() as session:
                picPageUrlList = await self.fetch(session,url)
                picUrlList = await self.process(session, picPageUrlList)
                await self.DownloadImg(session, picUrlList)

    async def fetch(self,session, url):
        print("Fetching URL: " + url)
        url= url.replace('com','cn')
        self.headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 8.1.0; zh-cn; OE106 Build/OPM1.171019.026) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/9.2 Mobile Safari/537.36',
        'Referer': url,
        }
        html = await self.getHtmlText(session, url)
        a = re.findall('imgJson = ([\s\S]*?);', html.decode())
        # print(a)
        # print(type(a))
        # print(a[0])
        jsonp = json.loads(a[0])
        folder = jsonp['gallery_title']
        picInfo = jsonp['picInfo']
        print(len(picInfo))
        print(folder)
        res = []
        for i in picInfo:
            tmp = {}
            tmp['add_intro'] = i['add_intro']
            tmp['url'] = i['url']
            res.append(tmp)
            '''
            [{'add_intro': '总比打呼噜好', 'url': 'http://s1.dwstatic.com/group1/M00/6A/E5/2a17d8dfe3b8c4f1118ae54332981992.jpg'}, {'add_intro': '最耐热的昆虫', 'url': 'http://s1.dwstatic.com/group1/M00/52/ED/3bab732d8ec878177a9bab6eaa1bac3b.jpg'}]
            '''
        # print(res)
        exit()
        # pattern = re.compile('上一页</li><li>([\s\S]*?)</li>')
        # allPage = re.findall(pattern, html)
        # allPage = (allPage[0]).split('/')[1]
        # picUrlList = [re.sub(r'(\d+)(?=.htm)', str(e), url) for e in range(1,int(allPage)+1)]
        # return picUrlList

    # process pic url
    async def process(self, session, picUrlList):
        # print("process URL: " + url);
        tmp = []
        for picUrl in picUrlList:
            # print("process picUrl: " + picUrl);
            html = await self.getHtmlText(session, picUrl)
            pattern = re.compile("IMG SRC='([\s\S]*?)'")
            imgUrl = re.findall(pattern, html)
            imgUrl = imgUrl[0].replace('''"''', "").replace("+", "")

            parameter_global_js = ({
            # "server0": "http://n.1whour.com/",
            # "server": "http://n.1whour.com/",
            # "m200911d": "http://n.1whour.com/",
            # "m201001d": "http://n.1whour.com/",
            'm2007':'http://m8.1whour.com/',
            })
            for _i in parameter_global_js:
                urlPic = imgUrl.replace(str(_i), str(parameter_global_js[_i]))
                tmp.append(urlPic)
        return tmp

    # download Pic
    async def DownloadImg(self, session, picUrlList):
        for picUrl in picUrlList:
            async with session.get(picUrl, headers=self.headers, timeout=15, verify_ssl=False) as response:
                print('download picUrl: ' + picUrl)
                try:
                    img_response = await response.read()
                    tmp = picUrl.split('/')[-2:]
                    folder = './' + tmp[0]
                    file = folder +'/'+ tmp[1]

                    isExists = os.path.exists(folder)
                    if not isExists:
                        os.makedirs(folder)
                    with open(file, 'wb') as f:
                        f.write(img_response)
                except Exception as e:
                    print(e)
                    pass

    # get html text
    async def getHtmlText(self, session, url):
        async with session.get(url, headers=self.headers,timeout=15,verify_ssl=False) as response:
            # return await response.text(encoding='utf-8')
            return await response.read()


def test():
    # main loop
    import requests

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
        'Referer': 'http://tu.duowan.cn/tag/20721.html',
    }
    # url = 'http://tu.duowan.com/tag/20721.html'   # 冷知识
    '''
    API interface
    '''
    urlAPI = 'http://tu.duowan.com/index.php?r=api/ajaxgallerys&page=1&pageSize=500&tag=20721&t=0.9035365604856225&callback=jsonp2'
    r = requests.get(urlAPI,headers=headers)
    if r.status_code == 200:  # ok
        html = r.content.decode('utf-8')
        file = 'jsonp.json'
        isExists = os.path.exists(file)
        if not isExists:
            print('Create jsonp file.')
            with open(file,'w',encoding='utf-8')as f:
                res=re.findall('jsonp2\((.*?)\)',html)
                f.write(res[0])                     # save to file
        print('Use local json')
        with open(file,'r',encoding='utf-8')as f:
            data = f.readlines()
            jsonp = json.loads(data[0])          # read file to json
        urlList = []
        gallerys = jsonp['gallerys']
        for i in gallerys:
            urlList.append(i['url'])
        # print(urlList)
        print('All urlPage is: ', len(urlList))
        c = Crawler(urlList)
        asyncio.run(c.crawl())
        print('OK')


if __name__=='__main__':
    start = time.time()
    test()
    end = time.time()
    print("Finished in Time Consuming: {}".format(end-start))