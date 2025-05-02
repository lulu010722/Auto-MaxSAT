import pandas as pd

df = pd.read_csv("best_scores.csv")
df.loc[df["benchmark_set"] == "judgment-aggregation-ja-kemeny-preflib", ["best_score"]] = [1.1]
df.to_csv("best_scores.csv", index=False)