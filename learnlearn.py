# !/usr/bin/python3
# -*- coding:utf-8 -*-

import requests
import time
import hashlib
import urllib.request
import re
import json
from moviepy.editor import *
import os
import sys
import threading
import traceback
import signal
import imageio
imageio.plugins.ffmpeg.download()

USAGE="""
learnlearn.py fetch <mid csv> <fetch info>
learnlearn.py pull <fetch info> 
"""


def signal_handler(signal,frame):
    Show()
    sys.exit(0)
 
signal.signal(signal.SIGINT,signal_handler)

def get_play_list(start_url, cid, quality):
    entropy = 'rbMCKn@KuamXWlPMoJGsKcbiJKUfkPF_8dABscJntvqhRSETg'
    appkey, sec = ''.join([chr(ord(i) + 2) for i in entropy[::-1]]).split(':')
    params = 'appkey=%s&cid=%s&otype=json&qn=%s&quality=%s&type=' % (appkey, cid, quality, quality)
    chksum = hashlib.md5(bytes(params + sec, 'utf8')).hexdigest()
    url_api = 'https://interface.bilibili.com/v2/playurl?%s&sign=%s' % (params, chksum)
    headers = {
        'Referer': start_url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    # print(url_api)
    html = requests.get(url_api, headers=headers).json()
    # print(json.dumps(html))
    video_list = []
    for i in html['durl']:
        video_list.append(i['url'])
    # print(video_list)
    return video_list


def down_video(mid, video_list, title, start_url, page):
    currentVideoPath = os.path.join(sys.path[0], 'bilibili_video', 'up_'+mid.strip())
    print(currentVideoPath)
    if not os.path.exists(currentVideoPath):
        os.makedirs(currentVideoPath)
    for i in video_list:
        opener = urllib.request.build_opener()
        # 请求头
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0'),
            ('Accept', '*/*'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Accept-Encoding', 'gzip, deflate, br'),
            ('Range', 'bytes=0-'),
            ('Referer', start_url),
            ('Origin', 'https://www.bilibili.com'),
            ('Connection', 'keep-alive'),
        ]
        urllib.request.install_opener(opener)

        if not os.path.exists(currentVideoPath):
            os.makedirs(currentVideoPath)

        urllib.request.urlretrieve(url=i, filename=os.path.join(currentVideoPath, r'{}.flv'.format(title)))

if __name__ == '__main__':

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
    }

    if len(sys.argv) < 2:
        print(USAGE)
        exit(-2)

    cmd = sys.argv[1]
    if cmd == 'fetch':
        middb = {}

        ups = open(sys.argv[2], 'r').readlines()
        infofile = open(sys.argv[3], 'w')

        for mid in ups:
            mid = mid.strip('\n')

            middb[mid] = {}
            middb[mid]['vlist'] = []
            cnt = 25
            pn = 1
            ps = cnt
            while True:
                url = 'https://api.bilibili.com/x/space/arc/search?&pn='+str(pn)+'&ps='+str(ps)+'&jsonp=jsonp&mid='+mid
                resp = requests.get(url, headers=headers).json()
                new_vlist = resp["data"]["list"]["vlist"]
                middb[mid]['vlist'].extend(new_vlist)
                if (len(new_vlist) < cnt):
                    break
                else:
                    pn += 1

            # print(middb[mid]['vlist'])
            # middb[mid]['cid_list'] = []
            # for v in middb[mid]['vlist']:
            #     try:
            #         url = 'https://api.bilibili.com/x/web-interface/view?bvid='+v["bvid"]
            #         resp = requests.get(url, headers=headers).json()
            #         if resp["code"] != 0:
            #             print(url)
            #             print(resp)
            #             continue

            #         time.sleep(0.05)

            #         data = resp["data"]
            #         # print(data)
            #         aid = data["aid"]
            #         pic = data["pic"]
            #         title = data["title"]

            #         data['pages'][0]["aid"] = aid
            #         data['pages'][0]["title"] = title
            #         data['pages'][0]["pic"] = pic
            #         middb[mid]['cid_list'].append(data['pages'][0])
            #     except Exception as err:
            #         traceback.print_exc()
            #         exit(1)
        json.dump(middb, infofile)

    elif cmd == 'pull':
        middb = json.load(open(sys.argv[2], 'r'))

        cidinfos = []
        for k, v in middb.items():
            print('{}: {}'.format(k, len(v)))
            
            def DownloadOneMid(mid, vlist):
                donefile = open('up.'+str(mid)+'.csv', 'w')
                for i, v in enumerate(vlist):
                    try:
                        def vtoitem(v):
                            url = 'https://api.bilibili.com/x/web-interface/view?bvid='+v["bvid"]
                            resp = requests.get(url, headers=headers).json()
                            if resp["code"] != 0:
                                print(url)
                                print(resp)
                                return None

                            data = resp["data"]
                            # print(data)
                            aid = data["aid"]
                            pic = data["pic"]
                            title = data["title"]

                            data['pages'][0]["aid"] = aid
                            data['pages'][0]["title"] = title
                            data['pages'][0]["pic"] = pic
                            return data['pages'][0]

                        item = vtoitem(v)
                        if item == None:
                            print(v)
                            continue

                        cid = str(item['cid'])
                        page = str(item['page'])
                        start_url = 'https://api.bilibili.com/x/web-interface/view?aid='+str(item['aid'])
                        start_url = start_url + "/?p=" + page
                        video_list = get_play_list(start_url, cid, 32)
                        try:
                            down_video(mid, video_list, item["title"], start_url, page)
                        except Exception as err:
                            print(err)
                            print(video_list)
                            continue
                        row = '{},{},{}\n'.format(item['aid'], item['pic'], item['title'])
                        donefile.write(row)
                        donefile.flush()
                    except Exception as err:
                        traceback.print_exc()

            while True:
                if threading.active_count() < 10:
                    print('fuck '+str(k))
                    threading.Thread(target=DownloadOneMid, args=(k, v["vlist"])).start()
                    break
                else:
                    time.sleep(1)

    else:
        print(USAGE)
