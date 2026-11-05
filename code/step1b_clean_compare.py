# -*- coding: utf-8 -*-
"""
第1步补充：数据清洗前后对比图（fig01 - fig03）
用途：在论文第4章"数据清洗与治理"里，用图表对比清洗前后的数据，
      证明"清洗后数据更干净、分布更合理，更有利于后续建模"。
生成的图：
  fig01 数据清洗流水线（瀑布图，展示每一步删了多少）
  fig02 清洗前的脏数据构成（横向条形图，展示各类脏数据数量）
  fig03 清洗前后单价分布对比（箱线图，展示极端值被清理后分布变正常）
数字均与 step1_load_clean.py 的清洗日志一致，可复核。
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# ========== 全局设置：中文字体 + 统一配色（与 step2 一致） ==========
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200
plt.rcParams["axes.edgecolor"] = "#666666"
plt.rcParams["axes.linewidth"] = 0.8

C_MAIN = "#2E75B6"    # 主蓝
C_LIGHT = "#9DC3E6"   # 浅蓝
C_ORANGE = "#ED7D31"  # 橙
C_GREEN = "#70AD47"   # 绿
C_GRAY = "#A6A6A6"    # 灰
C_RED = "#C00000"     # 红

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(BASE, "fig")
RAW = os.path.join(BASE, "data", "raw", "Online Retail.xlsx")
CLEAN = os.path.join(BASE, "data", "clean", "sales_clean.csv")
os.makedirs(FIG, exist_ok=True)


def save(fig, name):
    fig.savefig(os.path.join(FIG, name), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已保存:", name)


# ============================================================
# 图1：数据清洗流水线（瀑布图，断轴放大删除量）
# ============================================================
print("=" * 50)
print("图1：数据清洗流水线")
print("=" * 50)

labels = ["原始数据", "删除完全\n重复行", "拆分退货\n/取消单", "剔除非\n商品编码", "删除数值\n异常记录", "删除极端\n单价记录", "清洗后"]
# 每根柱：(bottom, height, 颜色)
bars = [
    (0, 541909, C_MAIN),       # 原始 541,909
    (536641, 5268, C_ORANGE),  # 去重 -5,268
    (527390, 9251, C_ORANGE),  # 退货 -9,251
    (525025, 2365, C_ORANGE),  # 非商品 -2,365
    (522531, 2494, C_ORANGE),  # 数值异常 -2,494
    (522529, 2, C_RED),        # 极端单价 -2
    (0, 522529, C_GREEN),      # 清洗后 522,529
]
top_vals = [541909, 541909, 536641, 527390, 525025, 522531, 522529]  # 每根柱顶部数值（用于标注）
del_vals = ["", "-5,268", "-9,251", "-2,365", "-2,494", "-2", ""]

fig, ax = plt.subplots(figsize=(10, 5.2))
x = np.arange(len(bars))
for i, (b, h, c) in enumerate(bars):
    ax.bar(i, h, bottom=b, color=c, width=0.62, zorder=3,
           edgecolor="white", linewidth=0.6)

# 顶部数值标注
for i, tv in enumerate(top_vals):
    ax.text(i, tv + 400, f"{tv:,}", ha="center", va="bottom",
            fontsize=10.5, color="#333333", fontweight="bold")
# 删除量标注（递减柱中间）
for i, dv in enumerate(del_vals):
    if dv:
        b = bars[i][0]
        h = bars[i][1]
        if i == 5:  # 极端单价只删2条，柱子太矮看不见，用红色箭头单独标注
            ax.annotate("-2", xy=(i, b + 3), xytext=(i + 0.34, b + 4500),
                        fontsize=10, color=C_RED, fontweight="bold",
                        arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.2))
        else:
            ax.text(i, b + h / 2, dv, ha="center", va="center",
                    fontsize=10, color="white", fontweight="bold")

# 断轴：纵轴从 520,000 起，放大显示删除量
ax.set_ylim(519000, 543500)
ax.axhline(520500, color="#888888", lw=1, ls="--", zorder=1, alpha=0.6)
ax.text(-0.42, 520900, "纵轴从\n520,000起", fontsize=8.5, color="#888888", ha="left", va="bottom")

# 断轴锯齿标记
d = 0.012
kwargs = dict(transform=ax.transAxes, color="#888888", clip_on=False, lw=1.2)
ax.plot((-d, +d), (0.00, 0.02), **kwargs)
ax.plot((-d, +d), (0.02, 0.04), **kwargs)

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9.5)
ax.tick_params(axis="y", labelsize=9)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v/10000:.1f}万"))
ax.set_ylabel("记录数（条）", fontsize=10)
ax.set_title("图1　数据清洗流水线（原始54.2万条 → 清洗后52.3万条，保留率96.4%）",
             fontsize=13, pad=12)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", ls="--", lw=0.5, alpha=0.35)
save(fig, "fig01_清洗流水线_数据量递减.png")


# ============================================================
# 图2：清洗前的脏数据构成（横向条形图，对数刻度）
# ============================================================
print("=" * 50)
print("图2：清洗前脏数据构成")
print("=" * 50)

cats = ["退货/取消单（拆分）", "完全重复行（删除）", "数值异常记录（删除）",
        "非商品编码（删除）", "缺失商品描述（补齐）", "极端单价记录（删除）"]
counts = [9251, 5268, 2494, 2365, 1454, 2]
# 降序排列
order = np.argsort(counts)[::-1]
cats = [cats[i] for i in order]
counts = [counts[i] for i in order]

fig, ax = plt.subplots(figsize=(10, 4.6))
y = np.arange(len(cats))[::-1]
colors = [C_ORANGE, C_ORANGE, C_ORANGE, C_ORANGE, C_GRAY, C_RED]
colors = [colors[i] for i in order]
bars = ax.barh(y, counts, color=colors, height=0.6, zorder=3,
               edgecolor="white", linewidth=0.6)
ax.set_xscale("log")
ax.set_xlim(0.8, 20000)
for yi, c, col in zip(y, counts, colors):
    ax.text(c * 1.15, yi, f"{c:,}", va="center", ha="left",
            fontsize=10, color="#333333", fontweight="bold")
ax.set_yticks(y)
ax.set_yticklabels(cats, fontsize=10.5)
ax.set_xlabel("记录数（条，对数刻度）", fontsize=10)
ax.set_title("图2　清洗前发现的六类脏数据（清洗后均已清零）", fontsize=13, pad=12)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="x", ls="--", lw=0.5, alpha=0.35)
save(fig, "fig02_清洗前后数据质量对比.png")


# ============================================================
# 图3：清洗前后单价分布对比（箱线图，对数刻度）
# ============================================================
print("=" * 50)
print("图3：清洗前后单价分布对比")
print("=" * 50)

df = pd.read_excel(RAW)
clean = pd.read_csv(CLEAN)

up_raw = df["UnitPrice"].dropna()
up_clean = clean["UnitPrice"].dropna()
# 只取正单价（负单价本身就是异常，正是清洗要剔除的）
up_raw_pos = up_raw[up_raw > 0]
up_clean_pos = up_clean[up_clean > 0]

fig, ax = plt.subplots(figsize=(10, 4.8))
bp = ax.boxplot([np.log10(up_raw_pos), np.log10(up_clean_pos)],
                labels=["清洗前", "清洗后"], widths=0.45, patch_artist=True,
                showfliers=True, flierprops=dict(marker="o", markersize=2.5,
                                                 markerfacecolor=C_GRAY, markeredgecolor="none", alpha=0.5))
for patch, color in zip(bp["boxes"], [C_ORANGE, C_GREEN]):
    patch.set_facecolor(color)
    patch.set_alpha(0.75)
for w in bp["whiskers"]:
    w.set_color("#555555")
for cap in bp["caps"]:
    cap.set_color("#555555")
for med in bp["medians"]:
    med.set_color(C_RED)
    med.set_linewidth(2)

# y 轴用原始单价标注（10^0, 10^1, ...）
ticks = [0, 1, 2, 3, 4, 5]
ax.set_yticks(ticks)
ax.set_yticklabels(["1", "10", "100", "1,000", "10,000", "100,000"], fontsize=9)
ax.set_ylabel("商品单价（英镑，对数刻度）", fontsize=10)

# 关键数字标注
ax.annotate("清洗前最大单价\n38,970 英镑", xy=(1, np.log10(38970)), xytext=(1.15, 4.5),
            fontsize=9, color=C_RED, ha="left",
            arrowprops=dict(arrowstyle="->", color=C_RED, lw=0.8))
ax.annotate("清洗后最大单价\n649.5 英镑", xy=(2, np.log10(649.5)), xytext=(2.28, 2.6),
            fontsize=9, color=C_GREEN, ha="left",
            arrowprops=dict(arrowstyle="->", color=C_GREEN, lw=0.8))
ax.text(1, 0.05, "中位数 2.08 英镑", fontsize=9, color="#333333", ha="center")
ax.text(2, 0.05, "中位数 2.08 英镑", fontsize=9, color="#333333", ha="center")

ax.set_title("图3　清洗前后商品单价分布对比（箱线图，对数刻度）", fontsize=13, pad=12)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", ls="--", lw=0.5, alpha=0.35)
save(fig, "fig03_清洗前后单价分布对比.png")

print("\n全部完成")
