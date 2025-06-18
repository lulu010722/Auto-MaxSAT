from pathlib import Path
from rich.logging import RichHandler
from datetime import datetime
from multiprocessing import Process

import logging
import yaml

import single


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_time=False)]
)


logger = logging.getLogger(__name__)

file_handler = logging.FileHandler("test.log", mode="a", encoding="utf-8")

logger.addHandler(file_handler)

with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

BENCHMARK_DIR_PATH = config["route"]["benchmark"]



def get_benchmark_sets():
    benchmark_sets = []
    for path in Path(BENCHMARK_DIR_PATH).iterdir():
        if path.is_dir():
            benchmark_sets.append(path.name)
    return benchmark_sets


def main():
    benchmark_sets = get_benchmark_sets()
    benchmark_sets.sort(key=lambda x: x.lower())

    processes = []
    for benchmark_set in benchmark_sets:
        process = Process(target=single.main, kwargs={"benchmark_set": benchmark_set})
        processes.append(process)

    for p in processes:
        p.start()
        logger.info(f"开始处理测例集: {p.name}")
    for p in processes:
        p.join()
        logger.info(f"测例集处理完成: {p.name}")
    logger.info("所有测例集处理完成")


if __name__ == "__main__":
    main()
