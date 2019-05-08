#encoding:utf-8
import requests

ID = '137442'
url = 'http://tu.duowan.cn/gallery/%s.html' % ID

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; U; Android 8.1.0; zh-cn; OE106 Build/OPM1.171019.026) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/9.2 Mobile Safari/537.36',
    'Referer': 'http://tu.duowan.com/gallery/%s.html' % ID,
}
import re
r = requests.get(url,headers=headers)
if r.status_code == 200:  # ok
    s = r.content
    html = s.decode()
    print(html)
    # strs = str(s)
    # print(strs.replace(r"\\\\",r"\\"))
    
    # html = r.content.decode('utf-8')
    # print(html)
    a = re.findall('imgJson = ([\s\S]*?);',html)
    # print(a)
    # exit()
    # print(a)
    # print(type(a))
    # print(a[0])
    import json
    jsonp = json.loads(a[0])
    
    folder = jsonp['gallery_title']
    picInfo = jsonp['picInfo']
    print(len(picInfo))
    print(folder)
    for i in picInfo:
        add_intro = i['add_intro']
        url = i['url']
        print(add_intro,url)