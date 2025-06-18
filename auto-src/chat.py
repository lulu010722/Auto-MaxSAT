from openai import OpenAI
from pathlib import Path

import json
import time
import datetime
import shutil
import numpy as np
import random
import yaml
import logging

logger = logging.getLogger(__name__)


API_KEY = ""
BASE_URL = ""
MODEL = ""
TEMPERATURE = 0.0

SOLVER_SRC_PATH = ""
ORIGIN_FILE_PATH = ""
OPTIMIZED_FILE_PATH = ""
LOG_DIR_PATH = ""

SYSTEM_PROMPT = ""
USER_PROMPT = ""

BENCHMARK_SET_FEATURE = ""
TARGET_FUNCTIONS = []


with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)


def init(benchmark_set_feature, target_functions):
    global API_KEY, BASE_URL, MODEL, TEMPERATURE, CLIENT
    global SOLVER_SRC_PATH, ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH, LOG_DIR_PATH
    global SYSTEM_PROMPT, USER_PROMPT
    global BENCHMARK_SET_FEATURE, TARGET_FUNCTIONS

    API_KEY = config["model"]["api_key"]
    BASE_URL = config["model"]["base_url"]
    MODEL = config["model"]["name"]
    TEMPERATURE = config["model"]["temperature"]

    SOLVER_SRC_PATH = config["route"]["solver_src"]
    ORIGIN_FILE_PATH = config["route"]["origin_file"]
    OPTIMIZED_FILE_PATH = config["route"]["optimized_file"]
    LOG_DIR_PATH = config["route"]["log"]

    SYSTEM_PROMPT = config["prompt"]["system"]
    USER_PROMPT = config["prompt"]["user"]

    TARGET_FUNCTIONS = target_functions
    BENCHMARK_SET_FEATURE = benchmark_set_feature

    CLIENT = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def set_system_prompt(chat_history: list):
    system_prompt = {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
    chat_history.insert(0, system_prompt)


def chat(message, chat_history):
    chat_history += [{"role": "user", "content": message}]
    response = CLIENT.chat.completions.create(
        model=MODEL,
        messages=chat_history,
        temperature=TEMPERATURE
    )
    chat_history += [{"role": "assistant", "content": response.choices[0].message.content}]

    return response.choices[0].message.content


def insert_function(optimized_file_name: str, response: str, func_name_to_replace: str):

    with open(optimized_file_name, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # 找到插入位置，并确定原函数的范围，判断逻辑是，从函数名开始，直到某一行以}开头，表明这个函数结束了
    insert_index = 0
    for i, line in enumerate(lines):
        if func_name_to_replace in line:
            insert_index = i
            break

    while lines[insert_index][0] != "}":
        del lines[insert_index]
    del lines[insert_index]

    response_lines = response.splitlines(keepends=True)
    for i, line in enumerate(response_lines):
        if func_name_to_replace in line:
            while response_lines[i][0] != "}":
                lines.insert(insert_index, response_lines[i])
                insert_index += 1
                i += 1
        break

    lines.insert(insert_index, "}\n")

    with open(optimized_file_name, "w", encoding="utf-8") as file:
        file.writelines(lines)


def optimize():
    # 初始化算法骨架
    with open(ORIGIN_FILE_PATH, "r", encoding="utf-8") as baseline_file:
        code = baseline_file.read()

    func_num = len(TARGET_FUNCTIONS)
    func_to_be_optimize_num = max(1, np.random.binomial(func_num, 1 / func_num))
    func_to_be_optimize = random.sample(TARGET_FUNCTIONS, func_to_be_optimize_num)

    # 开始问答
    chat_history = []
    set_system_prompt(chat_history)
    log_file_path = f"{LOG_DIR_PATH}/history_{int(time.time() * 1000)}.json"

    with open(ORIGIN_FILE_PATH, "r", encoding="utf-8") as baseline_file:
        code = baseline_file.read()
        target_funcs_str = "\n".join(func_to_be_optimize)
        rewrite_prompt = USER_PROMPT % (BENCHMARK_SET_FEATURE, target_funcs_str, code)
        res = chat(rewrite_prompt, chat_history)

        shutil.copyfile(ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH)
        for target_func in func_to_be_optimize:
            insert_function(OPTIMIZED_FILE_PATH, res, target_func)  # type: ignore

    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(json.dumps(chat_history, ensure_ascii=False, indent=4))
        logger.info(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "优化完成")


def main(benchmark_set_feature, target_functions):
    init(benchmark_set_feature, target_functions)
    optimize()


if __name__ == "__main__":
    
    benchmark_set_feature = ""
    target_functions = ["int USW::pick_var()"]

    main(benchmark_set_feature, target_functions)
