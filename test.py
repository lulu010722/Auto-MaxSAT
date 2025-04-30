import subprocess
import os
import random


SHELL_SCRIPT = "starexec_usw-ls-runsolver.sh"
CUTOFF_TIME = 60  # 超过时间限制则结束当前实例的运算
INSTANCES_TO_RUN_NUM = 20  # 运行实例数量上限，运行到这个数量就停机


all_costs = []


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
    for dirpath, dirnames, filenames in os.walk("benchmark"):
        for filename in filenames:
            if filename.endswith(".wcnf"):
                filepath = os.path.join(dirpath, filename)
                print(f"Running Starexec on {filepath}")
                seed = random.randint(1, 1000000)
                output = subprocess.run(f"./{SHELL_SCRIPT} {filepath} {seed} {CUTOFF_TIME}", shell=True, capture_output=True, text=True)
                lines = output.stdout

                cost = parse_starexec_output(lines)

                all_costs.append(cost)

                runned_instances_cnt += 1
                if runned_instances_cnt > INSTANCES_TO_RUN_NUM:
                    print("达到运行实例数量上限，停机")
                    return
                

if __name__ == "__main__":
    run_starexec()
    print(all_costs)