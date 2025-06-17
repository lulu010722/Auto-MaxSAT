#!/bin/bash

# 用于将 benchmark/mse24-anytime-weighted 中的所有 .wcnf 文件转换为旧格式的脚本
find benchmark/** -name "*.wcnf" | while read file; do
    fname=$(basename "$file")
    target_file="benchmark/$fname"
    echo "Processing $file to $target_file"
    if [ -f "$target_file" ]; then
        echo "Skipping $fname, already converted."
        continue
    fi
    ./maxsat_benchmarks_code_base/bin/to_old_fmt "$file" > "$target_file"
done