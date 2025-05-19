import os
import re
import sys
import json


RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
RESET = "\033[0m"



def extract_performance_over_cutoff_time():

    data = []
    for i in range(17):
        data.append([])

    for i in range(7):
        for j in range(17):
            for file in os.listdir(f"concurrent/concurrent_{i + 13}/sub_{j}/output"):
                if file.startswith("concurrent"):
                    with open(f"concurrent/concurrent_{i + 13}/sub_{j}/output/{file}", "r") as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.startswith("该算法最终得分"):
                                match = re.search(r"该算法最终得分：([0-9.]+)", line)
                                score = float(match.group(1))
                                data[j].append(score)
                                break
                    break

    with open("data", "w") as f:
        for i in range(17):
            for j in range(7):
                f.write(f"{data[i][j]} ")
            f.write("\n")


def extract_single_concurrent_result(index):

    data = []
    p1 = rf"concurrent/concurrent_{index}_.*?/sub_.*?/output/concurrent_.*?\.ans"

    for dirpath, dirnames, filenames in os.walk("concurrent"):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            result = re.findall(p1, filepath)
            if len(result) > 0:
                sub_data = {
                    "benchmark_set": "",
                    "data": []
                }
                with open(filepath, "r") as output_file:
                    lines = output_file.readlines()
                    for line in lines:
                        p2 = r"运行实例集合目录：benchmark/([a-zA-Z-]+)"
                        p3 = r"该算法最终得分：(\d+\.\d+|\d+)"
                        m2 = re.search(p2, line)
                        m3 = re.search(p3, line)
                        if m2:
                            sub_data["benchmark_set"] = m2.group(1)
                        if m3:
                            sub_data["data"].append(float(m3.group(1)))
                data.append(sub_data)
    data.sort(key=lambda x: x["benchmark_set"].lower())

    with open(f"data/scores_{index}.ans", "w") as output_file:
        output_file.write(f"第{index:>3}号并发测试的结果为：\n")
        for i, item in enumerate(data):
            benchmark_set = item["benchmark_set"]
            initial_score = item["data"][0]
            max_score = max(item["data"])

            output_file.write(f"第{i + 1:>3}个子集{BLUE}{benchmark_set:>12}{RESET}训练前：{YELLOW}{initial_score:>5.3f}{RESET}，最高分：{GREEN}{max_score:5.3f}{RESET}\n")

    return data


if __name__ == "__main__":
    index = int(sys.argv[1])
    data = extract_single_concurrent_result(index)

    print(json.dumps(data))
    

    # with open(f"test.ans", "w") as output_file:
    #     for i, item in enumerate(all_data):
    #         benchmark_set = item["benchmark_set"]
    #         initial_score = item["data"][0]
    #         max_score = max(item["data"])

    #         output_file.write(f"{BLUE}{benchmark_set:>12}{RESET} & {YELLOW}{initial_score:>5.3f}{RESET}&{GREEN}{max_score:5.3f}{RESET}\\\\\n")
    #         output_file.write("\\hline\n")