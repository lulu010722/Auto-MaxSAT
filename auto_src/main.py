from pathlib import Path
from multiprocessing import Process

import logging
import yaml
import shutil

import single

with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

OUTPUT_DIR_PATH = config["route"]["output"]
shutil.rmtree(OUTPUT_DIR_PATH, ignore_errors=True)
Path(OUTPUT_DIR_PATH).mkdir(parents=True, exist_ok=True)


logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(Path(OUTPUT_DIR_PATH) / "main.log")
formatter = logging.Formatter('[%(asctime)s] [%(levelname)-7s] %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


BENCHMARK_DIR_PATH = config["route"]["benchmark_old"]


def get_benchmark_sets():
    benchmark_sets = []
    for path in Path(BENCHMARK_DIR_PATH).iterdir():
        if path.is_dir():
            benchmark_sets.append(path.name)
    return benchmark_sets


def main():
    benchmark_sets = get_benchmark_sets()
    benchmark_sets.sort(key=lambda x: x.lower())
    # benchmark_sets = benchmark_sets[:2]

    processes = []
    for benchmark_set in benchmark_sets:
        process = Process(target=single.main, name=benchmark_set, kwargs={"benchmark_set": benchmark_set})
        process.start()
        logger.info(f"开始处理测例集: {process.name}")
        processes.append(process)

    for process in processes:
        process.join()
        logger.info(f"测例集处理完成: {process.name}")
    logger.info("所有测例集处理完成")


if __name__ == "__main__":
    main()
