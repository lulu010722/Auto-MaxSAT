from openai import OpenAI
from pathlib import Path

import json
import time
import datetime
import shutil
import subprocess


# 模型交互信息
API_KEY = "sk-ce01122bd312429e83c9f2bd8640cc29"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# 目录信息
SRC_DIR = "source-code"
ITER_DIR_PATH = f"{SRC_DIR}/iterations"
LOG_DIR_PATH = f"{SRC_DIR}/log"
ORIGIN_FILE_PATH = f"{SRC_DIR}/heuristic_origin.h.txt"
OPTIMIZED_FILE_PATH = f"{SRC_DIR}/heuristic.h"
TARGET_FUNC = "int USW::pick_var()"
# # 轮询优化多个模块的多个函数
ORIGIN_FILES_PATH = []
OPTIMIZED_FILES_PATH = []
TARGET_FUNCS = []


# 主程序迭代运行信息
ITER_NUM = 2


# prompt信息
system_prompt = """
    You are a code generator, your goal is to generate a MaxSAT solver based on the given requirements and the code provided.
    You will be given a code snippet and you need to generate a complete code that meets the requirements.
    Note that the MaxSAT problem solver that we are going to optimize is targeted to solve unweighted MaxSAT problem without hard clauses.
"""
rewrite_prompt_template = f"""
    Your goal is to improve the MaxSAT solver by rewriting a selected function included in the <key code>, after reading and understanding the <key code> of MaxSAT solver below
    
    Steps:
    1. Read the <key code> and understand the functionality of the code.
    2. Rewrite the selected function code in the <key code> according to the requirements below.

    Requirements:
    1. Your rewritten function code must be different from original code, not just rewrite code synonymously
    2. Please make sure that the response text is a pure code response, without any explanation or comments
    3. You should not respond the code in markdown format, i.e. no leading and trailing ```.
    4. You should only output the rewritten function.
    
    This time, your goal is to optimize {TARGET_FUNC}.
    <key code> of MaxSAT solver is:
"""



def set_system_prompt(chat_history: list, prompt):
    system_prompt = {
        "role": "system",
        "content": prompt
    }
    chat_history.insert(0, system_prompt)


def chat(message, chat_history):
    chat_history += [{"role": "user", "content": message}]
    response_raw = client.chat.completions.create(
        model=MODEL,
        messages=chat_history
    )
    chat_history += [{"role": "assistant", "content": response_raw.choices[0].message.content}]

    return response_raw.choices[0].message.content


def insert_function(optimized_file_name: str, code: str, func_name_to_replace: str):
    formatted_code = subprocess.run(["clang-format"], input=code, capture_output=True, text=True).stdout

    with open(optimized_file_name, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # 找到插入位置，并确定原函数的范围，判断逻辑是，从函数名开始，直到某一行以}开头，表明这个函数结束了
    insert_index = 0
    for i, line in enumerate(lines):
        if func_name_to_replace in line:
            insert_index = i

    while lines[insert_index][0] != "}":
        del lines[insert_index]

    del lines[insert_index]

    for line in formatted_code.splitlines():
        lines.insert(insert_index, line + "\n")
        insert_index += 1

    with open(optimized_file_name, "w", encoding="utf-8") as file:
        file.writelines(lines)


def convert_last_version_to_cpp(file_name: str):
    shutil.copyfile(file_name, OPTIMIZED_FILE_PATH)


# 运行主程序
if __name__ == "__main__":

    # 清除iterations目录
    iter_dir = Path(ITER_DIR_PATH)
    for iter_file in iter_dir.iterdir():
        if iter_file.suffix == ".txt":
            iter_file.unlink()

    # 初始化算法骨架
    with open(ORIGIN_FILE_PATH, "r", encoding="utf-8") as baseline_file:
        code = baseline_file.read()
        with open(f"{ITER_DIR_PATH}/iteration_0.txt", "w", encoding="utf-8") as output_file:
            output_file.write(code)

    # 开始问答
    chat_history = []
    set_system_prompt(chat_history, system_prompt)
    log_file_name = f"{LOG_DIR_PATH}/history_{int(time.time() * 1000)}.json"
    max_score = 0.0


    for i in range(ITER_NUM):
        baseline_file_name = f"{ITER_DIR_PATH}/iteration_{i}.txt"
        optimized_file_name = f"{ITER_DIR_PATH}/iteration_{i + 1}.txt"
        with open(baseline_file_name, "r", encoding="utf-8") as baseline_file:
            code = baseline_file.read()
            rewrite_prompt = rewrite_prompt_template + code
            res = chat(rewrite_prompt, chat_history)

            shutil.copyfile(baseline_file_name, optimized_file_name)
            insert_function(optimized_file_name, res, TARGET_FUNC)
        convert_last_version_to_cpp(optimized_file_name)


    with open(log_file_name, "w", encoding="utf-8") as log_file:
        log_file.write(json.dumps(chat_history, ensure_ascii=False, indent=4))
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "优化完成")
