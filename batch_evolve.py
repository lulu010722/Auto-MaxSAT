import single_evolve as single

import time
import os

BLUE = "\033[1;34m"
RESET = "\033[0m"


def print_blue(message):
    print(f"{BLUE}{message}{RESET}")


def main():
    benchmark_sets = os.listdir("benchmark/mse24-anytime-weighted-old-format")
    benchmark_sets.sort()
    for benchmark_set in benchmark_sets:
        print_blue(f"开始进化测试集{benchmark_set}")
        single.main(benchmark_set)
        print_blue(f"进化完成{benchmark_set}")
        print()
        time.sleep(0.5)

main()