#!/bin/bash


work_dir=$(cd "$(dirname "$0")"; pwd)
timestamp=$(date "+%Y%m%d_%H%M%S")
CONCURRENT_DIR=concurrent/$timestamp
benchmark_sets=$(find benchmark_old -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)

rm -rf $CONCURRENT_DIR
mkdir -p $CONCURRENT_DIR/template
rsync -av \
      --exclude='__pycache__' \
      --exclude='.vscode' \
      --exclude='benchmark_new' \
      --exclude='benchmark_old' \
      --exclude='concurrent' \
      --exclude='mse24-anytime-weighted.zip' \
      --exclude='.git' \
      --exclude='util' \
      --exclude='test*' \
      --exclude='start*' \
      . \
      $CONCURRENT_DIR/template


cd $CONCURRENT_DIR

for benchmark_set in $benchmark_sets; do
    cp -rf template $benchmark_set
done

cd template
ln -s "/home/users/tylu/auto/benchmark_new" "benchmark_new"
ln -s "/home/users/tylu/auto/benchmark_old" "benchmark_old"
cd ..

for benchmark_set in $benchmark_sets; do
    cd $benchmark_set
    ln -s "/home/users/tylu/auto/benchmark_new" "benchmark_new"
    ln -s "/home/users/tylu/auto/benchmark_old" "benchmark_old"
    cd ..
done

cd $work_dir

python start.py concurrent/$timestamp

# 工具命令
# ps aux | grep single | grep -v grep
# ps aux | grep single | grep -v grep | awk '{print $2}' | xargs kill -9