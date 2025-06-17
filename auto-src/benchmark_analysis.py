import os
import re

features = []


for benchmark_set in os.listdir("benchmark-new-format"):
    if benchmark_set.startswith("switchinga"):
        continue
    nvars = 0
    ncls = 0
    total_lits = 0
    nhards = 0
    nhard_nlits = 0
    nsofts = 0
    nsoft_nlits = 0
    nsoft_wts = 0

    for file in os.listdir(f"benchmark-new-format/{benchmark_set}"):
        with open(f"benchmark-new-format/{benchmark_set}/{file}", "r") as wcnf_file:
            lines = []
            for i in range(30):
                line = wcnf_file.readline()
                lines.append(line)
            print(f"正在处理{file}")

            nvars += int(re.search(r'c "nvars":\s*(\d+(?:\.\d+)?),', lines[3]).group(1))
            ncls += int(re.search(r'c "ncls":\s*(\d+(?:\.\d+)?),', lines[4]).group(1))
            total_lits += int(re.search(r'c "total_lits":\s*(\d+(?:\.\d+)?),', lines[5]).group(1))
            nhards += int(re.search(r'c "nhards":\s*(\d+(?:\.\d+)?),', lines[6]).group(1))
            nhard_nlits += int(re.search(r'c "nhard_nlits":\s*(\d+(?:\.\d+)?),', lines[7]).group(1))
            nsofts += int(re.search(r'c "nsofts":\s*(\d+(?:\.\d+)?),', lines[13]).group(1))
            nsoft_nlits += int(re.search(r'c "nsoft_nlits":\s*(\d+(?:\.\d+)?),', lines[14]).group(1))
            nsoft_wts += int(re.search(r'c "nsoft_wts":\s*(\d+(?:\.\d+)?),', lines[20]).group(1))

    file_num = len(os.listdir(f"benchmark-new-format/{benchmark_set}"))
    nvars = nvars // file_num
    ncls = ncls // file_num
    total_lits = total_lits // file_num
    nhards = nhards // file_num
    nhard_nlits = nhard_nlits // file_num
    nsofts = nsofts // file_num
    nsoft_nlits = nsoft_nlits // file_num
    nsoft_wts = nsoft_wts // file_num

    features.append([nvars, ncls, total_lits, nhards / ncls, nsofts / ncls])

with open("test_feature.txt", "w") as file:
    for feature in features:
        for number in feature:
            string = str(number)
            file.write(f"{number:<20.3f}")
        file.write("\n")
