import subprocess
import pandas as pd
import os
import sys
import shutil
import multiprocessing
import json
from pathlib import Path

import src.chat as chat
import run_benchmark


lock = multiprocessing.Lock()


RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RESET = "\033[0m"


src_dir = "source-code"


# 与chat相关的配置
ORIGIN_FILE_PATH = f"{src_dir}/backup/heuristic.h.origin"
OPTIMIZED_FILE_PATH = f"{src_dir}/heuristic.h"
TARGET_FUNCS = [
    "int USW::pick_var()",
    "void USW::hard_increase_weights()",
    "void USW::soft_increase_weights_partial()",
    "void USW::soft_increase_weights_not_partial()",
    "void USW::hard_smooth_weights()",
    "void USW::soft_smooth_weights()",
]


# 与test相关的配置
CUTOFF_TIME = 30  # 超过时间限制则结束当前实例的运算，单位是秒
INSTANCE_NUM_LIMIT = 200  # 运行实例数量上限，运行到这个数量就停机
INSTANCES_SIZE_LIMIT = 1024 * 1024 * 1024 * 10  # 单位是字节
BENCHMARK_DIR_PATH = "benchmark"  # 细分测试集
BENCHMARK_ITER_TIME = 16  # 遍历测试集次数


EPOCH = 10  # 总共进化轮数
PROGRESS_HISTORY_ROOT_DIR = "progress"


best_scores = []


def print_red(message):
    print(f"{RED}{message}{RESET}")


def print_yellow(message):
    print(f"{YELLOW}{message}{RESET}")


def print_green(message):
    print(f"{GREEN}{message}{RESET}")


def read_best_scores(benchmark_set):
    global best_scores
    best_scores = pd.read_csv("best_scores.csv").to_dict(orient="records")

    best_scores_benchmark_set = [item["benchmark_set"] for item in best_scores]
    benchmark_set = os.path.basename(f"benchmark-new-format/{benchmark_set}")
    if benchmark_set not in best_scores_benchmark_set:
        best_scores.append({"benchmark_set": benchmark_set, "best_score": 0.0})
        new_row = pd.DataFrame([{"benchmark_set": benchmark_set, "best_score": 0.0}])
        new_row.to_csv("best_scores.csv", mode="a", index=False, header=False)


def reset_baseline_file():
    # 在评分没有更高时，重置算法骨架
    shutil.copyfile("source-code/iterations/iteration_0.txt", "source-code/heuristic.h")


# 获取某个子测例集中第一个测例文件的问题结构特征，就用原生的格式，可以去掉开头的先导comment字符c
def get_benchmark_set_feature(benchmark_set):
    feature = ""
    benchmark_set_path = f"benchmark-new-format/{benchmark_set}"
    wcnf_file = os.listdir(benchmark_set_path)[0]
    with open(os.path.join(benchmark_set_path, wcnf_file), "r") as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith("c--"):
                return feature
            elif line.startswith("c"):
                feature += line[1:]
            else:
                return feature
    return feature


def main(benchmark_set):
    global best_scores

    init()
    benchmark_set_path = f"{BENCHMARK_DIR_PATH}/{benchmark_set}"

    if False:  # 在测试大模型交互性能时，可以把这个迭代前测评关了
        print_yellow("训练前的基准测试")
        run_benchmark.main(CUTOFF_TIME, INSTANCE_NUM_LIMIT, INSTANCES_SIZE_LIMIT, benchmark_set_path)
        print_green("训练前基准测试完成")

        read_best_scores(benchmark_set_path)

        temp_file_name = "temp"
        with open(temp_file_name, "r") as temp_file:
            best_score_after_llm = float(temp_file.read())
        os.remove(temp_file_name)
        df = pd.read_csv("best_scores.csv")
        df.loc[df["benchmark_set"] == benchmark_set, ["best_score"]] = [best_score_after_llm]
        df.to_csv("best_scores.csv", index=False)

    progress_cnt = 0

    epoch = 0
    fail_cnt = 0
    benchmark_set_feature = get_benchmark_set_feature(benchmark_set)

    best_scores_with_epoch = []

    while epoch < EPOCH:
        target_func_num = len(TARGET_FUNCS)
        print_yellow("开始LLM对话")
        chat.main(src_dir, benchmark_set_feature, ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH, TARGET_FUNCS[epoch % target_func_num], TARGET_FUNCS)
        print_green("LLM对话迭代完成")

        print_yellow("构建算法可执行文件")
        make_result = subprocess.run(["make", "-C", "source-code"])
        if make_result.returncode != 0:
            print_red("Makefile执行失败，重新询问大模型")
            reset_baseline_file()
            if fail_cnt > EPOCH:
                print_red("Makefile执行失败次数过多，退出")
                return
            fail_cnt += 1
            continue
        print_green("构建完成")

        best_scores_after_llm = []
        processes = []
        for i in range(BENCHMARK_ITER_TIME):
            print_yellow("开始基准测试")
            process = multiprocessing.Process(target=run_benchmark.main, args=(CUTOFF_TIME, INSTANCE_NUM_LIMIT, INSTANCES_SIZE_LIMIT, benchmark_set_path, lock))
            process.start()
            processes.append(process)


        for process in processes:
            process.join()
            print_green("基准测试完成")

        read_best_scores(benchmark_set_path)

        with open("temp", "r") as temp_file:
            for line in temp_file.readlines():
                best_scores_after_llm.append(float(line.strip()))
        os.remove("temp")

        best_score_after_llm = max(best_scores_after_llm)
        best_scores_with_epoch.append({
            "epoch": epoch,
            "scores": best_scores_after_llm
        })

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
                    reset_baseline_file()
                    print_yellow(f"对于{benchmark_set}，第{epoch}轮问询没有找到更好的算法")

        epoch += 1
    
    with open("best_scores_with_epoch.json", "w") as output_file:
        json.dump(best_scores_with_epoch, output_file)


def init():
    with open("best_scores.csv", "w") as f:
        f.write("benchmark_set,best_score\n")
    with open("2024_my_costs.csv", "w") as f:
        pass

    shutil.rmtree("source-code/iterations", ignore_errors=True)
    shutil.rmtree("source-code/log", ignore_errors=True)
    shutil.rmtree("progress", ignore_errors=True)

    os.mkdir("source-code/iterations")
    os.mkdir("source-code/log")
    os.mkdir("progress")

    shutil.copyfile("source-code/backup/heuristic.h.origin", "source-code/heuristic.h")


if __name__ == "__main__":
    init()
    benchmark_set = sys.argv[1]
    main(benchmark_set)
