# encoding:utf-8
import re
import os
import json
import time
import aiohttp
import asyncio
from lxml import etree

class Crawler:

    def __init__(self, urls, max_workers=8):
        self.urls = urls
        self.folder = ''
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
                res = await self.fetch(session,url)
                await self.DownloadImg(session, res)

    async def fetch(self,session, url):
        print("Fetching URL: " + url)
        newUrl= url.replace('com','cn')
        self.headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 8.1.0; zh-cn; OE106 Build/OPM1.171019.026) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/9.2 Mobile Safari/537.36',
        'Referer': url,
        }
        data = {}
        html = await self.getHtmlText(session, newUrl)
        if html is not None:
            a = re.findall('imgJson = ([\s\S]*?);', html.decode())
        
            jsonp = json.loads(a[0])
            picInfo = jsonp['picInfo']
            data['folder']=jsonp['gallery_title']
            data['fetchUrl']=url
            res = []
            for i in picInfo:
                tmp = {}
                tmp['intro'] = i['add_intro']
                tmp['url'] = i['url']
                res.append(tmp)
            data['res'] = res
        return data

    # download Pic
    async def DownloadImg(self, session, data):
        # print(type(data))
        if data:
            for i in data['res']:
                intro = i['intro']
                picUrl = i['url']
                tmp = picUrl.split('/')[-2:]
                extend = picUrl.split('.')[-1:]
                folder = './pic/' + data['folder']

                isExists = os.path.exists(folder)
                print(folder)
                if not isExists:
                    os.makedirs(folder)
                file = folder +'/'+ intro + '.'+ extend[0] # tmp[1]
                isFileExists = os.path.exists(file)
                if not isFileExists:
                    async with session.get(picUrl, headers=self.headers, timeout=15, verify_ssl=False) as response:
                        print('download picUrl: ' + picUrl)
                        try:
                            img_response = await response.read()
                            with open(file, 'wb') as f:
                                f.write(img_response)
                        except Exception as e:
                            print(e)
                            return
            # done
            with open('success.log','a')as f:
                f.write(data['fetchUrl']+'\n')
    # get html text
    async def getHtmlText(self, session, url):
        try:
            async with session.get(url, headers=self.headers,timeout=15) as response:
                # return await response.text(encoding='utf-8')
                return await response.read()
        
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(e)

def test():
    import requests

    ID = '5037'    # 今日囧图
    ID = '20721'   # 冷知识
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36',
        'Referer': 'http://tu.duowan.cn/tag/%s.html'%ID,
    }
    
    file = '%s.json'%ID

    isExists = os.path.exists(file)
    if not isExists:
        '''
        API interface
        '''
        urlAPI = 'http://tu.duowan.com/index.php?r=api/ajaxgallerys&page=1&pageSize=500&tag=%s&t=0.9035365604856225&callback=jsonp2'%ID
        r = requests.get(urlAPI,headers=headers)
        if r.status_code == 200:  # ok
            html = r.content.decode('utf-8')
            print('Create jsonp file.')
            with open(file,'w',encoding='utf-8')as f:
                res=re.findall('jsonp2\((.*?)\)',html)
                f.write(res[0])                     # save to file
    with open(file,'r',encoding='utf-8')as f:
        data = f.readlines()
        jsonp = json.loads(data[0])          # read file to json
    urlList = []
    gallerys = jsonp['gallerys']
    for i in gallerys:
        title = i['title']
        res = re.findall('369',title)         # before 369 is None !
        urlList.append(i['url'])
        if res:
            break
    print('All urlPage is: ', len(urlList))
    c = Crawler(urlList)
    asyncio.run(c.crawl())
    print('OK')


if __name__=='__main__':
    start = time.time()
    test()
    end = time.time()
    print("Finished in Time Consuming: {}".format(end-start))
