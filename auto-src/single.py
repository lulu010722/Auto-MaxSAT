from pathlib import Path

import subprocess
import pandas as pd
import os
import sys
import shutil
import multiprocessing
import json
import random
import re
import yaml
import logging

import chat

logger = logging.getLogger(__name__)

with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)


lock = multiprocessing.Lock()


SOLVER_SRC_PATH = ""
ORIGIN_FILE_PATH = ""
OPTIMIZED_FILE_PATH = ""
BENCHMARK_DIR_PATH = ""
PROGRESS_DIR_PATH = ""
LOG_DIR_PATH = ""

EXECUTER_SCRIPT = ""

TARGET_FUNCTIONS = []
CUTOFF_TIME = 0
EPOCH = 0
BENCHMARK_ITER_TIME = 0


MY_COSTS = []
BEST_COSTS = []
BEST_SCORES = []

BEST_COSTS_PATH = ""
BEST_SCORES_PATH = ""
MY_COSTS_PATH = ""

BENCHMARK_SET_PATH = ""


def init():
    global SOLVER_SRC_PATH, ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH, BENCHMARK_DIR_PATH, PROGRESS_DIR_PATH, LOG_DIR_PATH
    global EXECUTER_SCRIPT
    global TARGET_FUNCTIONS, CUTOFF_TIME, EPOCH, BENCHMARK_ITER_TIME
    global BENCHMARK_SET_PATH
    global BEST_SCORES_PATH, BEST_SCORES_PATH, MY_COSTS_PATH

    SOLVER_SRC_PATH = config["route"]["solver_src"]
    ORIGIN_FILE_PATH = config["route"]["origin_file"]
    OPTIMIZED_FILE_PATH = config["route"]["optimized_file"]
    BENCHMARK_DIR_PATH = config["route"]["benchmark"]
    PROGRESS_DIR_PATH = config["route"]["progress"]
    LOG_DIR_PATH = config["route"]["log"]

    EXECUTER_SCRIPT = config["route"]["executer"]

    TARGET_FUNCTIONS = config["train"]["target_functions"]
    CUTOFF_TIME = config["runtime"]["cutoff_time"]
    EPOCH = config["runtime"]["epoch"]

    BEST_COSTS_PATH = config["data"]["best_costs"]
    BEST_SCORES_PATH = config["data"]["best_scores"]
    MY_COSTS_PATH = config["data"]["my_costs"]


    with open(BEST_SCORES_PATH, "w") as f:
        f.write("benchmark_set,best_score\n")
    with open(MY_COSTS_PATH, "w") as f:
        pass

    shutil.rmtree(LOG_DIR_PATH, ignore_errors=True)
    shutil.rmtree(PROGRESS_DIR_PATH, ignore_errors=True)

    os.mkdir(LOG_DIR_PATH)
    os.mkdir(PROGRESS_DIR_PATH)

    shutil.copyfile(ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH)


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


def read_best_scores(benchmark_set):
    global BEST_SCORES
    BEST_SCORES = pd.read_csv("best_scores.csv").to_dict(orient="records")

    best_scores_benchmark_set = [item["benchmark_set"] for item in BEST_SCORES]
    benchmark_set = os.path.basename(f"benchmark/{benchmark_set}")
    if benchmark_set not in best_scores_benchmark_set:
        BEST_SCORES.append({"benchmark_set": benchmark_set, "best_score": 0.0})
        new_row = pd.DataFrame([{"benchmark_set": benchmark_set, "best_score": 0.0}])
        new_row.to_csv("best_scores.csv", mode="a", index=False, header=False)


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


def run_single_benchmark_set(benchmark_set_path, lock):
    global MY_COSTS

    instances_path = [path.name for path in Path(benchmark_set_path).iterdir()]

    MY_COSTS = []
    for filepath in instances_path:
        filename = os.path.basename(filepath)
        seed = random.randint(0, 1000000)
        logger.info(f"运行测例文件： {filepath}")
        try:
            output = subprocess.run(f"./{EXECUTER_SCRIPT} {filepath} {seed} {CUTOFF_TIME}", shell=True, capture_output=True, text=True).stdout
            cost = parse_executer_output(output)
            MY_COSTS.append({
                "instance": filename,
                "cost": cost,
                "best_cost": -1
            })
        except Exception as e:
            logger.error(f"Error running {filename}: {e}")

    with lock:
        BEST_COSTS = pd.read_csv("2024_best_costs.csv").to_dict(orient="records")
        compare_with_best_costs()
        write_costs_to_csv()

        score = rate()
        with open("temp", "a") as temp_file:
            temp_file.write(f"{score}\n")


def compare_with_best_costs():
    global MY_COSTS, BEST_COSTS
    for cost_item in MY_COSTS:
        for best_cost_item in BEST_COSTS:
            if cost_item["instance"] == best_cost_item["instance"]:
                cost_item["best_cost"] = best_cost_item["best_cost"]
                break
        else:
            logger.warning(f"实例{cost_item['instance']}的最佳cost没找到")


def write_costs_to_csv():
    my_costs_file = config["data"]["my_costs"]
    df = pd.DataFrame(MY_COSTS)
    df.to_csv(my_costs_file, index=False)
    logger.info(f"输出结果已保存到{my_costs_file}")


def rate():
    tota_score = 0
    valid_instance_cnt = 0
    for item in MY_COSTS:
        if item["cost"] < 0:
            logger.warning(f"实例{item['instance']}的my_cost没找到")
            continue
        if item["best_cost"] < 0:
            logger.warning(f"实例{item['instance']}的best_cost没找到")
            continue

        score = (1 + item['best_cost']) / (1 + item['cost'])
        tota_score += score
        valid_instance_cnt += 1

    return tota_score / valid_instance_cnt if valid_instance_cnt > 0 else 0


def main(benchmark_set):
    global BEST_SCORES

    init()
    benchmark_set_path = f"{BENCHMARK_DIR_PATH}/{benchmark_set}"

    progress_cnt = 0
    epoch = 0
    fail_cnt = 0
    benchmark_set_feature = get_benchmark_set_feature(benchmark_set)

    best_scores_with_epoch = []

    while epoch < EPOCH:
        logger.info("开始LLM对话")
        chat.main(benchmark_set_feature, TARGET_FUNCTIONS)
        logger.info("LLM对话迭代完成")

        logger.info("构建算法可执行文件")
        make_result = subprocess.run(["make", "-C", "source-code"])
        if make_result.returncode != 0:
            logger.warning("Makefile执行失败，重新询问大模型")
            shutil.copyfile(ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH)

            if fail_cnt > EPOCH:
                logger.error("Makefile执行失败次数过多，退出")
                return
            fail_cnt += 1
            continue
        logger.info("构建完成")

        best_scores_after_llm = []
        processes = []
        for i in range(BENCHMARK_ITER_TIME):
            logger.info("开始基准测试")
            process = multiprocessing.Process(target=run_single_benchmark_set, args=(CUTOFF_TIME, benchmark_set_path, lock))
            process.start()
            processes.append(process)

        for process in processes:
            process.join()
            logger.info("基准测试完成")

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

        progress_history_wrt_benchmark_set_dir = f"{PROGRESS_DIR_PATH}/{benchmark_set}"
        Path(progress_history_wrt_benchmark_set_dir).mkdir(parents=True, exist_ok=True)

        for item in BEST_SCORES:
            if item["benchmark_set"] == benchmark_set:
                if best_score_after_llm > item["best_score"] * 1.05:  # 加5%门槛以排除评分波动
                    origin_filename = os.path.basename(ORIGIN_FILE_PATH)
                    shutil.copyfile(OPTIMIZED_FILE_PATH, f"{progress_history_wrt_benchmark_set_dir}/{origin_filename}.progress_{progress_cnt}")
                    progress_cnt += 1

                    df = pd.read_csv("best_scores.csv")
                    df.loc[df["benchmark_set"] == benchmark_set, ["best_score"]] = [best_score_after_llm]
                    df.to_csv("best_scores.csv", index=False)
                    logger.info(f"对于{benchmark_set}，第{epoch}轮问询找到了更好的算法")

                else:
                    shutil.copyfile("source-code/iterations/iteration_0.txt", "source-code/heuristic.h")
                    logger.warning(f"对于{benchmark_set}，第{epoch}轮问询没有找到更好的算法")

        epoch += 1

    with open("best_scores_with_epoch.json", "w") as output_file:
        json.dump(best_scores_with_epoch, output_file)


if __name__ == "__main__":
    init()
    benchmark_set = sys.argv[1]
    main(benchmark_set)

