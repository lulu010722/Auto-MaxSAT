#!/bin/bash

timestamp=$(date +%Y.%m.%d_%H:%M:%S)

# 后台运行
nohup python3 -u batch_evolve.py > output/output_$timestamp.ans 2>&1 &

# 前台运行
# python3 batch_evolve.py

# 杀掉进程
# ps aux | grep batch_evolve.py | grep -v grep | awk '{print $2}' | xargs kill -9