import subprocess
import os
import datetime
import sys



benchmark_sets = []
dir = sys.argv[1]
os.chdir(dir)


def get_benchmark_sets():
    for dirname in os.listdir("template/benchmark_old"):
        if os.path.isdir(os.path.join("template/benchmark_old", dirname)):
            benchmark_sets.append(dirname)


def main():
    get_benchmark_sets()
    processes = []
    benchmark_sets.sort(key=lambda x: x.lower())
    os.mkdir("_output")
    for benchmark_set in benchmark_sets:
        os.chdir(benchmark_set)
        os.mkdir("log")
        command = f"nohup python3 -u auto_src/main.py {benchmark_set} > ../_output/{benchmark_set}.ans 2>&1 &"
        p = subprocess.Popen(command, shell=True)
        processes.append(p)
        os.chdir("..")

    for p in processes:
        p.wait()
    print("所有测例集处理完成")


if __name__ == "__main__":
    main()
