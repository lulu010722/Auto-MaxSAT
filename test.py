import multiprocessing
import subprocess

def worker(queue, i):
    # 执行脚本并捕获输出
    result = subprocess.run(["bash", 'test.sh'], capture_output=True, text=True)
    output = result.stdout.strip()
    queue.put(f"[Process {i}] Output:\n{output}")

if __name__ == '__main__':
    q = multiprocessing.Queue()
    processes = [multiprocessing.Process(target=worker, args=(q, i)) for i in range(3)]

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    # 主进程统一输出
    while not q.empty():
        print(q.get())
