#!/bin/bash

# 安装依赖
pip install -r requirements.txt

# 检查依赖是否安装成功
if [ $? -eq 0 ]; then
    echo "依赖安装成功"
else
    echo "依赖安装失败"
    exit 1
fi

# 运行脚本
python window.py