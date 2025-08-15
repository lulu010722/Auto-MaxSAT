#!/bin/bash

set -euo pipefail

ZIP_FILE="mse24-anytime-weighted.zip"
NEW_DIR="~/benchmark_new"
OLD_DIR="~/benchmark_old"


mkdir -p "$TARGET_DIR"
unzip -o "$ZIP_FILE" -d "$TARGET_DIR"

find "$TARGET_DIR" -type f -name "*.xz" -exec unxz {} \;

find "$TARGET_DIR" -type f -name "*.wcnf" | while read -r file; do
    out="$file"
    ./maxsat_benchmarks_code_base/bin/to_old_fmt "$file" > "$OLD_DIR/$out"
done

for benchmark_dir in "$NEW_DIR $OLD_DIR"; do
    find "$NEW_DIR" -maxdepth 1 -type | while read -r filepath; do
        filename=$(basename "$filepath")
        prefix=${filename:0:10}
        subdir="$OLD_DIR/$prefix"
        mkdir -p "$subdir"
        mv "$filepath" "$subdir/"
    done
done


find 
