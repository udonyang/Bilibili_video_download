#!/usr/local/bin/python3
# -*- coding:utf-8 -*-

from moviepy.editor import *
import base64
import binascii
import hashlib
import imageio
import json
import math
import os
import re
import requests
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
import urllib.request

imageio.plugins.ffmpeg.download()

USAGE="""
learnlearn.py fetch <mid csv>
learnlearn.py pull <fetch info> 
"""

def RunCmd(cmd):
    # print('--------' + cmd)
    proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='latin1')
    output, error = proc.communicate() 
    # print(output)
    return (output, error)

def RemoveWatermark(video, dst_video):
    PROBCMD = 'ffprobe -v quiet -print_format json -show_format -show_streams {}'
    output, error = RunCmd(PROBCMD.format(video))
    probe = json.loads(output)
    print(probe)

    width = 0
    height = 0
    for stream in probe["streams"]:
        if stream["codec_type"] == "video":
            width = stream["width"]
            height = stream["height"]

    if width == 0 or height == 0:
        sys.stderr.write("fuck can't probe {}\n".format(video))
        return 1

    wm_width = math.floor(width/820*320)
    wm_height = math.floor(height/520*59)
    wshift = width-(wm_width+2)
    hshift = height-(wm_height+2)

    wms = {
            "tl": { "x": 1, "y": 1 },
            "tr": { "x": wshift, "y": 1 },
            "br": { "x": wshift, "y": hshift },
            "bl": { "x": 1, "y": hshift }
            }

    
    # TODO random pick multi pic in each corner
    acs = []
    for k, v in wms.items():
        OTMPL = '{}.{}.bmp'
        ofile = OTMPL.format(video, k)

        CMD = "ffmpeg -v 0 -y -ss 1 -i {} -vf crop=x={}:y={}:w={}:h={} -frames:v 1 {}"
        output, error = RunCmd(CMD.format(video, v["x"], v["y"], wm_width, wm_height, ofile))

        OCR = "tesseract {} stdout -l eng+chi_sim".format(ofile)
        output, error = RunCmd(OCR.format(ofile))
        
        output = output.strip()
        if len(output) > 0:
            acs.append((ofile, v, output))
            # print(acs)

    if len(acs) == 1:
        # sys.stderr.write("detected: acs["+str(acs)+"]\n")
        _, wm, res = acs[0]
        RMCMD = "ffmpeg -y -i {} -vf delogo=x={}:y={}:w={}:h={} {}"
        output, error = RunCmd(RMCMD.format(video, wm["x"], wm["y"], wm_width, wm_height, dst_video))
        if error.find("Conversion failed!") != -1:
            sys.stderr.write("{} fuck up\n".format(video)+error)
            os.remove(dst_video)
            return 2
    else:
        print("i don't know how to remove: len(acs)={}".format(str(acs)))
        return 3
    
    return 0

def signal_handler(signal,frame):
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


def down_video(mid, cid, video_list, title, start_url, page, pic_url):
    currentVideoPath = os.path.join(os.getcwd(), 'bilibili_video', 'up_'+mid.strip())
    if not os.path.exists(currentVideoPath):
        os.makedirs(currentVideoPath)
    for i in video_list:
        headers = {
                'User-Agent': 'Mozilla/5.0 Macintosh; Intel Mac OS X 10.13; rv:56.0 Gecko/20100101 Firefox/56.0',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Range': 'bytes=0-',
                'Referer': start_url,
                'Origin': 'https://www.bilibili.com',
                'Connection': 'keep-alive',
                }

        if not os.path.exists(currentVideoPath):
            os.makedirs(currentVideoPath)

        tmp_video_name = os.path.join(currentVideoPath, r'{}.{}.flv'.format(mid, cid))
        filename = os.path.join(currentVideoPath, r'{}.flv'.format(title))
        print('{} ----> {}'.format(tmp_video_name, filename))
        if os.access(filename, 4) == False:
            buf = requests.get(i, headers = headers, timeout = 3).content
            tmp_video = open(tmp_video_name, 'wb')
            tmp_video.write(buf)
            tmp_video.flush()
            shutil.move(tmp_video_name, filename)

        picname = os.path.join(currentVideoPath, r'{}.jpg'.format(title))
        if os.access(picname, 4) == False:
            open(picname, 'wb').write(requests.get(pic_url, timeout = 3).content)

        tmp_rwm_video_name = os.path.join(currentVideoPath, r'{}.delogo.mp4'.format(tmp_video_name))
        rwm_video_name = os.path.join(currentVideoPath, r'{}.delogo.mp4'.format(title))
        if os.access(rwm_video_name, 4) == False:
            shutil.copyfile(filename, tmp_video_name)
            if RemoveWatermark(tmp_video_name, tmp_rwm_video_name) == 0:
                shutil.move(tmp_rwm_video_name, rwm_video_name)
                os.remove(filename)
            os.remove(tmp_video_name)
            os.remove(tmp_rwm_video_name)

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
        infofile = open(sys.argv[2]+'.json', 'w')

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

        json.dump(middb, infofile)

    elif cmd == 'pull':
        middb = json.load(open(sys.argv[2], 'r'))

        cidinfos = []
        for k, v in middb.items():
            print('{}: {}'.format(k, len(v)))
            
            def DownloadOneMid(mid, vlist):
                # donefile = open('up.'+str(mid)+'.csv', 'w')
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
                            down_video(mid, cid, video_list, item["title"], start_url, page, item["pic"])
                        except Exception as err:
                            print('FATAL: {}'.format(err))
                            traceback.print_exc()
                            continue
                        row = '{},{},{}\n'.format(item['aid'], item['pic'], item['title'])
                        # donefile.write(row)
                        # donefile.flush()
                    except Exception as err:
                        print('FATAL: fuck damn {} '.format(k))
                        traceback.print_exc()
                    # break

            while True:
                if threading.active_count() < 10:
                    # print('fuck damn {} '.format(k))
                    threading.Thread(target=DownloadOneMid, args=(k, v["vlist"])).start()
                    break
                else:
                    time.sleep(1)

    else:
        print(USAGE)
