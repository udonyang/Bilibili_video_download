- [安装](#安装)
- [用法](#用法)
- [生成文件](#生成文件)

# 吸B站
一个下载的工具，肥宅们都懂

# 安装
## Win10
1. win+s
2. 搜索栏输入ubuntu，找到应用商店安装入口
3. 打开ubuntu，然后走ubuntu的安装流程

## Ubuntu
复制下面的命令，执行就ok，install.sh可能会要求输入sudo密码，输入就好了，因为要安装依赖
```bash
git clone https://github.com/udonyang/BilibiliSucker.git --depth=1
cd BilibiliSucker
bash install.sh
```

## Mac
没钱

# 用法
先编辑一个包含up主id的列表文件，例如叫test.txt，一行一个up主，然后执行该两个命令，会以up主为单位进行并发
```bash
python3 main.py fetch test.txt
python3 main.py pull test.txt.json
```
然后，视频就会下载在当前目录，一个叫bilibili_video的文件夹里头，每个up主一个文件夹，执行下面的命令，就能跳到视频所在的文件夹了
```bash
explorer.exe .
```
中断程序执行，可以用Ctrl+C

# 生成文件
|格式|内容
|:-|:-
|mp4|骑兵
|flv|步兵
|bmp|调试文件
|jpg|封面
