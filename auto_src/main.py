from pathlib import Path
from multiprocessing import Process, Queue, Lock
from datetime import datetime

import subprocess
import pandas as pd
import os
import shutil
import random
import re
import yaml
import sys
import json

import chat

with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)


TARGET_FUNCTIONS = config["train"]["target_functions"]
CUTOFF_TIME = config["runtime"]["cutoff_time"]
EPOCH = config["runtime"]["epoch"]
BENCHMARK_ITER_TIME = config["runtime"]["benchmark_iter_time"]

THRESHOLD_RATE = config["train"]["threshold_rate"]


def print_debug(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} \033[1;34mDEBUG   \033[34m{message}\033[0m")


def print_info(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} \033[1;32mINFO    \033[32m{message}\033[0m")


def print_warning(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} \033[1;33mWARNING \033[33m{message}\033[0m")


def print_error(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} \033[1;31mERROR   \033[31m{message}\033[0m")


def init() -> None:
    global logger

    with open("data/best_scores.csv", "w") as f:
        f.write("benchmark_set,best_score\n")
    for index in range(BENCHMARK_ITER_TIME):
        with open(f"data/my_costs_{index}.csv", "w") as f:
            f.write("instance,cost\n")

    shutil.copyfile("solver_src/baseline/heuristic.h.origin", "solver_src/heuristic.h")


def parse_executer_output(output: str) -> int:
    lines = output.splitlines()
    current_best = -2
    verified = False
    for line in lines:
        pattern = r"\bo [1-9][0-9]*\b"
        matches = re.findall(pattern, line)
        if len(matches) > 0:
            current_best = int(matches[0][2:])
        if "verified" in line:
            verified = True
    return current_best if verified else -2


def read_best_scores(benchmark_set: str) -> None:
    global BEST_SCORES
    BEST_SCORES = pd.read_csv("data/best_scores.csv").to_dict(orient="records")

    best_scores_benchmark_set = [item["benchmark_set"] for item in BEST_SCORES]
    benchmark_set = os.path.basename(f"{"benchmark_old"}/{benchmark_set}")
    if benchmark_set not in best_scores_benchmark_set:
        BEST_SCORES.append({"benchmark_set": benchmark_set, "best_score": 0.0})
        new_row = pd.DataFrame([{"benchmark_set": benchmark_set, "best_score": 0.0}])
        new_row.to_csv("data/best_scores.csv", mode="a", index=False, header=False)


def get_benchmark_set_feature(benchmark_set: str) -> str:
    feature = ""
    benchmark_set_path = f"benchmark_new/{benchmark_set}"
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


def run_single(benchmark_set_path: str, lock, queue: Queue, iter_index: int) -> None:
    global MY_COSTS, BEST_COSTS

    instances_path = [path.joinpath() for path in Path(benchmark_set_path).iterdir()]

    MY_COSTS = []
    for filepath in instances_path:
        filename = os.path.basename(filepath)
        seed = random.randint(0, 1000000)
        try:
            print_debug(f"测例开始: {filename}")
            output = subprocess.run(f"auto_src/starexec_usw-ls-runsolver.sh {filepath} {seed} {CUTOFF_TIME}", shell=True, capture_output=True, text=True).stdout
            cost = parse_executer_output(output)
            MY_COSTS.append({
                "instance": filename,
                "cost": cost
            })
            print_debug(f"测例完毕: {filename}, 代价: {cost}")
        except Exception as e:
            print_error(f"执行文件错误: {filename}: {e}")

    BEST_COSTS = pd.read_csv("data/best_costs.csv").to_dict(orient="records")

    with lock:
        write_costs_to_csv(iter_index)
    score = rate()
    queue.put(score)


def write_costs_to_csv(iter_index) -> None:
    df = pd.read_csv(f"data/my_costs_{iter_index}.csv")
    for my_cost_item in MY_COSTS:
        match = df["instance"] == my_cost_item["instance"]
        if match.any():
            df.loc[df["instance"] == my_cost_item["instance"], "cost"] = my_cost_item["cost"]
        else:
            df = pd.concat([df, pd.DataFrame([my_cost_item])], ignore_index=True)
    df.to_csv(f"data/my_costs_{iter_index}.csv", index=False)
    print_debug(f"输出结果已保存到data/my_costs_{iter_index}.csv")


def rate() -> float:
    tota_score = 0
    valid_instance_cnt = 0
    for my_cost_item in MY_COSTS:
        for best_cost_item in BEST_COSTS:
            if my_cost_item["instance"] != best_cost_item["instance"]:
                continue
            if my_cost_item["cost"] < 0:
                print_warning(f"实例{my_cost_item['instance']}的当前求解器代价没找到")
                continue
            if best_cost_item["cost"] < 0:
                print_warning(f"实例{best_cost_item['instance']}的最佳代价没找到")
                continue

            score = (1 + best_cost_item['cost']) / (1 + my_cost_item['cost'])
            tota_score += score
            valid_instance_cnt += 1

    return tota_score / valid_instance_cnt if valid_instance_cnt > 0 else 0


def write_progress(progress_cnt: int):
    files = [f for f in os.listdir("log") if os.path.isfile(os.path.join("log", f))]
    files.sort(key=lambda x: x.lower())
    with open(f"progress/{progress_cnt}", "w") as progress_file:
        with open(f"log/{files[-1]}", "r") as log_file:
            response = json.load(log_file)[2]["content"]
            progress_file.write(f"大模型的回答是:\n{response}\n")


def main(benchmark_set, lock):
    global BEST_SCORES

    init()
    benchmark_set_path = f"benchmark_old/{benchmark_set}"

    epoch = 0
    progress_cnt = 0
    make_fail_cnt = 0
    benchmark_set_feature = get_benchmark_set_feature(benchmark_set)

    while epoch < EPOCH:
        print_debug(f"========第{epoch}轮迭代开始！========")
        print_debug("开始LLM对话")
        chat.main(benchmark_set_feature, TARGET_FUNCTIONS)
        print_debug("LLM对话迭代完成")

        print_debug("构建算法可执行文件")
        make_result = subprocess.run(["make", "-C", "solver_src"])
        if make_result.returncode != 0:
            print_warning("Makefile执行失败，重新询问大模型")
            shutil.copyfile("solver_src/baseline/heuristic.h.origin", "solver_src/heuristic.h")

            if make_fail_cnt > EPOCH:
                print_error("Makefile执行失败次数过多，退出")
                return
            make_fail_cnt += 1
            continue
        print_debug("构建完成")

        processes = []
        queues = []
        for index in range(BENCHMARK_ITER_TIME):
            print_debug(f"对于{benchmark_set}的第{epoch}轮第{index}次平行基准测试开始")
            queue = Queue()
            process = Process(target=run_single, name=benchmark_set, args=(benchmark_set_path, lock, queue, index))
            process.start()
            queues.append(queue)
            processes.append(process)

        for index, process in enumerate(processes):
            process.join()
            print_debug(f"对于{benchmark_set}的第{epoch}轮第{index}次平行基准测试完成")

        scores = [queue.get() for queue in queues]
        score = sum(scores) / len(scores) if scores else 0
        print_info(f"{benchmark_set}的第{epoch}轮的平均得分是: {score}")
        read_best_scores(benchmark_set_path)

        Path("progress").mkdir(parents=True, exist_ok=True)

        for item in BEST_SCORES:
            if item["benchmark_set"] == benchmark_set:
                if score > item["best_score"] * THRESHOLD_RATE:
                    write_progress(progress_cnt)
                    shutil.copyfile("solver_src/heuristic.h", "solver_src/baseline/heuristic.h.origin")
                    progress_cnt += 1

                    with lock:
                        df = pd.read_csv("data/best_scores.csv")
                        df.loc[df["benchmark_set"] == benchmark_set, ["best_score"]] = [score]
                        df.to_csv("data/best_scores.csv", index=False)
                        print_info(f"对于{benchmark_set}，第{epoch}轮问询找到了更好的算法")

                else:
                    shutil.copyfile("solver_src/baseline/heuristic.h.origin", "solver_src/heuristic.h")
                    print_warning(f"对于{benchmark_set}，第{epoch}轮问询没有找到更好的算法")

        epoch += 1


if __name__ == "__main__":
    benchmark_set = sys.argv[1]
    lock = Lock()
    main(benchmark_set, lock)
