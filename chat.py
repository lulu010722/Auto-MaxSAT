from openai import OpenAI
from pathlib import Path

import json
import time
import datetime
import shutil
import numpy as np
import random


# 模型交互信息
# 自己的API_KEY
# API_KEY = "sk-ce01122bd312429e83c9f2bd8640cc29" # deepseek
# BASE_URL = "https://api.deepseek.com"
# MODEL = "deepseek-chat"
# MODEL = "deepseek-reasoner"

API_KEY = "sk-ca13676a17cc4ee0a4e7bce47e6ce643" # qwen
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-max"

# 实验室的API_KEY
# API_KEY = "sk-DCexuFsJNJS1A7DpAa8a29800e2e4488A2A016F6D6B34f99" # proxy
# BASE_URL = "https://api.132999.xyz/v1"
# MODELS = {
#     "1": "deepseek-v3",
#     "2": "claude-3-5-sonnet-all",
#     "3": "gpt-3.5-turbo",
#     "4": "gpt-4-32k",
#     "5": "gpt-4-turbo",
#     "6": "o1",
#     "7": "o1-mini",
#     "8": "gemini-pro",
#     "9": "deepseek-r1"
# }
# MODEL = MODELS["4"]

TEMPERATURE = 0.0
CLIENT = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# 可变全局变量
SRC_DIR = ""
BENCHMARK_SET_FEATURE = ""
ORIGIN_FILE_PATH = ""
OPTIMIZED_FILE_PATH = ""
TARGET_FUNC = ""
TARGET_FUNCS = []

ITER_DIR_PATH = ""
LOG_DIR_PATH = ""


# prompt信息
system_prompt = """
You are a code generator, your goal is to generate a MaxSAT solver based on the given requirements and the code provided.
You will be given a complete code module and you need to rewrite selected parts that meets the requirements.
Note that the MaxSAT problem solver that we are going to optimize is targeted to solve weighted partial MaxSAT problem,
which is a variant of the MaxSAT problem where each clause has a weight and therea are two types of clauses: hard clauses and soft clauses.
"""
rewrite_prompt_template = """
Your goal is to improve the MaxSAT solver by rewriting a selected function included in the <key code>, after reading and understanding the <key code> of MaxSAT solver below

Steps:
1. Read the <key code> and understand the functionality of the code.
2. Rewrite the code with the given function name in the <key code> according to the requirements below.

Requirements:
1. Your rewritten function code must be different from original code, not just rewrite code synonymously.
2. Please make sure that the response text is a pure code response, without any explanation or comments.
3. You are not allowed to use data structures that is not defined or included in the <key code>.
4. You should not respond the code in markdown format, i.e. no leading and trailing ```, just use plain text.
5. You maybe required to optimized multiple functions. In this case, rewrite each function and give output in order, separated by 2 new lines.


We provide you with the feature of the benchmark set that we are going to use to test the performance of the solver.
You can use this feature to optimize the code.
The feature is as follows (ended with a mark ---):
%s
---
Explanation of the benchmark set feature by an example:
 Standard MaxSat Instance
{
 "sha1sum": "929379226355ee19e327a2ee481f00cbbcefe410", # the hash value of the instance
 "nvars": 40290, # number of variables
 "ncls": 145910, # number of clauses
 "total_lits": 355550, # number of literals
 "nhards": 145238, # number of har clauses
 "nhard_nlits": 354878, # number of literals in hard clauses
 "nhard_len_stats": # some statistics of the length of hard clauses
    { "min": 1, # minimum length
      "max": 6, # maximum length
      "ave": 2.4434, # average length
      "stddev": 0.9066 }, # standard deviation of length
 "nsofts": 672, # number of soft clauses
 "nsoft_nlits": 672, # number of literals in soft clauses
 "nsoft_len_stats": # some statistics of the length of soft clauses
    { "min": 1, # minimum length
      "max": 1, # maximum length
      "ave": 1.0000, # average length
      "stddev": 0.0000 }, # standard deviation of length
 "nsoft_wts": 667, # number of weights of soft clauses
 "soft_wt_stats": # some statistics of the weights of soft clauses
    { "min": 22, # minimum weight
      "max": 49600, # maximum weight
      "ave": 17352.1726, # average weight
      "stddev": 10300.9184 } # standard deviation of weight
}


This time, the function(s) you need to optimize is:
%s


<key code> of MaxSAT solver is (ended with a mark ---):
%s
---

For example, your respones should look like:

int <scope>::<function_A_name>()
{
    ...
}


void <scope>::<function_B_name>()
{
    ...
}

"""


def set_system_prompt(chat_history: list, prompt):
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
    # formatted_code = subprocess.run(["clang-format"], input=code, capture_output=True, text=True).stdout

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


def clear_iterations_dir():
    # 清除iterations目录
    iter_dir = Path(ITER_DIR_PATH)
    for iter_file in iter_dir.iterdir():
        if iter_file.suffix == ".txt":
            iter_file.unlink()


# 集中优化一个函数
def optimize_one_at_a_time():
    clear_iterations_dir()

    # 初始化算法骨架
    with open(ORIGIN_FILE_PATH, "r", encoding="utf-8") as baseline_file:
        code = baseline_file.read()
        with open(f"{ITER_DIR_PATH}/iteration_0.txt", "w", encoding="utf-8") as output_file:
            output_file.write(code)

    # 开始问答
    chat_history = []
    set_system_prompt(chat_history, system_prompt)
    log_file_path = f"{LOG_DIR_PATH}/history_{int(time.time() * 1000)}.json"

    baseline_file_name = f"{ITER_DIR_PATH}/iteration_0.txt"
    optimized_file_name = f"{ITER_DIR_PATH}/iteration_1.txt"
    with open(baseline_file_name, "r", encoding="utf-8") as baseline_file:
        code = baseline_file.read()
        rewrite_prompt = rewrite_prompt_template % (BENCHMARK_SET_FEATURE, TARGET_FUNC, code)
        res = chat(rewrite_prompt, chat_history)

        shutil.copyfile(baseline_file_name, optimized_file_name)
        insert_function(optimized_file_name, res, TARGET_FUNC)
    convert_last_version_to_cpp(optimized_file_name)

    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(json.dumps(chat_history, ensure_ascii=False, indent=4))
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "优化完成")


# TODO 支持优化来自多个文件的多个函数
def optimize_multiple():
    clear_iterations_dir()
    # 初始化算法骨架
    with open(ORIGIN_FILE_PATH, "r", encoding="utf-8") as baseline_file:
        code = baseline_file.read()
        with open(f"{ITER_DIR_PATH}/iteration_0.txt", "w", encoding="utf-8") as output_file:
            output_file.write(code)
    func_num = len(TARGET_FUNCS)
    func_to_be_optimize_num = max(1, np.random.binomial(func_num, 1 / func_num))
    func_to_be_optimize = random.sample(TARGET_FUNCS, func_to_be_optimize_num)
    
    # 开始问答
    chat_history = []
    set_system_prompt(chat_history, system_prompt)
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
            insert_function(optimized_file_name, res, target_func)
    convert_last_version_to_cpp(optimized_file_name)

    with open(log_file_path, "w", encoding="utf-8") as log_file:
        log_file.write(json.dumps(chat_history, ensure_ascii=False, indent=4))
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "优化完成")



# 通过import的方式执行子模块
def main(src_dir, benchmark_set_feature, origin_file_path, optimized_file_path, target_func, target_funcs):
    global SRC_DIR
    global BENCHMARK_SET_FEATURE
    global ORIGIN_FILE_PATH
    global OPTIMIZED_FILE_PATH
    global TARGET_FUNC
    global TARGET_FUNCS
    global ITER_DIR_PATH
    global LOG_DIR_PATH

    SRC_DIR = src_dir
    BENCHMARK_SET_FEATURE = benchmark_set_feature
    ORIGIN_FILE_PATH = origin_file_path
    OPTIMIZED_FILE_PATH = optimized_file_path
    TARGET_FUNC = target_func
    TARGET_FUNCS = target_funcs

    ITER_DIR_PATH = f"{SRC_DIR}/iterations"
    LOG_DIR_PATH = f"{SRC_DIR}/log"

    Path(ITER_DIR_PATH).mkdir(parents=True, exist_ok=True)
    Path(LOG_DIR_PATH).mkdir(parents=True, exist_ok=True)

    # optimize_one_at_a_time()
    optimize_multiple()


if __name__ == "__main__":
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

    main(src_dir, "", ORIGIN_FILE_PATH, OPTIMIZED_FILE_PATH, TARGET_FUNCS[0], TARGET_FUNCS)
