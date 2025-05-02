import subprocess
import pandas as pd
import os
import shutil
import sys
from pathlib import Path

import chat
import run_benchmark


RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RESET = "\033[0m"


src_dir = "source-code"


# 与chat相关的配置
ORIGIN_FILE_PATH = f"{src_dir}/backup/heuristic.h.origin"
OPTIMIZED_FILE_PATH = f"{src_dir}/heuristic.h"
TARGET_FUNC = "int USW::pick_var()"
ITER_NUM = 1


# 与test相关的配置
CUTOFF_TIME = 20  # 超过时间限制则结束当前实例的运算，单位是秒
INSTANCE_NUM_LIMIT = 100  # 运行实例数量上限，运行到这个数量就停机
INSTANCES_SIZE_LIMIT = 1024 * 1024 * 1024  # 超过这个大小的就不计算了，因为WSL会爆炸！单位是字节
BENCHMARK_DIR_PATH = "benchmark/mse24-anytime-weighted-old-format" # 细分测试集
BENCHMARK_SET_PATH = ""


# 总共进化轮数
EPOCH = 1
PROGRESS_HISTORY_DIR = "progress"


best_scores = []


def print_yellow(message):
    print(f"{YELLOW}{message}{RESET}")


def print_green(message):
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


def main():
    try:
        benchmark_set = sys.argv[1]
    except Exception as e:
        print(f"usage: python automation.py <benchmark_set>")
        exit(1)

    global BENCHMARK_SET_PATH
    BENCHMARK_SET_PATH = f"{BENCHMARK_DIR_PATH}/{benchmark_set}"

    progress_cnt = 0

    for epoch in range(EPOCH):
        print_yellow("starting chatting with LLM to optimize the algorithm")
        chat.main(src_dir, ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH, TARGET_FUNC, ITER_NUM)
        print_green("LLM interation done")

        print_yellow("making newly generated code into executable USW-LS")
        subprocess.run(["make", "-C", "source-code"])
        print_green("make USW-LS done")

        print_yellow("running benchmark test")
        run_benchmark.main(CUTOFF_TIME, INSTANCE_NUM_LIMIT, INSTANCES_SIZE_LIMIT, BENCHMARK_SET_PATH)
        print_green("benchmark test done")

        read_best_scores()

        with open("temp", "r") as temp_file:
            best_score_after_llm = float(temp_file.read())

        Path(PROGRESS_HISTORY_DIR).mkdir(parents=True, exist_ok=True)
        for item in best_scores:
            if item["benchmark_set"] == benchmark_set:
                if best_score_after_llm > item["best_score"] * 1.05: # 加5%门槛以排除评分波动
                    print_green(f"对于{benchmark_set}，第{epoch}轮问询找到了更好的算法")
                    origin_filename = os.path.basename(ORIGIN_FILE_PATH)
                    shutil.copyfile(OPTIMIZED_FILE_PATH, f"{PROGRESS_HISTORY_DIR}/{origin_filename}.progress_{progress_cnt}")
                    progress_cnt += 1

                    df = pd.read_csv("best_scores.csv")
                    df.loc[df["benchmark_set"] == benchmark_set, ["best_score"]] = [best_score_after_llm]
                    df.to_csv("best_scores.csv", index=False)

                else:
                    print_yellow(f"对于{benchmark_set}，第{epoch}轮问询没有找到更好的算法")


if __name__ == "__main__":
    main()