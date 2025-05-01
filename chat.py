from openai import OpenAI
from pathlib import Path

import json
import time
import datetime
import shutil
import subprocess
import sys


# 模型交互信息
API_KEY = "sk-ce01122bd312429e83c9f2bd8640cc29"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

try:
    # 需要接受外部传入的程序参数的全局变量
    SRC_DIR = sys.argv[1]
    # 优化单个文件中的单个函数
    ORIGIN_FILE_PATH = sys.argv[2]
    OPTIMIZED_FILE_PATH = sys.argv[3]
    TARGET_FUNC = sys.argv[4]
    # 主程序迭代运行信息
    ITER_NUM = int(sys.argv[5])
except Exception as e:
    print(f"Error: {e}")
    print("Usage: python chat.py <SRC_DIR> <ORIGIN_FILE_PATH> <OPTIMIZED_FILE_PATH> <TARGET_FUNC> <ITER_NUM>")
    sys.exit(1)

ITER_DIR_PATH = f"{SRC_DIR}/iterations"
LOG_DIR_PATH = f"{SRC_DIR}/log"


# TODO 轮询优化多个模块的多个函数
# ORIGIN_FILES_PATH = []
# OPTIMIZED_FILES_PATH = []
# TARGET_FUNCS = []


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
            rewrite_prompt = rewrite_prompt_template + code
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


if __name__ == "__main__":
    optimize_one_at_a_time()