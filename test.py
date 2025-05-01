import subprocess
import os
import random
import pandas as pd


SHELL_SCRIPT = "starexec_usw-ls-runsolver.sh"
CUTOFF_TIME = 20  # 超过时间限制则结束当前实例的运算
INSTANCES_TO_RUN_NUM = 10  # 运行实例数量上限，运行到这个数量就停机
INSTANCE_SIZE_LIMIT = 1024 * 1024 * 100


all_costs = []
best_costs = []


def read_best_costs():
    df = pd.read_csv("2024_best_costs.csv")
    for _, row in df.iterrows():
        best_costs.append({
            "instance": row["instance"],
            "cost": row["best_cost"]
        })


def parse_starexec_output(output: str):
    """
    解析Starexec的输出结果
    :param output: Starexec的输出结果
    :return: None
    """
    lines = output.splitlines()
    current_best = -2
    for line in lines:
        if "c" in line:
            continue
        elif "o" in line:
            current_best = line.split(" ")[1]
        elif "s OPTIMUM FOUND" in line:
            pass
        elif "s UNSATISFIABLE" in line:
            pass
        elif "s UNKNOWN" in line:
            pass

    return current_best


def run_starexec():
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
        seed = random.randint(1, 1000000)
        print(f"Running USW-LS on {filepath}")
        # 较高概率出错的部分，使用try-except捕获异常
        try:
            output = subprocess.run(f"./{SHELL_SCRIPT} {filepath} {seed} {CUTOFF_TIME}", shell=True, capture_output=True, text=True)
            lines = output.stdout
            cost = parse_starexec_output(lines)
            all_costs.append({
                "instance": filename,
                "cost": cost
            })
        except Exception as e:
            print(f"Error running {filename}: {e}")

        runned_instances_cnt += 1
        if runned_instances_cnt >= INSTANCES_TO_RUN_NUM:
            print("达到运行实例数量上限，停机")
            return


def compare_with_best_costs():
    for my_cost in all_costs:
        for best_cost in best_costs:
            if my_cost["instance"] == best_cost["instance"]:
                print(f"Instance: {my_cost['instance']}, Cost: {my_cost['cost']}, Best Cost: {best_cost['cost']}")
                break
        else:
            print(f"Instance: {my_cost['instance']}, Cost: {my_cost['cost']}, Best Cost: Not Found")


def write_costs_to_csv():
    with open("2024_my_costs.csv", "w") as output_file:
        writer = pd.DataFrame(all_costs)
        writer.to_csv(output_file, index=False)
        print("输出结果已保存到output.csv")


if __name__ == "__main__":
    print("开始运行Starexec")
    run_starexec()
    read_best_costs()
    compare_with_best_costs()
    write_costs_to_csv()

