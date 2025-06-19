from pathlib import Path
from multiprocessing import Process, Queue, Lock

import subprocess
import pandas as pd
import os
import shutil
import random
import re
import yaml
import logging
import sys

import chat

with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

SOLVER_SRC_PATH = config["route"]["solver_src"]
ORIGIN_FILE_PATH = config["route"]["origin_file"]
OPTIMIZED_FILE_PATH = config["route"]["optimized_file"]
BENCHMARK_NEW_PATH = config["route"]["benchmark_new"]
BENCHMARK_OLD_PATH = config["route"]["benchmark_old"]
PROGRESS_DIR_PATH = config["route"]["progress"]
LOG_DIR_PATH = config["route"]["log"]
OUTPUT_DIR_PATH = config["route"]["output"]

EXECUTER_SCRIPT = config["route"]["executer"]

TARGET_FUNCTIONS = config["train"]["target_functions"]
CUTOFF_TIME = config["runtime"]["cutoff_time"]
EPOCH = config["runtime"]["epoch"]
BENCHMARK_ITER_TIME = config["runtime"]["benchmark_iter_time"]

BEST_COSTS_PATH = config["data"]["best_costs"]
BEST_SCORES_PATH = config["data"]["best_scores"]
MY_COSTS_PATH = config["data"]["my_costs"]

logger = logging.getLogger()

class StderrLogger:
    def write(self, message):
        if message.strip():
            logger.error(message.strip())

    def flush(self):
        pass


def init(benchmark_set) -> None:
    global logger

    with open(BEST_SCORES_PATH, "w") as f:
        f.write("benchmark_set,best_score\n")
    with open(MY_COSTS_PATH, "w") as f:
        f.write("instance,cost\n")

    shutil.copyfile(ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH)

    logger = logging.getLogger(benchmark_set)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(Path(OUTPUT_DIR_PATH) / f"{benchmark_set}.log")
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)-7s] %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    sys.stderr = StderrLogger()



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
    BEST_SCORES = pd.read_csv(BEST_SCORES_PATH).to_dict(orient="records")

    best_scores_benchmark_set = [item["benchmark_set"] for item in BEST_SCORES]
    benchmark_set = os.path.basename(f"{BENCHMARK_OLD_PATH}/{benchmark_set}")
    if benchmark_set not in best_scores_benchmark_set:
        BEST_SCORES.append({"benchmark_set": benchmark_set, "best_score": 0.0})
        new_row = pd.DataFrame([{"benchmark_set": benchmark_set, "best_score": 0.0}])
        new_row.to_csv(BEST_SCORES_PATH, mode="a", index=False, header=False)


def get_benchmark_set_feature(benchmark_set: str) -> str:
    feature = ""
    benchmark_set_path = f"{BENCHMARK_NEW_PATH}/{benchmark_set}"
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


def run_single(benchmark_set_path: str, lock, queue: Queue) -> None:
    global MY_COSTS, BEST_COSTS

    instances_path = [path.joinpath() for path in Path(benchmark_set_path).iterdir()]

    MY_COSTS = []
    for filepath in instances_path:
        filename = os.path.basename(filepath)
        seed = random.randint(0, 1000000)
        try:
            logger.info(f"运行测例文件: {filepath}")
            output = subprocess.run(f"./{EXECUTER_SCRIPT} {filepath} {seed} {CUTOFF_TIME}", shell=True, capture_output=True, text=True).stdout
            cost = parse_executer_output(output)
            MY_COSTS.append({
                "instance": filename,
                "cost": cost
            })
            logger.info(f"测例文件运行完毕: {filename}, 代价: {cost}")
        except Exception as e:
            logger.error(f"执行文件错误: {filename}: {e}")

    BEST_COSTS = pd.read_csv(BEST_COSTS_PATH).to_dict(orient="records")

    with lock:
        write_costs_to_csv()
    score = rate()
    logger.info(f"当前测例集的本轮评分: {score}")
    queue.put(score)


def write_costs_to_csv() -> None:
    df = pd.read_csv(MY_COSTS_PATH)
    for my_cost_item in MY_COSTS:
        match = df["instance"] == my_cost_item["instance"]
        if match.any():    
            df.loc[df["instance"] == my_cost_item["instance"], "cost"] = my_cost_item["cost"]
        else:
            df = pd.concat([df, pd.DataFrame([my_cost_item])], ignore_index=True)
    df.to_csv(MY_COSTS_PATH, index=False)
    logger.info(f"输出结果已保存到{MY_COSTS_PATH}")


def rate() -> float:
    tota_score = 0
    valid_instance_cnt = 0
    for my_cost_item in MY_COSTS:
        for best_cost_item in BEST_COSTS:
            if my_cost_item["instance"] != best_cost_item["instance"]:
                continue
            if my_cost_item["cost"] < 0:
                logger.warning(f"实例{my_cost_item['instance']}的当前求解器代价没找到")
                continue
            if best_cost_item["cost"] < 0:
                logger.warning(f"实例{best_cost_item['instance']}的最佳代价没找到")
                continue

            score = (1 + best_cost_item['cost']) / (1 + my_cost_item['cost'])
            tota_score += score
            valid_instance_cnt += 1

    return tota_score / valid_instance_cnt if valid_instance_cnt > 0 else 0


def main(benchmark_set, lock):
    global BEST_SCORES

    init(benchmark_set)
    benchmark_set_path = f"{BENCHMARK_OLD_PATH}/{benchmark_set}"

    epoch = 0
    progress_cnt = 0
    make_fail_cnt = 0
    benchmark_set_feature = get_benchmark_set_feature(benchmark_set)

    while epoch < EPOCH:
        logger.info("开始LLM对话")
        chat.main(benchmark_set_feature, TARGET_FUNCTIONS)
        logger.info("LLM对话迭代完成")

        logger.info("构建算法可执行文件")
        make_result = subprocess.run(["make", "-C", SOLVER_SRC_PATH])
        if make_result.returncode != 0:
            logger.warning("Makefile执行失败，重新询问大模型")
            shutil.copyfile(ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH)

            if make_fail_cnt > EPOCH:
                logger.error("Makefile执行失败次数过多，退出")
                return
            make_fail_cnt += 1
            continue
        logger.info("构建完成")

        processes = []
        queues = []
        for _ in range(BENCHMARK_ITER_TIME):
            logger.info(f"开始基准测试: {benchmark_set}")
            queue = Queue()
            process = Process(target=run_single, name=benchmark_set, args=(benchmark_set_path, lock, queue))
            process.start()
            queues.append(queue)
            processes.append(process)

        for process in processes:
            process.join()
            logger.info("基准测试完成")

        scores = [queue.get() for queue in queues]
        score = sum(scores) / len(scores) if scores else 0
        read_best_scores(benchmark_set_path)

        progress_of_benchmark_set_dir = f"{PROGRESS_DIR_PATH}/{benchmark_set}"
        Path(progress_of_benchmark_set_dir).mkdir(parents=True, exist_ok=True)

        for item in BEST_SCORES:
            if item["benchmark_set"] == benchmark_set:
                if score > item["best_score"] * 1.05:  # 加5%门槛以排除评分波动
                    origin_file = os.path.basename(ORIGIN_FILE_PATH)
                    shutil.copyfile(OPTIMIZED_FILE_PATH, f"{progress_of_benchmark_set_dir}/{origin_file}.progress_{progress_cnt}")
                    progress_cnt += 1

                    with lock:
                        df = pd.read_csv(BEST_SCORES_PATH)
                        df.loc[df["benchmark_set"] == benchmark_set, ["best_score"]] = [score]
                        df.to_csv(BEST_SCORES_PATH, index=False)
                        logger.info(f"对于{benchmark_set}，第{epoch}轮问询找到了更好的算法")

                else:
                    shutil.copyfile(ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH)
                    logger.warning(f"对于{benchmark_set}，第{epoch}轮问询没有找到更好的算法")

        epoch += 1


if __name__ == "__main__":
    benchmark_set = "drmx-crypt"
    lock = Lock()
    main(benchmark_set, lock)
