from openai import OpenAI
from pathlib import Path

import json
import time
import datetime
import shutil


# 模型交互信息
# API_KEY = "sk-ce01122bd312429e83c9f2bd8640cc29" # deepseek
API_KEY = "sk-DCexuFsJNJS1A7DpAa8a29800e2e4488A2A016F6D6B34f99" # proxy
BASE_URL = "https://api.132999.xyz/v1"
MODELS = [
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4-32k",
    "gpt-4-turbo",
    "o1",
    "o1-mini",
    "gemini-pro"
]
MODEL = MODELS[5]
CLIENT = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# 可变全局变量
SRC_DIR = ""
ORIGIN_FILE_PATH = ""
OPTIMIZED_FILE_PATH = ""
TARGET_FUNC = ""
ITER_NUM = 0

ITER_DIR_PATH = ""
LOG_DIR_PATH = ""


# prompt信息
system_prompt = """
    You are a code generator, your goal is to generate a MaxSAT solver based on the given requirements and the code provided.
    You will be given a code snippet and you need to generate a complete code that meets the requirements.
    Note that the MaxSAT problem solver that we are going to optimize is targeted to solve unweighted MaxSAT problem without hard clauses.
"""
rewrite_prompt_template = """
    Your goal is to improve the MaxSAT solver by rewriting a selected function included in the <key code>, after reading and understanding the <key code> of MaxSAT solver below
    
    Steps:
    1. Read the <key code> and understand the functionality of the code.
    2. Rewrite the code with the given function name in the <key code> according to the requirements below.

    Requirements:
    1. Your rewritten function code must be different from original code, not just rewrite code synonymously.
    2. Please make sure that the response text is a pure code response, without any explanation or comments.
    3. You should not respond the code in markdown format, i.e. no leading and trailing ```, just use plain text.
    
    This time, your goal is to optimize %s.
    <key code> of MaxSAT solver is:
    %s
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
        messages=chat_history
    )
    chat_history += [{"role": "assistant", "content": response_raw.choices[0].message.content}]

    return response_raw.choices[0].message.content


def insert_function(optimized_file_name: str, code: str, func_name_to_replace: str):
    # formatted_code = subprocess.run(["clang-format"], input=code, capture_output=True, text=True).stdout

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

    for line in code.splitlines():
        lines.insert(insert_index, line + "\n")
        insert_index += 1

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
    log_file_name = f"{LOG_DIR_PATH}/history_{int(time.time() * 1000)}.json"

    for i in range(ITER_NUM):
        baseline_file_name = f"{ITER_DIR_PATH}/iteration_{i}.txt"
        optimized_file_name = f"{ITER_DIR_PATH}/iteration_{i + 1}.txt"
        with open(baseline_file_name, "r", encoding="utf-8") as baseline_file:
            code = baseline_file.read()
            rewrite_prompt = rewrite_prompt_template % (TARGET_FUNC, code)
            res = chat(rewrite_prompt, chat_history)

            shutil.copyfile(baseline_file_name, optimized_file_name)
            insert_function(optimized_file_name, res, TARGET_FUNC)
        convert_last_version_to_cpp(optimized_file_name)

    with open(log_file_name, "w", encoding="utf-8") as log_file:
        log_file.write(json.dumps(chat_history, ensure_ascii=False, indent=4))
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "优化完成")


# TODO 支持优化来自多个文件的多个函数
def optimize_multiple():
    pass


# 通过import的方式执行子模块
def main(src_dir, origin_file_path, optimized_file_path, target_func, iter_num):
    global SRC_DIR
    global ORIGIN_FILE_PATH
    global OPTIMIZED_FILE_PATH
    global TARGET_FUNC
    global ITER_NUM
    global ITER_DIR_PATH
    global LOG_DIR_PATH

    SRC_DIR = src_dir
    ORIGIN_FILE_PATH = origin_file_path
    OPTIMIZED_FILE_PATH = optimized_file_path
    TARGET_FUNC = target_func
    ITER_NUM = iter_num

    ITER_DIR_PATH = f"{SRC_DIR}/iterations"
    LOG_DIR_PATH = f"{SRC_DIR}/log"

    Path(ITER_DIR_PATH).mkdir(parents=True, exist_ok=True)
    Path(LOG_DIR_PATH).mkdir(parents=True, exist_ok=True)

    optimize_one_at_a_time()


if __name__ == "__main__":
    pass