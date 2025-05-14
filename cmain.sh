#!/bin/bash

# usage: ./cmain.sh
# example: ./cmain.sh

work_dir=$(cd "$(dirname "$0")"; pwd)

index=$(cat concurrent/index)

CONCURRENT_DIR=concurrent/concurrent_$index

rm -rf $CONCURRENT_DIR

mkdir -p $CONCURRENT_DIR/template

rsync -av \
      --exclude='__pycache__' \
      --exclude='benchmark' \
      --exclude='maxsat_benchmarks_code_base' \
      --exclude='mse24-anytime-weighted.zip' \
      --exclude='.git' \
      --exclude='concurrent*' \
      . \
      $CONCURRENT_DIR/template

cd $CONCURRENT_DIR

cd template
rm -rf .git
cd ..

for i in $(seq 0 16); do
    cp -rf template "sub_$i"
done

rm -f "template/benchmark"
ln -s "/home/users/tylu/USW-LS-LLM/benchmark" "template/benchmark"
for i in {0..16}; do
    rm -f "sub_$i/benchmark"
    ln -s "/home/users/tylu/USW-LS-LLM/benchmark" "sub_$i/benchmark"
done


cd $work_dir
python3 cmain.py

new_index=$((index + 1))
echo $new_index > concurrent/index

# 工具命令
# ps aux | grep single | grep -v grep
# ps aux | grep single | grep -v grep | awk '{print $2}' | xargs kill -9