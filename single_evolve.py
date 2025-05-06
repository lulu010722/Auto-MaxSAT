import subprocess
import pandas as pd
import os
import shutil
import sys
from pathlib import Path

import chat
import run_benchmark


GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RESET = "\033[0m"


src_dir = "source-code"


# 与chat相关的配置
ORIGIN_FILE_PATH = f"{src_dir}/backup/heuristic.h.origin"
OPTIMIZED_FILE_PATH = f"{src_dir}/heuristic.h"
TARGET_FUNC = "int USW::pick_var()"
ITER_NUM = 1  # 和LLM对话的次数


# 与test相关的配置
CUTOFF_TIME = 20  # 超过时间限制则结束当前实例的运算，单位是秒
INSTANCE_NUM_LIMIT = 100  # 运行实例数量上限，运行到这个数量就停机
INSTANCES_SIZE_LIMIT = 1024 * 1024 * 1024 * 10  # 单位是字节
BENCHMARK_DIR_PATH = "benchmark/mse24-anytime-weighted-old-format"  # 细分测试集
BENCHMARK_SET_PATH = ""


EPOCH = 3  # 总共进化轮数
PROGRESS_HISTORY_ROOT_DIR = "progress"


best_scores = []


def print_yellow(message):
    print(f"{YELLOW}{message}{RESET}")


def print_green(message):
    print(f"{GREEN}{message}{RESET}")


def read_best_scores():
    global best_scores
    best_scores = pd.read_csv("best_scores.csv").to_dict(orient="records")

    best_scores_benchmark_set = [item["benchmark_set"] for item in best_scores]
    benchmark_set = os.path.basename(BENCHMARK_SET_PATH)
    if benchmark_set not in best_scores_benchmark_set:
        best_scores.append({"benchmark_set": benchmark_set, "best_score": 0.0})
        new_row = pd.DataFrame([{"benchmark_set": benchmark_set, "best_score": 0.0}])
        new_row.to_csv("best_scores.csv", mode="a", index=False, header=False)


def main(benchmark_set):

    global BENCHMARK_SET_PATH
    global best_scores
    BENCHMARK_SET_PATH = f"{BENCHMARK_DIR_PATH}/{benchmark_set}"

    progress_cnt = 0

    for epoch in range(EPOCH):
        print_yellow("开始LLM对话")
        chat.main(src_dir, ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH, TARGET_FUNC, ITER_NUM)
        print_green("LLM对话迭代完成")

        print_yellow("构建算法可执行文件")
        subprocess.run(["make", "-C", "source-code"])
        print_green("构建完成")

        print_yellow("开始基准测试")
        run_benchmark.main(CUTOFF_TIME, INSTANCE_NUM_LIMIT, INSTANCES_SIZE_LIMIT, BENCHMARK_SET_PATH)
        print_green("基准测试完成")

        read_best_scores()

        temp_file_name = "temp"
        with open(temp_file_name, "r") as temp_file:
            best_score_after_llm = float(temp_file.read())
        os.remove(temp_file_name)

        progress_history_wrt_benchmark_set_dir = f"{PROGRESS_HISTORY_ROOT_DIR}/{benchmark_set}"
        Path(progress_history_wrt_benchmark_set_dir).mkdir(parents=True, exist_ok=True)

        for item in best_scores:
            if item["benchmark_set"] == benchmark_set:
                if best_score_after_llm > item["best_score"] * 1.05:  # 加5%门槛以排除评分波动
                    origin_filename = os.path.basename(ORIGIN_FILE_PATH)
                    shutil.copyfile(OPTIMIZED_FILE_PATH, f"{progress_history_wrt_benchmark_set_dir}/{origin_filename}.progress_{progress_cnt}")
                    progress_cnt += 1

                    df = pd.read_csv("best_scores.csv")
                    df.loc[df["benchmark_set"] == benchmark_set, ["best_score"]] = [best_score_after_llm]
                    df.to_csv("best_scores.csv", index=False)
                    print_green(f"对于{benchmark_set}，第{epoch}轮问询找到了更好的算法")

                else:
                    print_yellow(f"对于{benchmark_set}，第{epoch}轮问询没有找到更好的算法")
