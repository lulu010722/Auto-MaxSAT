import subprocess
import pandas as pd
import os
import shutil

import chat
import run_benchmark


RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RESET = "\033[0m"


SRC_DIR = "source-code"


# 与chat相关的配置
ORIGIN_FILE_PATH = f"{SRC_DIR}/backup/heuristic.h.origin"
OPTIMIZED_FILE_PATH = f"{SRC_DIR}/heuristic.h"
TARGET_FUNC = "int USW::pick_var()"
ITER_NUM = 0


# 与test相关的配置
CUTOFF_TIME = 20  # 超过时间限制则结束当前实例的运算，单位是秒
INSTANCE_NUM_LIMIT = 2  # 运行实例数量上限，运行到这个数量就停机
INSTANCES_SIZE_LIMIT = 1024 * 1024 * 500  # 超过这个大小的就不计算了，因为WSL会爆炸！单位是字节，目前是500M
BENCHMARK_SET_PATH = "benchmark/mse24-anytime-weighted-old-format/abstraction-refinement_wt"  # 细分测试集


PROGRESS_HISTORY_DIR = "progress"


best_scores = []


def print_start_info(message):
    print(f"{YELLOW}{message}{RESET}")


def print_done_info(message):
    print(f"{GREEN}{message}{RESET}")


def read_best_scores():
    df = pd.read_csv("best_scores.csv")
    for _, row in df.iterrows():
        best_scores.append({
            "benchmark_set": row["benchmark_set"],
            "best_score": row["best_score"]
        })
    
    best_scores_benchmark_set = [item["benchmark_set"] for item in best_scores]
    benchmark_set = os.path.basename(BENCHMARK_SET_PATH)
    if benchmark_set not in best_scores_benchmark_set:
        new_row = pd.DataFrame([{"benchmark": benchmark_set, "best_score": 0.0}])
        new_row.to_csv("best_scores.csv", mode="a", index=False, header=False)


# 总共进化轮数
EPOCH = 2

if __name__ == "__main__":

    progress_cnt = 0

    for epoch in range(EPOCH):
        print_start_info("starting chatting with LLM to optimize the algorithm")
        # subprocess.run(["python", "chat.py", SRC_DIR, ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH, TARGET_FUNC, ITER_NUM])
        # chat.main(SRC_DIR, ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH, TARGET_FUNC, ITER_NUM)
        print_done_info("LLM interation done")

        print_start_info("making newly generated code into executable USW-LS")
        # subprocess.run(["make", "-C", "source-code"])
        print_done_info("make USW-LS done")

        print_start_info("running benchmark test")
        # subprocess.run(["python", "run_benchmark.py", CUTOFF_TIME, INSTANCE_NUM_LIMIT, INSTANCES_SIZE_LIMIT, BENCHMARK_SET_PATH])
        run_benchmark.main(CUTOFF_TIME, INSTANCE_NUM_LIMIT, INSTANCES_SIZE_LIMIT, BENCHMARK_SET_PATH)
        print_done_info("benchmark test done")

        read_best_scores()

        current_score = 0.0
        with open("temp", "r") as temp_file:
            current_score = float(temp_file.read())

        for item in best_scores:
            if item["benchmark_set"] == os.path.basename(BENCHMARK_SET_PATH):
                if current_score > item["best_score"]:
                    # 应该保留当前程序文件副本并更新状态
                    origin_filename = os.path.basename(ORIGIN_FILE_PATH)
                    shutil.copyfile(OPTIMIZED_FILE_PATH, f"{PROGRESS_HISTORY_DIR}/{origin_filename}._progress_{progress_cnt}")
                    progress_cnt += 1
                else:
                    print(f"the optimized version found in epoch {epoch} is not better")
