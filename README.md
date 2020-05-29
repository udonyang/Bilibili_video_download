# Bilibili sucker

# Install
## Mac
```bash
pip3 install -r requirements.txt
brew install ffmpeg tesseract
```

# Usage
## fetch 
Fetch all video info of specific authors.
Ouput a json file.
```bash
python3 main.py fetch <mid csv>
```

## pull
Download all video specific by json, which is generated by fetch command, along with videocover, and fuzz watermark(It will success if you are lucky).
```bash
python3 main.py pull <video json>
```
