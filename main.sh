#!/bin/bash

timestamp=$(date +%Y.%m.%d_%H:%M:%S)

# 后台运行
# nohup python3 -u batch_evolve.py > output/output_$timestamp.ans 2>&1 &

# 前台运行
python3 -u batch_evolve.py > output/output_$timestamp.ans 2>&1
