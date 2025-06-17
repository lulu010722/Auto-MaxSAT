from openai import OpenAI
from pathlib import Path

import json
import time
import datetime
import shutil
import numpy as np
import random
import yaml


API_KEY = ""
BASE_URL = ""
MODEL = ""
TEMPERATURE = 0.0

SOLVER_SRC_PATH = ""
ORIGIN_FILE_PATH = ""
OPTIMIZED_FILE_PATH = ""
LOG_DIR_PATH = ""

BENCHMARK_SET_FEATURE = ""
TARGET_FUNCTION = ""
TARGET_FUNCTIONS = []




with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)



def init_params(benchmark_set_feature, target_function, target_functions):
    global API_KEY, BASE_URL, MODEL, TEMPERATURE, CLIENT
    global SOLVER_SRC_PATH, ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH, LOG_DIR_PATH
    global BENCHMARK_SET_FEATURE, TARGET_FUNCTION, TARGET_FUNCTIONS
    
    API_KEY = config["model"]["api_key"]
    BASE_URL = config["model"]["base_url"]
    MODEL = config["model"]["name"]
    TEMPERATURE = config["model"]["temperature"]

    SOLVER_SRC_PATH = config["route"]["solver_src"]
    ORIGIN_FILE_PATH = config["route"]["origin_file"]
    OPTIMIZED_FILE_PATH = config["route"]["optimized_file"]
    LOG_DIR_PATH = config["route"]["log"]

    TARGET_FUNCTION = target_function
    TARGET_FUNCTIONS = target_functions
    BENCHMARK_SET_FEATURE = benchmark_set_feature

    CLIENT = OpenAI(api_key=API_KEY, base_url=BASE_URL)



def set_system_prompt(chat_history: list):
    system_prompt = {
        "role": "system",
        "content": prompt
    }
    chat_history.insert(0, system_prompt)


def chat(message, chat_history):
    chat_history += [{"role": "user", "content": message}]
    response_raw = CLIENT.chat.completions.create(
        model=MODEL,
        messages=chat_history,
        temperature=TEMPERATURE
    )
    chat_history += [{"role": "assistant", "content": response_raw.choices[0].message.content}]

    return response_raw.choices[0].message.content


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


def convert_last_version_to_cpp(file_name: str):
    shutil.copyfile(file_name, OPTIMIZED_FILE_PATH)



# 集中优化一个函数
def optimize_one_at_a_time():

    # 初始化算法骨架
    with open(ORIGIN_FILE_PATH, "r", encoding="utf-8") as baseline_file:
        code = baseline_file.read()

    # 开始问答
    chat_history = []
    set_system_prompt(chat_history, system_prompt)
    log_file_path = f"{LOG_DIR_PATH}/history_{int(time.time() * 1000)}.json"

    with open(baseline_file_name, "r", encoding="utf-8") as baseline_file:
        code = baseline_file.read()
        rewrite_prompt = rewrite_prompt_template % (BENCHMARK_SET_FEATURE, TARGET_FUNCTION, code)
        res = chat(rewrite_prompt, chat_history)

        shutil.copyfile(baseline_file_name, optimized_file_name)
        insert_function(optimized_file_name, res, TARGET_FUNCTION) # type: ignore
    convert_last_version_to_cpp(optimized_file_name)

    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(json.dumps(chat_history, ensure_ascii=False, indent=4))
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "优化完成")


# TODO 支持优化来自多个文件的多个函数
def optimize_multiple():
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

    baseline_file_name = f"{ITER_DIR_PATH}/iteration_0.txt"
    optimized_file_name = f"{ITER_DIR_PATH}/iteration_1.txt"
    with open(baseline_file_name, "r", encoding="utf-8") as baseline_file:
        code = baseline_file.read()
        target_funcs_str = "\n".join(func_to_be_optimize)
        rewrite_prompt = rewrite_prompt_template % (BENCHMARK_SET_FEATURE, target_funcs_str, code)
        res = chat(rewrite_prompt, chat_history)

        shutil.copyfile(baseline_file_name, optimized_file_name)
        for target_func in func_to_be_optimize:
            insert_function(optimized_file_name, res, target_func) # type: ignore
    convert_last_version_to_cpp(optimized_file_name)

    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(json.dumps(chat_history, ensure_ascii=False, indent=4))
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "优化完成")



# 通过import的方式执行子模块
def main(benchmark_set_feature, target_func, target_funcs):

    init_params(benchmark_set_feature, target_func, target_funcs)

    Path(LOG_DIR_PATH).mkdir(parents=True, exist_ok=True)

    # optimize_one_at_a_time()
    optimize_multiple()


if __name__ == "__main__":
    solver_src = "solver-src"
    # 与chat相关的配置
    ORIGIN_FILE_PATH = f"{solver_src}/backup/heuristic.h.origin"
    OPTIMIZED_FILE_PATH = f"{solver_src}/heuristic.h"
    TARGET_FUNCTIONS = [
        "int USW::pick_var()",
        "void USW::hard_increase_weights()",
        "void USW::soft_increase_weights_partial()",
        "void USW::soft_increase_weights_not_partial()",
        "void USW::hard_smooth_weights()",
        "void USW::soft_smooth_weights()",
    ]

    main(solver_src, "", ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH, TARGET_FUNCTIONS[0], TARGET_FUNCTIONS)
