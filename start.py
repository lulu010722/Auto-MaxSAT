import subprocess
import os
import datetime
import sys



promising_sets = ["causal-dis", "railway-tr", "decision-t", "lisbon-wed", "synplicate"]
# promising_sets = ["causal-dis"]
benchmark_sets = []
dir = sys.argv[1]
os.chdir(dir)


def get_benchmark_sets():
    global benchmark_sets
    for dirname in os.listdir("template/benchmark_old"):
        if os.path.isdir(os.path.join("template/benchmark_old", dirname)):
            benchmark_sets.append(dirname)
    benchmark_sets = [benchmark_set for benchmark_set in benchmark_sets if benchmark_set in promising_sets]


def main():
    get_benchmark_sets()
    benchmark_sets.sort(key=lambda x: x.lower())
    os.mkdir("_output")
    for benchmark_set in benchmark_sets:
        os.chdir(benchmark_set)
        os.mkdir("log")
        command = f"nohup python3 -u auto_src/main.py {benchmark_set} > ../_output/{benchmark_set}.ans 2>&1 &"
        p = subprocess.Popen(command, shell=True)
        os.chdir("..")
        print(f"基准集: {benchmark_set} at {datetime.datetime.now()} 启动成功")


if __name__ == "__main__":
    main()
