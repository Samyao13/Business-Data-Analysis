# -*- coding: utf-8 -*-
"""
第3步：商业分析模型 + 业务模型图（fig16-fig22）
用到的5类模型：
  1) 帕累托/ABC分类（结构与价值） -> fig13
  2) RFM八分类（用户与客群）      -> fig17 气泡图、fig18 分层图
  3) 同期群留存分析（用户与客群）  -> fig19 热力图
  4) Apriori购物篮关联规则（关联） -> fig20 散点图、fig21 Top规则条形图
  5) Holt-Winters需求预测（预测）  -> fig22 预测+95%置信区间+回测
所有关键数字会打印并存到 data/clean/model_results.txt，写报告直接引用。
"""
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200

C_MAIN = "#2E75B6"; C_LIGHT = "#9DC3E6"; C_ORANGE = "#ED7D31"
C_GREEN = "#70AD47"; C_GRAY = "#A6A6A6"; C_RED = "#C00000"
PALETTE = ["#2E75B6", "#ED7D31", "#70AD47", "#FFC000", "#5B9BD5", "#A5A5A5", "#4472C4", "#264478"]

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(BASE, "fig")
sales = pd.read_csv(os.path.join(BASE, "data", "clean", "sales_clean.csv"),
                    parse_dates=["InvoiceDate"])
results = {}   # 存放关键数字


def save(fig, name):
    fig.savefig(os.path.join(FIG, name), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已保存:", name)


# ============================================================
# 模型1：帕累托 / ABC 分类（商品结构分析）
# ============================================================
print("\n===== 模型1：帕累托/ABC =====")
prod = (sales.groupby(["StockCode", "Description"])["Amount"].sum()
        .sort_values(ascending=False).reset_index())
prod["cum_pct"] = prod["Amount"].cumsum() / prod["Amount"].sum() * 100
prod["pct"] = prod["Amount"] / prod["Amount"].sum() * 100
# ABC：累计前70%为A类，70-90%为B类，90-100%为C类
prod["ABC"] = np.where(prod["cum_pct"] <= 70, "A",
              np.where(prod["cum_pct"] <= 90, "B", "C"))
abc_stat = prod.groupby("ABC").agg(商品数=("StockCode", "count"), 销售额占比=("pct", "sum"))
print(abc_stat)
results["pareto"] = {
    "A类商品数": int(abc_stat.loc["A", "商品数"]),
    "A类销售占比": round(float(abc_stat.loc["A", "销售额占比"]), 1),
    "B类商品数": int(abc_stat.loc["B", "商品数"]),
    "B类销售占比": round(float(abc_stat.loc["B", "销售额占比"]), 1),
    "C类商品数": int(abc_stat.loc["C", "商品数"]),
    "C类销售占比": round(float(abc_stat.loc["C", "销售额占比"]), 1),
    "商品总数": len(prod),
    "前20%商品销售占比": round(float(prod["pct"].iloc[: int(len(prod) * 0.2)].sum()), 1),
}

fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(prod))
ax.bar(x, (prod["Amount"] / 10000).to_numpy(), color=C_LIGHT, width=1.0, zorder=2)
ax.set_ylabel("销售额（万英镑）")
ax.set_xlabel("商品（按销售额降序）")
ax2 = ax.twinx()
ax2.plot(x, prod["cum_pct"].to_numpy(), color=C_RED, lw=2, zorder=3)
ax2.set_ylabel("累计销售额占比（%）", color=C_RED)
ax2.set_ylim(0, 105)
ax2.axhline(70, color=C_GRAY, ls="--", lw=1)
ax2.axhline(90, color=C_GRAY, ls="--", lw=1)
# 标注A/B/C分界线
a_end = (prod["cum_pct"] <= 70).sum()
b_end = (prod["cum_pct"] <= 90).sum()
ax2.axvline(a_end, color=C_ORANGE, ls=":", lw=1.2)
ax2.axvline(b_end, color=C_ORANGE, ls=":", lw=1.2)
ax2.text(a_end / 2, 75, f"A类\n{int(abc_stat.loc['A','商品数'])}种商品\n贡献{abc_stat.loc['A','销售额占比']:.1f}%",
         ha="center", fontsize=9, color="#333333",
         bbox=dict(boxstyle="round,pad=0.3", fc="#FFF2CC", ec="#BF9000", lw=0.8))
ax2.text((a_end + b_end) / 2, 55, f"B类\n{int(abc_stat.loc['B','商品数'])}种", ha="center",
         fontsize=9, color="#333333",
         bbox=dict(boxstyle="round,pad=0.3", fc="#DEEBF7", ec="#2E75B6", lw=0.8))
ax2.text(b_end + (len(prod) - b_end) / 2, 40, f"C类\n{int(abc_stat.loc['C','商品数'])}种", ha="center",
         fontsize=9, color="#333333",
         bbox=dict(boxstyle="round,pad=0.3", fc="#F2F2F2", ec="#7F7F7F", lw=0.8))
ax.set_title("图16  商品销售额帕累托分析（ABC分类）", fontsize=13, pad=12)
ax.spines[["top"]].set_visible(False)
save(fig, "fig16_帕累托图_商品ABC分类.png")

# ============================================================
# 模型2：RFM 八分类
# ============================================================
print("\n===== 模型2：RFM =====")
SNAPSHOT = pd.Timestamp("2011-12-10")  # 数据截止日后一天作为观察时点
cust = sales.dropna(subset=["CustomerID"]).copy()
rfm = cust.groupby("CustomerID").agg(
    最近购买=("InvoiceDate", "max"),
    F=("InvoiceNo", "nunique"),
    M=("Amount", "sum"))
rfm["R"] = (SNAPSHOT - rfm["最近购买"]).dt.days
rfm = rfm[["R", "F", "M"]]
print(rfm.describe().round(1))

# 阈值用中位数：比均值稳健，不受大额批发客户极端值影响
r_med, f_med, m_med = rfm["R"].median(), rfm["F"].median(), rfm["M"].median()
print(f"中位数阈值: R={r_med:.0f}天, F={f_med:.0f}次, M={m_med:.0f}英镑")
results["rfm_threshold"] = {"R中位数": float(r_med), "F中位数": float(f_med), "M中位数": round(float(m_med), 1)}

rfm["R高"] = rfm["R"] <= r_med   # R越小越近，记为"高"
rfm["F高"] = rfm["F"] >= f_med
rfm["M高"] = rfm["M"] >= m_med

seg_map = {
    (1, 1, 1): "重要价值客户", (1, 0, 1): "重要发展客户",
    (0, 1, 1): "重要保持客户", (0, 0, 1): "重要挽留客户",
    (1, 1, 0): "一般价值客户", (1, 0, 0): "一般发展客户",
    (0, 1, 0): "一般保持客户", (0, 0, 0): "一般挽留客户",
}
rfm["客户分层"] = [seg_map[(int(r), int(f), int(m))] for r, f, m in zip(rfm["R高"], rfm["F高"], rfm["M高"])]
seg_order = ["重要价值客户", "重要保持客户", "重要发展客户", "重要挽留客户",
             "一般价值客户", "一般保持客户", "一般发展客户", "一般挽留客户"]
seg_stat = rfm.groupby("客户分层").agg(人数=("R", "count"), 人均消费=("M", "mean"), 消费总额=("M", "sum"))
seg_stat = seg_stat.reindex(seg_order)
seg_stat["人数占比"] = seg_stat["人数"] / seg_stat["人数"].sum() * 100
seg_stat["金额占比"] = seg_stat["消费总额"] / seg_stat["消费总额"].sum() * 100
print(seg_stat.round(1))
results["rfm_seg"] = seg_stat.round(1).to_dict()
rfm.to_csv(os.path.join(BASE, "data", "clean", "rfm_result.csv"), encoding="utf-8-sig")

# --- fig17 RFM气泡散点图 ---
fig, ax = plt.subplots(figsize=(10, 6))
colors8 = dict(zip(seg_order, PALETTE))
for seg in seg_order:
    d = rfm[rfm["客户分层"] == seg]
    size = np.clip(d["M"] / d["M"].quantile(0.95) * 260, 12, 300)
    ax.scatter(d["R"].to_numpy(), d["F"].to_numpy(), s=size, alpha=0.55, color=colors8[seg], label=seg, edgecolors="none")
ax.axvline(r_med, color="#999999", ls="--", lw=1)
ax.axhline(f_med, color="#999999", ls="--", lw=1)
ax.set_xlim(-5, 375)
ax.set_ylim(0, 60)
ax.text(r_med + 5, 56, f"R中位数={r_med:.0f}天", fontsize=9, color="#666666")
ax.set_xlabel("R：距最近购买天数（天）")
ax.set_ylabel("F：购买次数（次）")
ax.set_title("图17  RFM客户价值气泡图（气泡大小=消费金额M）", fontsize=13, pad=12)
ax.legend(fontsize=8.5, loc="upper right", frameon=True, framealpha=0.9)
ax.spines[["top", "right"]].set_visible(False)
save(fig, "fig17_RFM气泡图.png")

# --- fig18 RFM八分类人数与金额贡献 ---
fig, ax = plt.subplots(figsize=(10, 5.5))
y = np.arange(len(seg_stat))
ax.barh(y - 0.2, seg_stat["人数占比"].to_numpy(), height=0.38, color=C_MAIN, label="人数占比(%)", zorder=2)
ax.barh(y + 0.2, seg_stat["金额占比"].to_numpy(), height=0.38, color=C_ORANGE, label="消费金额占比(%)", zorder=2)
for i, (p, m_) in enumerate(zip(seg_stat["人数占比"], seg_stat["金额占比"])):
    ax.text(p + 0.4, i - 0.2, f"{p:.1f}%", va="center", fontsize=9, color=C_MAIN)
    ax.text(m_ + 0.4, i + 0.2, f"{m_:.1f}%", va="center", fontsize=9, color=C_ORANGE)
ax.set_yticks(y)
ax.set_yticklabels(seg_stat.index, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel("占比（%）")
ax.set_title("图18  RFM八类客户：人数占比 vs 消费金额占比", fontsize=13, pad=12)
ax.legend(fontsize=10, loc="lower right", frameon=False)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", ls="--", alpha=0.3, zorder=0)
save(fig, "fig18_RFM八分类客户.png")

# ============================================================
# 模型3：同期群留存分析
# ============================================================
print("\n===== 模型3：同期群留存 =====")
cust["首购月"] = cust.groupby("CustomerID")["InvoiceDate"].transform("min").dt.to_period("M")
cust["活跃月"] = cust["InvoiceDate"].dt.to_period("M")
cohort = (cust.groupby(["首购月", "活跃月"])["CustomerID"].nunique().reset_index())
cohort["期数"] = (cohort["活跃月"] - cohort["首购月"]).apply(lambda x: x.n)
mat = cohort.pivot_table(index="首购月", columns="期数", values="CustomerID")
size0 = mat[0]
retention = mat.divide(size0, axis=0) * 100
print(retention.round(1))
avg_ret1 = retention[1].mean()
avg_ret3 = retention[3].mean()
results["cohort"] = {"次月平均留存": round(float(avg_ret1), 1), "第3月平均留存": round(float(avg_ret3), 1)}

fig, ax = plt.subplots(figsize=(10, 6))
import matplotlib.colors as mcolors
cmap = mcolors.LinearSegmentedColormap.from_list("bl", ["#FFFFFF", "#9DC3E6", "#2E75B6"])
data = retention.iloc[:, :12].to_numpy()
im = ax.imshow(data, cmap=cmap, vmin=0, vmax=60, aspect="auto")
ax.set_xticks(range(data.shape[1]))
ax.set_xticklabels([f"第{c}月" if c > 0 else "首月" for c in retention.columns[:12]], fontsize=9)
ax.set_yticks(range(len(retention)))
ax.set_yticklabels([str(i) for i in retention.index], fontsize=9)
for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        if not np.isnan(data[i, j]):
            ax.text(j, i, f"{data[i, j]:.0f}", ha="center", va="center", fontsize=8.5,
                    color="white" if data[i, j] > 32 else "#333333")
plt.colorbar(im, ax=ax, label="留存率（%）", shrink=0.85)
ax.set_title("图19  客户同期群月度留存热力图（%）", fontsize=13, pad=12)
save(fig, "fig19_同期群留存热力图.png")

# ============================================================
# 模型4：Apriori 购物篮关联规则
# ============================================================
print("\n===== 模型4：Apriori关联规则 =====")
from mlxtend.frequent_patterns import apriori, association_rules
# 只取英国市场销量前120的商品，保证稀疏矩阵可控、规则更有业务意义
uk = sales[sales["Country"] == "United Kingdom"]
top_items = uk.groupby("Description")["Quantity"].sum().nlargest(120).index
basket = (uk[uk["Description"].isin(top_items)]
          .groupby(["InvoiceNo", "Description"])["Quantity"].sum().unstack().fillna(0))
basket = (basket > 0).astype(int)
print("购物篮矩阵:", basket.shape)
freq = apriori(basket, min_support=0.02, use_colnames=True)
rules = association_rules(freq, metric="lift", min_threshold=1.2)
rules = rules.sort_values("lift", ascending=False)
rules["rule"] = rules.apply(
    lambda r: " + ".join(list(r["antecedents"]))[:25] + " → " + " + ".join(list(r["consequents"]))[:25], axis=1)
print(rules[["rule", "support", "confidence", "lift"]].head(10).to_string())
results["apriori"] = {
    "规则数": len(rules),
    "top3": rules[["rule", "support", "confidence", "lift"]].head(3).round(3).to_dict("records"),
}
rules.head(30).to_csv(os.path.join(BASE, "data", "clean", "apriori_rules.csv"),
                      index=False, encoding="utf-8-sig")

# --- fig20 关联规则散点图 ---
fig, ax = plt.subplots(figsize=(9.5, 6))
sc = ax.scatter((rules["support"] * 100).to_numpy(), (rules["confidence"] * 100).to_numpy(),
                s=rules["lift"] * 40, c=rules["lift"], cmap="YlOrRd",
                alpha=0.75, edgecolors="#999999", linewidths=0.5)
plt.colorbar(sc, ax=ax, label="提升度 Lift")
top5 = rules.head(5)
for _, r in top5.iterrows():
    ax.annotate(r["rule"][:30], (r["support"] * 100, r["confidence"] * 100),
                textcoords="offset points", xytext=(8, 6), fontsize=8, color="#333333")
ax.set_xlabel("支持度 Support（%）")
ax.set_ylabel("置信度 Confidence（%）")
ax.set_title("图20  关联规则分布（气泡大小与颜色=提升度）", fontsize=13, pad=12)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(ls="--", alpha=0.3)
save(fig, "fig20_关联规则散点图.png")

# --- fig21 Top10关联规则条形图 ---
top10r = rules.head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.barh(range(10), top10r["lift"].to_numpy(), color=C_MAIN, height=0.6, zorder=2)
for i, (lft, conf) in enumerate(zip(top10r["lift"], top10r["confidence"])):
    ax.text(lft + 0.3, i, f"lift={lft:.1f}  conf={conf*100:.0f}%", va="center", fontsize=8.5, color="#333333")
ax.set_yticks(range(10))
ax.set_yticklabels(top10r["rule"], fontsize=8.5)
ax.set_xlabel("提升度 Lift")
ax.set_xlim(0, top10r["lift"].max() * 1.45)
ax.set_title("图21  提升度Top10关联规则（英国市场）", fontsize=13, pad=12)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", ls="--", alpha=0.3, zorder=0)
save(fig, "fig21_Top10关联规则.png")

# ============================================================
# 模型5：Holt-Winters 需求预测（含95%置信区间与回测）
# ============================================================
print("\n===== 模型5：Holt-Winters预测 =====")
from statsmodels.tsa.holtwinters import ExponentialSmoothing
daily = sales.set_index("InvoiceDate")["Amount"].resample("D").sum()
daily = daily[daily.index <= "2011-12-09"]
train = daily[daily.index <= "2011-10-31"]
test = daily[(daily.index > "2011-10-31") & (daily.index <= "2011-11-30")]
print(f"日度序列: 训练集{len(train)}天, 测试集{len(test)}天")

# 加法趋势 + 周季节（周期7）：零售数据有明显“周末低、工作日高”的周节律
fit1 = ExponentialSmoothing(train, trend="add", seasonal="add",
                            seasonal_periods=7).fit(optimized=True)
pred = fit1.forecast(len(test))
# 测试期有几天销售额为0（节假日无交易），MAPE对0值会除爆，剔除这些天数再算
mask = test > 0
mape = np.mean(np.abs((test[mask] - pred[mask]) / test[mask])) * 100
rmse = np.sqrt(np.mean((test - pred) ** 2))
print(f"测试期零销售天数: {(~mask).sum()} 天（计算MAPE时已剔除）")
print(f"回测: MAPE={mape:.2f}%  RMSE={rmse:.0f}")
results["forecast"] = {"MAPE": round(float(mape), 2), "RMSE": round(float(rmse), 0),
                       "测试月份": "2011-11", "零销售天数": int((~mask).sum())}

# 全量数据重拟合，预测未来30天
fit2 = ExponentialSmoothing(daily, trend="add", seasonal="add",
                            seasonal_periods=7).fit(optimized=True)
future = fit2.forecast(30)
resid_std = np.std(fit2.resid)
h = np.arange(1, 31)
ci = 1.96 * resid_std * np.sqrt(h / 7 + 1)  # 随预测步长放宽的近似区间
fut_idx = pd.date_range("2011-12-10", periods=30, freq="D")

fig, ax = plt.subplots(figsize=(11, 5.5))
hist = daily[daily.index >= "2011-09-01"]
hx = mdates.date2num(hist.index.to_pydatetime())
tx = mdates.date2num(test.index.to_pydatetime())
fx = mdates.date2num(fut_idx.to_pydatetime())
ax.plot_date(hx, hist.to_numpy(), "-", color=C_MAIN, lw=1.5, label="历史日销售额")
ax.plot_date(tx, pred.to_numpy(), "-", color=C_GREEN, lw=2, label="11月回测预测")
ax.plot_date(fx, future.to_numpy(), "-", color=C_RED, lw=2, label="未来30天预测")
ax.fill_between(fx, (future - ci).to_numpy(), (future + ci).to_numpy(),
                color=C_RED, alpha=0.15, label="95%置信区间")
ax.axvline(mdates.date2num(pd.Timestamp("2011-11-01")), color="#999999", ls=":", lw=1)
ax.axvline(mdates.date2num(pd.Timestamp("2011-12-09")), color="#999999", ls=":", lw=1)
ax.text(mdates.date2num(pd.Timestamp("2011-11-02")), ax.get_ylim()[1] * 0.92,
        "← 回测期", fontsize=9, color="#666666")
ax.text(mdates.date2num(pd.Timestamp("2011-12-10")), ax.get_ylim()[1] * 0.92,
        "预测期 →", fontsize=9, color="#666666")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
ax.text(0.02, 0.04, f"回测误差：MAPE={mape:.1f}%  RMSE={rmse:,.0f} 英镑",
        transform=ax.transAxes, fontsize=10,
        bbox=dict(boxstyle="round,pad=0.35", fc="#FFF2CC", ec="#BF9000", lw=0.8))
ax.set_ylabel("日销售额（英镑）")
ax.set_title("图22  Holt-Winters日销售额预测（加法趋势+周季节，含95%置信区间）", fontsize=13, pad=12)
ax.legend(fontsize=9.5, loc="upper right", frameon=False)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(ls="--", alpha=0.3)
save(fig, "fig22_HoltWinters预测.png")

# ========== 汇总关键数字 ==========
with open(os.path.join(BASE, "data", "clean", "model_results.txt"), "w", encoding="utf-8") as f:
    f.write(json.dumps(results, ensure_ascii=False, indent=2, default=str))
print("\n模型结果已存到 data/clean/model_results.txt")
print(json.dumps(results, ensure_ascii=False, indent=2, default=str)[:800])
print("\n第二批图（fig16-fig22）全部完成！")
