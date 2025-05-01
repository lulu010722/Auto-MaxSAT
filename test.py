import subprocess
import os
import random
import sys
import pandas as pd
import json


SHELL_SCRIPT = "starexec_usw-ls-runsolver.sh"
try:
    CUTOFF_TIME = int(sys.argv[1])  # 超过时间限制则结束当前实例的运算，单位是秒
    INSTANCE_NUM_LIMIT = int(sys.argv[2])  # 运行实例数量上限，运行到这个数量就停机
    INSTANCE_SIZE_LIMIT = int(sys.argv[3])  # 超过这个大小的就不计算了，因为WSL会爆炸！单位是字节
    BENCHMARK_SET_PATH = sys.argv[4]  # 细分测试集
except Exception as e:
    print(f"Error: {e}")
    print("Usage: python test.py <CUTOFF_TIME> <INSTANCE_NUM_LIMIT> <INSTANCE_SIZE_LIMIT> <BENCHMARK_SET_PATH>")
    sys.exit(1)


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
#         "cost": 123
#     } ...
# ]
best_costs = []


# 将2024_best_costs.csv中的数据读取到best_costs中
def read_best_costs():
    df = pd.read_csv("2024_best_costs.csv")
    for _, row in df.iterrows():
        best_costs.append({
            "instance": row["instance"],
            "cost": row["best_cost"]
        })


def parse_starexec_output(output: str) -> int:
    lines = output.splitlines()
    current_best = -2
    for line in lines:
        if "c" in line:
            continue
        elif "o" in line:
            current_best = int(line.split(" ")[1])
        elif "s OPTIMUM FOUND" in line:
            pass
        elif "s UNSATISFIABLE" in line:
            pass
        elif "s UNKNOWN" in line:
            pass

    return current_best



# 有实例数量和文件大小的限制
def run_starexec_with_all_benchmark_set():
    runned_instances_cnt = 0

    all_wcnf_files_path = []
    for dirpath, _, filenames in os.walk("benchmark/mse24-anytime-weighted-old-format"):
        for filename in filenames:
            if filename.endswith(".wcnf"):
                filepath = os.path.join(dirpath, filename)

                # 这里可以添加一些条件来过滤文件，例如文件大小、文件名等
                if os.path.getsize(filepath) > INSTANCE_SIZE_LIMIT:
                    continue
                all_wcnf_files_path.append(filepath)

    # 打乱文件顺序
    random.shuffle(all_wcnf_files_path)

    for filepath in all_wcnf_files_path:
        filename = os.path.basename(filepath)
        seed = random.randint(1, 1000000)
        print(f"Running USW-LS on {filepath}")
        # 较高概率出错的部分，使用try-except捕获异常
        try:
            output = subprocess.run(f"./{SHELL_SCRIPT} {filepath} {seed} {CUTOFF_TIME}", shell=True, capture_output=True, text=True)
            lines = output.stdout
            cost = parse_starexec_output(lines)
            all_costs.append({
                "instance": filename,
                "cost": cost,
                "best_cost": -1
            })
        except Exception as e:
            print(f"Error running {filename}: {e}")

        runned_instances_cnt += 1
        if runned_instances_cnt >= INSTANCE_NUM_LIMIT:
            print("达到运行实例数量上限，停机")
            return



# 仍有文件大小上限限制，但无数量限制
def run_starexec_with_benchmark_set(benchmark_set_path = BENCHMARK_SET_PATH):

    all_wcnf_files_path = [os.path.join(benchmark_set_path, filename) for filename in os.listdir(benchmark_set_path)]
    all_wcnf_files_path = [filepath for filepath in all_wcnf_files_path if os.path.getsize(filepath) <= INSTANCE_SIZE_LIMIT]
    
    for filepath in all_wcnf_files_path:
        filename = os.path.basename(filepath)
        seed = random.randint(1, 1000000)
        print(f"Running USW-LS on {filepath}")
        # 较高概率出错的部分，使用try-except捕获异常
        try:
            output = subprocess.run(f"./{SHELL_SCRIPT} {filepath} {seed} {CUTOFF_TIME}", shell=True, capture_output=True, text=True)
            lines = output.stdout
            cost = parse_starexec_output(lines)
            all_costs.append({
                "instance": filename,
                "cost": cost,
                "best_cost": -1
            })
        except Exception as e:
            print(f"Error running {filename}: {e}")



def compare_with_best_costs():
    for cost in all_costs:
        for best_cost in best_costs:
            if cost["instance"] == best_cost["instance"]:
                cost["best_cost"] = best_cost["cost"]
                break
        else:
            print(f"实例{cost['instance']}的最佳cost没找到")


def write_costs_to_csv():
    with open("2024_my_costs.csv", "w") as output_file:
        writer = pd.DataFrame(all_costs)
        writer.to_csv(output_file, index=False)
        print("输出结果已保存到2024_my_costs.csv")


def rate():
    tota_score = 0
    valid_instance_cnt = 0
    for cost in all_costs:
        if cost["best_cost"] == -1:
            print(f"实例{cost['instance']}的best_cost没找到")
            continue
        elif cost["cost"] < 0:
            print(f"实例{cost['instance']}的my_cost没找到")
            continue
        else:
            score = (1 + cost['best_cost']) / (1 + cost['cost'])
            tota_score += score
            valid_instance_cnt += 1

    return tota_score / valid_instance_cnt if valid_instance_cnt > 0 else 0


if __name__ == "__main__":
    print("开始运行Starexec")
    print(f"运行实例时间上限：{CUTOFF_TIME}秒")
    print(f"运行实例数量上限：{INSTANCE_NUM_LIMIT}个")
    print(f"运行实例大小上限：{INSTANCE_SIZE_LIMIT}B")
    print(f"运行实例集合目录：{BENCHMARK_SET_PATH}")
    
    # run_starexec_with_all_benchmark_set()
    run_starexec_with_benchmark_set()

    read_best_costs()
    compare_with_best_costs()
    write_costs_to_csv()

    current_score = rate()
    print(f"该算法最终得分：{current_score}")
    with open("best_scores.json", "r") as json_file:
        best_scores = json.load(json_file)
        for item in best_scores:
            path, best_score = item["benchmark_set_path"], item["best_score"]
            if os.path.basename(path) == BENCHMARK_SET_PATH and current_score > best_score:
                pass
