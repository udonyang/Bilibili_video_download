#!/bin/bash


function install()
{
  #if [[ ! -f ${bak} ]]; then
  #  sudo cp -bf conf/sources.list /etc/apt/
  #fi
  sudo apt update
  sudo apt install -y python3 python3-pip ffmpeg tesseract-ocr libtesseract-dev
  pip3 install -r conf/requirements.txt
  python3 -c 'import imageio; imageio.plugins.ffmpeg.download()'
  return 0
}

function uninstall()
{
  sudo mv -f ${bak} ${ori}
  sudo apt update
}

function main()
{
  local cmd=${1}
  local ori=/etc/apt/sources.list
  local bak=/etc/apt/sources.list~
  if [[ ! -z ${cmd} ]]; then 
    ${cmd}
  else
    install
  fi
  return 0
}

main ${*}
