# -*- coding: utf-8 -*-

import sys
import math
import subprocess
import os
import json
import base64
import shutil
import binascii

def RunCmd(cmd):
    # print('--------' + cmd)
    proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='latin1')
    output, error = proc.communicate() 
    # print(output)
    return (output, error)

def Main(video):
    video_name = video.split('.')
    suffix = video_name[-1]
    prefix = video_name[:-1]
    b64video = binascii.hexlify('.'.join(prefix).encode('utf8')).decode('utf8')+ '.' + suffix
    # print(video_name)
    # print(suffix)
    # print(prefix)
    # print(b64video)
    shutil.copyfile(video, b64video)

    orivideo = video
    video = b64video

    PROBCMD = 'ffprobe -v quiet -print_format json -show_format -show_streams {}'
    output, error = RunCmd(PROBCMD.format(video))
    probe = json.loads(output)

    width = 0
    height = 0
    for stream in probe["streams"]:
        if stream["codec_type"] == "video":
            width = stream["width"]
            height = stream["height"]

    if width == 0 or height == 0:
        sys.stderr.write("fuck can't probe {}\n".format(video))
        return 0

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

    if len(acs) == 0:
        RMCMD = "ffmpeg -y -i {} {}.delogo.mp4"
        output, error = RunCmd(RMCMD.format(video, video))
    elif len(acs) == 1:
        # sys.stderr.write("detected: acs["+str(acs)+"]\n")
        _, wm, res = acs[0]
        DELOGO_FMT = '{}.delogo.mp4'
        delogofile = DELOGO_FMT.format(video)
        RMCMD = "ffmpeg -y -i {} -vf delogo=x={}:y={}:w={}:h={} {}"
        output, error = RunCmd(RMCMD.format(video, wm["x"], wm["y"], wm_width, wm_height, delogofile))
        if error.find("Conversion failed!") != -1:
            sys.stderr.write("{} fuck up\n".format(video)+error)
            os.remove(delogofile)
        else:
            shutil.move(delogofile, DELOGO_FMT.format(orivideo))
    else:
        print("i don't know how to remove: len(acs)={}".format(str(acs)))
    
    return 0

if __name__ == '__main__':
    video = sys.argv[1]
    Main(video)
