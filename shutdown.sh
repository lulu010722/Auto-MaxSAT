#!/bin/bash

ps aux | grep auto_src/main.py | grep -v grep | awk '{print $2}' | xargs kill -9