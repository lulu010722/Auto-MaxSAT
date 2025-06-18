import os
import shutil

benchmark_dir = "benchmark_old"


def has_benchmark_set(benchmark_set_name):
    for dir_name in os.listdir(benchmark_dir):
        dir_path = os.path.join(benchmark_dir, dir_name)
        if os.path.isdir(dir_path):
            if dir_name == benchmark_set_name:
                return True
    return False


def sort_into_benchmark_set():
    for filename in os.listdir(benchmark_dir):
        filepath = os.path.join(benchmark_dir, filename)
        if os.path.isfile(filepath):
            benchmark_set_dir_name = filename[:10]
            benchmark_set_dir_path = os.path.join(benchmark_dir, benchmark_set_dir_name)
            if has_benchmark_set(benchmark_set_dir_name):
                shutil.move(filepath, benchmark_set_dir_path)
            else:
                os.makedirs(benchmark_set_dir_path, exist_ok=False)
                shutil.move(filepath, benchmark_set_dir_path)


def remove_minor_benchmark_set():
    for dir_name in os.listdir(benchmark_dir):
        dir_path = os.path.join(benchmark_dir, dir_name)
        if os.path.isdir(dir_path):
            if len(os.listdir(dir_path)) < 5:
                shutil.rmtree(dir_path)


def main():
    sort_into_benchmark_set()
    remove_minor_benchmark_set()


if __name__ == "__main__":
    main()
