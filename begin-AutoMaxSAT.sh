#!/bin/bash

python source-code/chat.py
make -C source-code
python test.py

