#!/bin/bash

# usage: ./cmain.sh <concurrent_dir_number>
# example: ./cmain.sh 1

CONCURRENT_DIR=concurrent_$1

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


# 工具命令
# ps aux | grep single | grep -v grep
# ps aux | grep single | grep -v grep | awk '{print $2}' | xargs kill -9