import single_evolve as single

import time
import os
import shutil

BLUE = "\033[1;34m"
RESET = "\033[0m"


def print_blue(message):
    print(f"{BLUE}{message}{RESET}")


def init():
    with open("best_scores.csv", "w") as f:
        f.write("benchmark_set,best_score\n")
    with open("2024_my_costs.csv", "w") as f:
        pass

    shutil.rmtree("source-code/iterations", ignore_errors=True)
    shutil.rmtree("source-code/log", ignore_errors=True)
    shutil.rmtree("progress", ignore_errors=True)

    os.mkdir("source-code/iterations")
    os.mkdir("source-code/log")
    os.mkdir("progress")


def reset_origin_file():
    shutil.copyfile("source-code/backup/heuristic.h.origin", "source-code/heuristic.h")


def main():

    init()
    benchmark_sets = os.listdir("benchmark/mse24-anytime-weighted-old-format")
    benchmark_sets.sort()
    for benchmark_set in benchmark_sets:
        if benchmark_set == "other":
            continue
        print_blue(f"开始进化测试集{benchmark_set}")
        single.main(benchmark_set)
        print_blue(f"进化完成{benchmark_set}")
        print()
        
        reset_origin_file()
        time.sleep(0.5)


main()
