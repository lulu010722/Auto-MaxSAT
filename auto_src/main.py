from pathlib import Path
from multiprocessing import Process, Lock
from datetime import datetime

import logging
import yaml
import shutil
import os

import single


lock = Lock()

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("output/main.log")
formatter = logging.Formatter('[%(asctime)s] [%(levelname)-7s] %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_benchmark_sets():
    benchmark_sets = []
    for path in Path("benchmark_old").iterdir():
        if path.is_dir():
            benchmark_sets.append(path.name)
    return benchmark_sets


shutil.rmtree("result", ignore_errors=True)
shutil.rmtree("progress", ignore_errors=True)
shutil.rmtree("log", ignore_errors=True)
Path("result").mkdir(parents=True, exist_ok=True)
Path("progress").mkdir(parents=True, exist_ok=True)
Path("log").mkdir(parents=True, exist_ok=True)



def main():
    
    benchmark_sets = get_benchmark_sets()
    benchmark_sets.sort(key=lambda x: x.lower())
    benchmark_sets = benchmark_sets[:2]

    processes = []

    for benchmark_set in benchmark_sets:
        process = Process(target=single.main, name=benchmark_set, args=(benchmark_set, lock))
        process.start()
        logger.info(f"开始处理测例集: {process.name}")
        processes.append(process)

    for process in processes:
        process.join()
        logger.info(f"测例集处理完成: {process.name}")
    logger.info("所有测例集处理完成")


if __name__ == "__main__":
    main()
