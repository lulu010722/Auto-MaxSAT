import subprocess
import os
import random
import pandas as pd
import re

SHELL_SCRIPT = "starexec_usw-ls-runsolver.sh"

CUTOFF_TIME = 0
INSTANCE_NUM_LIMIT = 0
INSTANCE_SIZE_LIMIT = 0
BENCHMARK_SET_PATH = ""


# all_costs:
# [
#     {
#         "instance": "example1.wcnf",
#         "cost": 12345,
#         "best_cost": 123
#     } ...
# ]
all_costs = []
# best_costs:
# [
#     {
#         "instance": "example1.wcnf",
#         "best_cost": 123
#     } ...
# ]
best_costs = []


# 将2024_best_costs.csv中的数据读取到best_costs中
def read_best_costs():
    global best_costs
    best_costs = pd.read_csv("2024_best_costs.csv").to_dict(orient="records")

def parse_starexec_output(output: str) -> int:
    lines = output.splitlines()
    current_best = -2
    for line in lines:
        pattern = r"\bo [1-9][0-9]*\b"
        matches = re.findall(pattern, line)
        if len(matches) > 0:
            current_best = int(matches[0][2:])

    return current_best


# 有实例数量和文件大小的限制
# def run_starexec_with_all_benchmark_set():
#     runned_instances_cnt = 0

#     all_wcnf_files_path = []
#     for dirpath, _, filenames in os.walk("benchmark/mse24-anytime-weighted-old-format"):
#         for filename in filenames:
#             if filename.endswith(".wcnf"):
#                 filepath = os.path.join(dirpath, filename)

#                 # 这里可以添加一些条件来过滤文件，例如文件大小、文件名等
#                 if os.path.getsize(filepath) > INSTANCE_SIZE_LIMIT:
#                     continue
#                 all_wcnf_files_path.append(filepath)

#     # 打乱文件顺序
#     random.shuffle(all_wcnf_files_path)

#     for filepath in all_wcnf_files_path:
#         filename = os.path.basename(filepath)
#         seed = random.randint(1, 1000000)
#         print(f"Running USW-LS on {filepath}")
#         # 较高概率出错的部分，使用try-except捕获异常
#         try:
#             output = subprocess.run(f"./{SHELL_SCRIPT} {filepath} {seed} {CUTOFF_TIME}", shell=True, capture_output=True, text=True).stdout
#             cost = parse_starexec_output(output)
#             all_costs.append({
#                 "instance": filename,
#                 "cost": cost,
#                 "best_cost": -1
#             })
#         except Exception as e:
#             print(f"Error running {filename}: {e}")

#         runned_instances_cnt += 1
#         if runned_instances_cnt >= INSTANCE_NUM_LIMIT:
#             print("达到运行实例数量上限，停机")
#             return


def run_starexec_with_benchmark_set():
    global all_costs

    runned_instaces_cnt = 0

    all_wcnf_files_path = [os.path.join(BENCHMARK_SET_PATH, filename) for filename in os.listdir(BENCHMARK_SET_PATH)]
    all_wcnf_files_path = [filepath for filepath in all_wcnf_files_path if os.path.getsize(filepath) <= INSTANCE_SIZE_LIMIT]

    # 这一步是因为在父级脚本中，改脚本在未销毁的情况下会多次运行，所以all_costs会有上次残留的信息
    # 后面因为有将这个变量写入csv文件的操作，所以需要清空
    all_costs = []
    for filepath in all_wcnf_files_path:
        filename = os.path.basename(filepath)
        seed = random.randint(1, 1000000)
        print(f"Running USW-LS on {filepath}")
        # 较高概率出错的部分，使用try-except捕获异常
        try:
            output = subprocess.run(f"./{SHELL_SCRIPT} {filepath} {seed} {CUTOFF_TIME}", shell=True, capture_output=True, text=True).stdout
            cost = parse_starexec_output(output)
            all_costs.append({
                "instance": filename,
                "cost": cost,
                "best_cost": -1
            })
        except Exception as e:
            print(f"Error running {filename}: {e}")

        runned_instaces_cnt += 1
        if runned_instaces_cnt >= INSTANCE_NUM_LIMIT:
            print("达到运行实例数量上限，停机")
            return


def compare_with_best_costs():
    global best_costs
    for cost_item in all_costs:
        for best_cost_item in best_costs:
            if cost_item["instance"] == best_cost_item["instance"]:
                cost_item["best_cost"] = best_cost_item["best_cost"]
                break
        else:
            print(f"实例{cost_item['instance']}的最佳cost没找到")


def write_costs_to_csv():
    df = pd.DataFrame(all_costs)
    df.to_csv("2024_my_costs.csv", index=False)
    print("输出结果已保存到2024_my_costs.csv")


def rate():
    tota_score = 0
    valid_instance_cnt = 0
    for item in all_costs:
        if item["cost"] < 0:
            print(f"实例{item['instance']}的my_cost没找到")
            continue
        if item["best_cost"] < 0:
            print(f"实例{item['instance']}的best_cost没找到")
            continue

        score = (1 + item['best_cost']) / (1 + item['cost'])
        tota_score += score
        valid_instance_cnt += 1

    return tota_score / valid_instance_cnt if valid_instance_cnt > 0 else 0


# 通过import执行子模块
def main(cutoff_time: int, instance_num_limit: int, instance_size_limit: int, benchmark_set_path: str):
    global CUTOFF_TIME
    global INSTANCE_NUM_LIMIT
    global INSTANCE_SIZE_LIMIT
    global BENCHMARK_SET_PATH
    CUTOFF_TIME = cutoff_time
    INSTANCE_NUM_LIMIT = instance_num_limit
    INSTANCE_SIZE_LIMIT = instance_size_limit
    BENCHMARK_SET_PATH = benchmark_set_path

    print("开始运行Starexec")
    print(f"运行实例时间上限：{CUTOFF_TIME} 秒")
    print(f"运行实例数量上限：{INSTANCE_NUM_LIMIT} 个")
    print(f"运行实例大小上限：{INSTANCE_SIZE_LIMIT // (1024 * 1024)} MB")
    print(f"运行实例集合目录：{BENCHMARK_SET_PATH}")

    # run_starexec_with_all_benchmark_set()
    run_starexec_with_benchmark_set()

    read_best_costs()
    compare_with_best_costs()
    write_costs_to_csv()

    score = rate()
    print(f"该算法最终得分：{score}")
    with open("temp", "w") as temp_file:
        temp_file.write(str(score))
