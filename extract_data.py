import os
import re

data = []
for i in range(17):
    data.append([])

for i in range(7):
    for j in range(17):
        for file in os.listdir(f"concurrent/concurrent_{i + 13}/sub_{j}/output"):
            if file.startswith("concurrent"):
                with open(f"concurrent/concurrent_{i + 13}/sub_{j}/output/{file}", "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith("该算法最终得分"):
                            match = re.search(r"该算法最终得分：([0-9.]+)", line)
                            score = float(match.group(1))
                            data[j].append(score)
                            break
                break

with open("data", "w") as f:
    for i in range(17):
        for j in range(7):
            f.write(f"{data[i][j]} ")
        f.write("\n")