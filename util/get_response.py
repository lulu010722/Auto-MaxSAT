import os
import json
import shutil
import sys


if len(sys.argv) > 1:
    concurrent_set = sys.argv[1]
else:
    concurrent_set = sorted(os.listdir("concurrent"))[-1]


benchmark_sets = []
logs = dict()


for ans_file in os.listdir(f"concurrent/{concurrent_set}/_output"):
    ans_path = f"concurrent/{concurrent_set}/_output/{ans_file}"
    with open(ans_path, "r", encoding="utf-8") as f:
        data = f.read()
        benchmark_sets.append(ans_file.split(".")[0])
        logs[ans_file.split(".")[0]] = data


shutil.rmtree(f"response/{concurrent_set}", ignore_errors=True)
os.mkdir(f"response/{concurrent_set}")

for benchmark_set in benchmark_sets:
    shutil.rmtree(f"response/{concurrent_set}/{benchmark_set}", ignore_errors=True)
    os.mkdir(f"response/{concurrent_set}/{benchmark_set}")
    epoch = 1
    for json_file in sorted(os.listdir(f"concurrent/{concurrent_set}/{benchmark_set}/log")):
        if json_file.endswith(".json"):
            input_path = f"concurrent/{concurrent_set}/{benchmark_set}/log/{json_file}"
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 获取第三项
                item = data[2]["content"]
                # 反转义
                if isinstance(item, str):
                    item = bytes(item, "utf-8").decode("unicode_escape")
            if f"第{epoch}轮问询找到了更好的算法" in logs[benchmark_set]:
                output_path = f"response/{concurrent_set}/{benchmark_set}/{epoch}_progress.cpp"
            else:
                output_path = f"response/{concurrent_set}/{benchmark_set}/{epoch}.cpp"
            with open(output_path, "w", encoding="utf-8") as reponse_file:
                reponse_file.write(item)
            epoch += 1
