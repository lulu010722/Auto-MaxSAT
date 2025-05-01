#!/bin/bash


RED="\e[1;31m"
GREEN="\e[1;32m"
YELLOW="\e[1;33m"
NC="\e[0m"

SRC_DIR="source-code"

# 与chat相关的配置
ORIGIN_FILE_PATH="${SRC_DIR}/backup/heuristic.h.origin"
OPTIMIZED_FILE_PATH="${SRC_DIR}/heuristic.h"
TARGET_FUNC="int USW::pick_var()"
ITER_NUM=1

# 与test相关的配置
CUTOFF_TIME=5  # 超过时间限制则结束当前实例的运算，单位是秒
INSTANCE_NUM_LIMIT=2  # 运行实例数量上限，运行到这个数量就停机
INSTANCES_SIZE_LIMIT=104857600  # 超过这个大小的就不计算了，因为WSL会爆炸！单位是字节，目前是100M
BENCHMARK_SET_PATH="benchmark/mse24-anytime-weighted-old-format/abstraction-refinement_wt"  # 细分测试集

echo -e "${YELLOW}starting chatting with LLM to optimize the algorithm.${NC}"
python chat.py "$SRC_DIR" "$ORIGIN_FILE_PATH" "$OPTIMIZED_FILE_PATH" "$TARGET_FUNC" "$ITER_NUM"
echo -e "${GREEN}LLM interation done.${NC}"

echo -e "${YELLOW}making newly generated code into executable USW-LS.${NC}"
make -C source-code
echo -e "${GREEN}make USW-LS done.${NC}"

echo -e "${YELLOW}running benchmark test.${NC}"
python test.py "$CUTOFF_TIME" "$INSTANCE_NUM_LIMIT" "$INSTANCES_SIZE_LIMIT" "$BENCHMARK_SET_PATH"
echo -e "${GREEN}benchmark test done.${NC}"
