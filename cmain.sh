#!/bin/bash

rm -rf concurrent/

mkdir -p concurrent/template

rsync -av \
      --exclude='__pycache__' \
      --exclude='benchmark' \
      --exclude='maxsat_benchmarks_code_base' \
      --exclude='mse24-anytime-weighted.zip' \
      --exclude='.git' \
      . \
      concurrent/template

cd concurrent

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