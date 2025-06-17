import subprocess
import os
import datetime
import sys



benchmark_sets = []
DESCRIPTION = "" if len(sys.argv) == 1 else sys.argv[1]

with open("concurrent/index", "r") as index_file:
    CONCURRENT_DIR_NUMBER = int(index_file.read().strip())

os.chdir(f"concurrent/concurrent_{CONCURRENT_DIR_NUMBER}_{DESCRIPTION}")


def get_benchmark_sets():
    for dirname in os.listdir("template/benchmark"):
        if os.path.isdir(os.path.join("template/benchmark", dirname)):
            benchmark_sets.append(dirname)


def main():
    get_benchmark_sets()
    processes = []
    benchmark_sets.sort(key=lambda x: x.lower())
    for index, benchmark_set in enumerate(benchmark_sets):
        # 暂时测试causal数据集，别的不管了
        if "causal" not in benchmark_set:
            continue
        print(f"进入测例集: {benchmark_set}")
        os.chdir(f"sub_{index}")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        command = f"nohup python3 -u single_evolve.py {benchmark_set} > output/concurrent_{timestamp}.ans 2>&1 &"
        p = subprocess.Popen(command, shell=True)
        processes.append(p)
        print(f"测例集结束: {benchmark_set}")
        os.chdir("..")

    for p in processes:
        p.wait()
    print("所有测例集处理完成")


if __name__ == "__main__":
    main()
