# -*- coding: utf-8 -*-
"""
第2步：探索性分析 + 复现《Excel数据可视化》第二章模板图（fig04-fig15）
统一采用深色商务主题，贴近教材第二章图表模板风格。
  fig04 渐变柱形图    fig05 带均值柱形图   fig06 标注柱形图
  fig07 层叠柱形图    fig08 蝴蝶图          fig09 甘特图
  fig10 平滑折线图    fig11 对比折线图      fig12 单值圆环图
  fig13 南丁格尔圆环图 fig14 仪表盘图        fig15 子弹图
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
import matplotlib.colors as mcolors

# ========== 全局设置：中文字体 + 深色商务主题 ==========
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200

# 深色商务配色（贴近教材模板）
BG = "#1F2A44"          # 深藏青背景
FG_TITLE = "#FFFFFF"    # 标题白
FG_SUB = "#A8B6CC"      # 副标题浅灰蓝
FG_LABEL = "#E6ECF5"    # 数据标签近白
FG_TICK = "#B8C4D9"     # 刻度文字
FG_NOTE = "#8A97AE"     # 注释灰
GRID = "#3A4A6B"        # 网格线
C_MAIN = "#4A90D9"      # 主蓝
C_MAIN_DEEP = "#1F4E79" # 深蓝
C_LIGHT = "#7FB3E8"     # 浅蓝
C_ORANGE = "#F5A623"    # 橙（均值线/强调）
C_GREEN = "#5FB05A"     # 绿
C_GOLD = "#E8C24A"      # 金黄
C_RED = "#E55A4E"       # 红
PALETTE = ["#4A90D9", "#F5A623", "#5FB05A", "#E8C24A", "#7FB3E8", "#B8C4D9"]

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(BASE, "fig")
os.makedirs(FIG, exist_ok=True)

sales = pd.read_csv(os.path.join(BASE, "data", "clean", "sales_clean.csv"),
                    parse_dates=["InvoiceDate"])
print("读取清洗后数据:", sales.shape)


def style_ax(ax):
    """统一深色风格：背景、刻度、边框、网格"""
    ax.set_facecolor(BG)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(GRID)
    ax.tick_params(colors=FG_TICK, labelsize=9)
    ax.yaxis.label.set_color(FG_TICK)
    ax.xaxis.label.set_color(FG_TICK)
    ax.grid(axis="y", ls="--", color=GRID, alpha=0.35, zorder=0)


def set_title(ax, main, sub=None, y=1.02):
    """主标题（白）+ 可选副标题（浅灰），左对齐贴近原作"""
    ax.set_title(main, color=FG_TITLE, fontsize=14, fontweight="bold",
                 loc="left", pad=26)
    if sub:
        ax.text(0, y, sub, transform=ax.transAxes, color=FG_SUB, fontsize=10,
                va="bottom", ha="left")


def save(fig, name):
    path = os.path.join(FIG, name)
    fig.savefig(path, bbox_inches="tight", facecolor=BG, edgecolor=BG)
    plt.close(fig)
    print("已保存:", name)


def gradient_bars(ax, x, heights, color_top="#5BA8E8", color_bottom="#1F4E79", width=0.62):
    """竖向渐变柱：顶部浅、底部深，贴近原作渐变柱形图"""
    cmap = mcolors.LinearSegmentedColormap.from_list("grad", [color_bottom, color_top])
    for xi, h in zip(x, heights):
        ax.bar(xi, h, width=width, color="none", zorder=2)
        grad = np.linspace(0, 1, 256).reshape(-1, 1)
        ax.imshow(grad, extent=[xi - width / 2, xi + width / 2, 0, h],
                  aspect="auto", cmap=cmap, zorder=2, vmin=0, vmax=1)
    ax.set_ylim(0, max(heights) * 1.18)


# ========== 公共数据准备 ==========
CN_MAP = {"United Kingdom": "英国", "Netherlands": "荷兰", "EIRE": "爱尔兰", "Germany": "德国",
          "France": "法国", "Australia": "澳大利亚", "Spain": "西班牙", "Belgium": "比利时",
          "Switzerland": "瑞士", "Sweden": "瑞典", "Norway": "挪威", "Italy": "意大利",
          "Denmark": "丹麦", "Portugal": "葡萄牙", "Japan": "日本", "Finland": "芬兰",
          "Austria": "奥地利", "USA": "美国", "Canada": "加拿大"}
monthly = sales.groupby("YearMonth")["Amount"].sum()
country_amt = sales.groupby("Country")["Amount"].sum().sort_values(ascending=False)
uk_amt = country_amt.get("United Kingdom", 0)

# ========== fig04 渐变柱形图：Top10国家销售额 ==========
top10c = country_amt.head(10) / 10000  # 万英镑
fig, ax = plt.subplots(figsize=(9, 5.2))
fig.patch.set_facecolor(BG)
labels = [CN_MAP.get(c, c) for c in top10c.index]
gradient_bars(ax, np.arange(10), top10c.values)
ax.set_xticks(np.arange(10))
ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9, color=FG_TICK)
for i, v in enumerate(top10c.values):
    ax.text(i, v + max(top10c.values) * 0.015, f"{v:,.0f}", ha="center",
            fontsize=9, color=FG_LABEL)
style_ax(ax)
set_title(ax, "图4  销售额Top10国家/地区",
          "英国872万英镑一枝独秀，是第二名荷兰的约31倍，本土市场是绝对基本盘")
ax.set_ylabel("销售额（万英镑）")
save(fig, "fig04_渐变柱形图_国家销售额Top10.png")

# ========== fig05 带均值柱形图：月度销售额 ==========
m = monthly / 10000
fig, ax = plt.subplots(figsize=(10, 5.2))
fig.patch.set_facecolor(BG)
ax.bar(range(len(m)), m.values, color=C_MAIN, width=0.66, zorder=2)
mean_v = m.mean()
ax.axhline(mean_v, color=C_ORANGE, ls="--", lw=2, zorder=3)
ax.text(len(m) - 0.45, mean_v + max(m.values) * 0.02, f"平均值 {mean_v:,.1f} 万英镑",
        color=C_ORANGE, ha="right", fontsize=10, fontweight="bold")
for i, v in enumerate(m.values):
    ax.text(i, v + max(m.values) * 0.012, f"{v:,.0f}", ha="center", fontsize=8.5,
            color=FG_LABEL)
ax.set_xticks(range(len(m)))
ax.set_xticklabels(m.index, rotation=45, ha="right", fontsize=9, color=FG_TICK)
style_ax(ax)
set_title(ax, "图5  月度销售额与均值线",
          "前三季度平稳，9月起圣诞季拉升，11月冲到145.2万英镑峰值")
ax.set_ylabel("销售额（万英镑）")
ax.text(0, -max(m.values) * 0.26, "注：2010年12月为数据起始月，2011年12月数据截至12月9日。",
        fontsize=8.5, color=FG_NOTE)
save(fig, "fig05_带均值柱形图_月度销售额.png")

# ========== fig06 标注柱形图：Top10商品销售额 ==========
prod = sales.groupby(["StockCode", "Description"])["Amount"].sum().sort_values(ascending=False)
top10p = prod.head(10) / 10000
names = [d[:18] + ("…" if len(d) > 18 else "") for d in top10p.index.get_level_values(1)]
fig, ax = plt.subplots(figsize=(10, 5.6))
fig.patch.set_facecolor(BG)
colors = [C_ORANGE if i == 0 else C_MAIN for i in range(10)]
ax.bar(range(10), top10p.values, color=colors, width=0.62, zorder=2)
for i, v in enumerate(top10p.values):
    ax.text(i, v + max(top10p.values) * 0.02, f"{v:.1f}", ha="center", fontsize=9,
            color=C_ORANGE if i == 0 else FG_LABEL,
            fontweight="bold" if i == 0 else "normal")
ax.set_xticks(range(10))
ax.set_xticklabels(names, rotation=32, ha="right", fontsize=8.5, color=FG_TICK)
style_ax(ax)
set_title(ax, "图6  销售额Top10商品",
          "冠军商品 REGENCY CAKESTAND 3 TIER 单品约16.9万英镑，是第十名的两倍多")
ax.set_ylabel("销售额（万英镑）")
save(fig, "fig06_标注柱形图_商品销售额Top10.png")

# ========== fig07 层叠柱形图：Top4国家季度销售额 ==========
sales["Quarter"] = sales["InvoiceDate"].dt.to_period("Q").astype(str)
top4 = country_amt.head(4).index.tolist()
q = (sales[sales["Country"].isin(top4)]
     .pivot_table(index="Quarter", columns="Country", values="Amount", aggfunc="sum")
     .fillna(0) / 10000)
q = q[top4]
fig, ax = plt.subplots(figsize=(9, 5.2))
fig.patch.set_facecolor(BG)
bottom = np.zeros(len(q))
for i, c in enumerate(q.columns):
    ax.bar(q.index, q[c], bottom=bottom, label=CN_MAP.get(c, c),
           color=PALETTE[i], width=0.55, zorder=2, edgecolor=BG)
    for j, v in enumerate(q[c]):
        if v > q.values.sum() * 0.02:
            ax.text(j, bottom[j] + v / 2, f"{v:,.0f}", ha="center", va="center",
                    fontsize=8, color="#FFFFFF", fontweight="bold")
    bottom += q[c].values
style_ax(ax)
set_title(ax, "图7  Top4国家各季度销售额",
          "英国占绝对大头且逐季走高，海外三国只占柱子的薄薄一层")
ax.set_ylabel("销售额（万英镑）")
leg = ax.legend(loc="upper left", fontsize=9, frameon=False)
for t in leg.get_texts():
    t.set_color(FG_LABEL)
save(fig, "fig07_层叠柱形图_国家季度销售额.png")

# ========== fig08 蝴蝶图：英国 vs 海外月度对比 ==========
sales["is_uk"] = sales["Country"] == "United Kingdom"
fly = sales.pivot_table(index="YearMonth", columns="is_uk", values="Amount", aggfunc="sum").fillna(0) / 10000
fly.columns = ["海外市场", "英国本土"]
fig, ax = plt.subplots(figsize=(9, 6))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
y = np.arange(len(fly))
ax.barh(y, -fly["英国本土"], color=C_MAIN, height=0.6, label="英国本土", zorder=2)
ax.barh(y, fly["海外市场"], color=C_ORANGE, height=0.6, label="海外市场", zorder=2)
for i, (a, b) in enumerate(zip(fly["英国本土"], fly["海外市场"])):
    ax.text(-a - 8, i, f"{a:,.0f}", ha="right", va="center", fontsize=8.5, color=C_MAIN)
    ax.text(b + 8, i, f"{b:,.0f}", ha="left", va="center", fontsize=8.5, color=C_ORANGE)
ax.set_yticks(y)
ax.set_yticklabels(fly.index, fontsize=9, color=FG_TICK)
ax.axvline(0, color=FG_TICK, lw=1)
lim = fly.values.max() * 1.25
ax.set_xlim(-lim, lim)
ax.set_xticks([])
set_title(ax, "图8  英国本土与海外市场月度对比",
          "两侧形状高度同步，海外市场只是被动承接，没有本地化运营")
leg = ax.legend(loc="lower right", fontsize=10, frameon=False)
for t in leg.get_texts():
    t.set_color(FG_LABEL)
for spine in ["top", "right", "bottom", "left"]:
    ax.spines[spine].set_visible(False)
save(fig, "fig08_蝴蝶图_英国vs海外月度对比.png")

# ========== fig09 甘特图：Top10客户活跃期 ==========
cust_sales = sales.dropna(subset=["CustomerID"])
top10u = (cust_sales.groupby("CustomerID")["Amount"].sum()
          .sort_values(ascending=False).head(10).index)
gantt = (cust_sales[cust_sales["CustomerID"].isin(top10u)]
         .groupby("CustomerID")["InvoiceDate"].agg(["min", "max"]))
gantt = gantt.sort_values("min")
fig, ax = plt.subplots(figsize=(10, 5.2))
fig.patch.set_facecolor(BG)
base_date = pd.Timestamp("2010-12-01")
for i, (cid, row) in enumerate(gantt.iterrows()):
    start = (row["min"] - base_date).days
    dur = max((row["max"] - row["min"]).days, 3)
    ax.broken_barh([(start, dur)], (i - 0.3, 0.6), facecolors=C_MAIN, alpha=0.9)
    ax.text(start + dur + 6, i, f"{dur}天", va="center", fontsize=8.5, color=FG_SUB)
ax.set_yticks(range(len(gantt)))
ax.set_yticklabels([f"客户 {int(c)}" for c in gantt.index], fontsize=9, color=FG_TICK)
ticks = [(pd.Timestamp(f"2011-{mm:02d}-01") - base_date).days for mm in range(1, 13)]
ax.set_xticks(ticks)
ax.set_xticklabels([f"2011-{mm:02d}" for mm in range(1, 13)], rotation=45, ha="right",
                   fontsize=8.5, color=FG_TICK)
style_ax(ax)
set_title(ax, "图9  消费额Top10客户活跃期",
          "头部客户大多全年持续活跃，是长期复购的批发关系而非一锤子买卖")
ax.set_xlabel("日期")
ax.grid(axis="x", ls="--", color=GRID, alpha=0.35)
ax.grid(axis="y", ls="--", color=GRID, alpha=0.35)
save(fig, "fig09_甘特图_Top10客户活跃期.png")

# ========== fig10 平滑折线图：周销售额走势 ==========
import matplotlib.dates as mdates
weekly = sales.set_index("InvoiceDate")["Amount"].resample("W").sum() / 10000
smooth = weekly.rolling(4, center=True, min_periods=1).mean()
wx = mdates.date2num(weekly.index.to_pydatetime())
fig, ax = plt.subplots(figsize=(10, 5.2))
fig.patch.set_facecolor(BG)
ax.plot_date(wx, weekly.to_numpy(), "-", color=C_LIGHT, lw=1, alpha=0.65, label="周销售额（原始）")
ax.plot_date(wx, smooth.to_numpy(), "-", color=C_MAIN, lw=2.8, label="4周移动平均（平滑）")
ax.fill_between(wx, smooth.to_numpy(), alpha=0.15, color=C_MAIN)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
style_ax(ax)
set_title(ax, "图10  周销售额走势与4周移动平均",
          "年末冲高明显，11月下旬达全年最高；年中5–6月有一波夏季促销小高峰")
ax.set_ylabel("销售额（万英镑）")
leg = ax.legend(fontsize=10, frameon=False)
for t in leg.get_texts():
    t.set_color(FG_LABEL)
save(fig, "fig10_平滑折线图_周销售额走势.png")

# ========== fig11 对比折线图：Top3国家月度走势 ==========
top3 = country_amt.head(3).index.tolist()
mm = (sales[sales["Country"].isin(top3)]
      .pivot_table(index="YearMonth", columns="Country", values="Amount", aggfunc="sum") / 10000)
fig, ax = plt.subplots(figsize=(10, 5.2))
fig.patch.set_facecolor(BG)
markers = ["o", "s", "^"]
for i, c in enumerate(top3):
    ax.plot(range(len(mm)), mm[c].to_numpy(), marker=markers[i], ms=6, lw=2,
            color=PALETTE[i], label=CN_MAP.get(c, c))
ax.set_xticks(range(len(mm)))
ax.set_xticklabels(mm.index, rotation=45, ha="right", fontsize=9, color=FG_TICK)
style_ax(ax)
set_title(ax, "图11  Top3国家月度销售额走势对比",
          "三条线9–11月齐头向上，圣诞季是全市场共振而非单一市场偶然")
ax.set_ylabel("销售额（万英镑）")
leg = ax.legend(fontsize=10, frameon=False)
for t in leg.get_texts():
    t.set_color(FG_LABEL)
save(fig, "fig11_对比折线图_Top3国家月度走势.png")

# ========== fig12 单值圆环图：英国市场占比 ==========
uk_share = uk_amt / country_amt.sum() * 100
fig, ax = plt.subplots(figsize=(6, 6))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.pie([uk_share, 100 - uk_share], startangle=90, counterclock=False,
       colors=[C_MAIN, "#33415E"], wedgeprops=dict(width=0.3, edgecolor=BG))
ax.text(0, 0.1, f"{uk_share:.1f}%", ha="center", va="center", fontsize=32,
        fontweight="bold", color=FG_TITLE)
ax.text(0, -0.22, "英国本土销售额占比", ha="center", va="center", fontsize=12, color=FG_SUB)
set_title(ax, "图12  英国本土销售额占比",
          "85.1%的销售额来自英国本土，海外38个市场合计不到15%")
save(fig, "fig12_单值圆环图_英国占比.png")

# ========== fig13 南丁格尔圆环图：Top8海外国家 ==========
oversea = country_amt.drop("United Kingdom").head(8) / 10000
oversea = oversea.sort_values(ascending=False)  # 按数值降序排列
fig = plt.figure(figsize=(8, 8))
fig.patch.set_facecolor(BG)
ax = fig.add_subplot(111, polar=True)
ax.set_facecolor(BG)
n = len(oversea)
theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
radii = np.sqrt(oversea.values)
width = 2 * np.pi / n * 0.86
# 单色系渐变（蓝），按数值深浅
cmap = mcolors.LinearSegmentedColormap.from_list("blue", ["#9DC3E6", "#1F4E79"])
norm = mcolors.Normalize(vmin=oversea.values.min(), vmax=oversea.values.max())
colors = [cmap(norm(v)) for v in oversea.values]
bars = ax.bar(theta, radii, width=width, bottom=1.2,
              color=colors, alpha=0.95, edgecolor=BG, linewidth=1.5)
name_map = CN_MAP
for t, r, cname, v in zip(theta, radii, oversea.index, oversea.values):
    ax.text(t, r + 1.9, f"{name_map.get(cname, cname)}\n{v:,.0f}",
            ha="center", va="center", fontsize=9, color=FG_LABEL)
ax.set_yticklabels([])
ax.set_xticklabels([])
ax.spines["polar"].set_visible(False)
ax.grid(color=GRID, alpha=0.35)
set_title(ax, "图13  海外Top8国家/地区销售额（单位：万英镑）",
          "荷兰、爱尔兰、德国构成海外第一梯队，梯队结构分明")
save(fig, "fig13_南丁格尔圆环图_海外国家.png")

# ========== fig14 仪表盘图：12月目标达成率 ==========
nov = sales[sales["YearMonth"] == "2011-11"]["Amount"].sum()
dec = sales[sales["YearMonth"] == "2011-12"]["Amount"].sum()
target = nov / 30 * 9
rate = dec / target * 100  # 实际达成率 141.1%，不封顶
fig, ax = plt.subplots(figsize=(7, 5.2))
fig.patch.set_facecolor(BG)
ax.axis("equal")
ax.axis("off")
ax.set_facecolor(BG)
# 刻度上限 150%
SCALE = 150
# 背景半圆（灰）
ax.add_patch(Wedge((0, 0), 1.0, 0, 180, width=0.28, facecolor="#33415E"))
# 值弧（绿，超100%仍用绿）
val_angle = 180 - min(rate, SCALE) / SCALE * 180
ax.add_patch(Wedge((0, 0), 1.0, val_angle, 180, width=0.28, facecolor=C_GREEN))
# 目标线（橙，标记100%）
ax.add_patch(Wedge((0, 0), 1.0, 59.8, 60.2, width=0.28, facecolor=C_ORANGE))
# 刻度 0~150
for k in range(0, SCALE + 1, 25):
    ang = np.deg2rad(180 - k * 180 / SCALE)
    ax.plot([0.86 * np.cos(ang), 0.92 * np.cos(ang)], [0.86 * np.sin(ang), 0.92 * np.sin(ang)],
            color=FG_TICK, lw=1.2)
    ax.text(1.22 * np.cos(ang), 1.22 * np.sin(ang), f"{k}%", ha="center", va="center",
            fontsize=9, color=FG_TICK)
# 指针
needle_ang = np.deg2rad(180 - min(rate, SCALE) / SCALE * 180)
ax.plot([0, 0.72 * np.cos(needle_ang)], [0, 0.72 * np.sin(needle_ang)], color="#FFFFFF", lw=3)
ax.add_patch(Circle((0, 0), 0.055, color="#FFFFFF"))
ax.text(0, -0.22, f"达成率 {rate:.1f}%", ha="center", fontsize=20, fontweight="bold",
        color=C_GREEN)
ax.text(0, -0.42, f"12月1-9日实际 {dec/10000:.1f} 万英镑 / 进度目标 {target/10000:.1f} 万英镑",
        ha="center", fontsize=9.5, color=FG_SUB)
ax.set_xlim(-1.45, 1.45)
ax.set_ylim(-0.6, 1.45)
set_title(ax, "图14  12月销售进度达成仪表盘",
          "年末冲刺开局顺利，前9天进度达成率141.1%，远超时间进度")
save(fig, "fig14_仪表盘_12月目标达成.png")

# ========== fig15 子弹图：Q4 vs 目标 vs 平均线 ==========
q_all = sales.groupby("Quarter")["Amount"].sum() / 10000
q4 = q_all.get("2011Q4", 0)
q_mean = q_all.iloc[:-1].mean()
q_target = q_all.get("2011Q3", 0) * 1.05
fig, ax = plt.subplots(figsize=(9, 3.2))
fig.patch.set_facecolor(BG)
maxv = max(q4, q_target, q_mean) * 1.15
# 背景三档
ax.barh([0], [maxv], height=0.52, color="#33415E", zorder=1)
ax.barh([0], [q_mean * 1.15], height=0.52, color="#3E5175", zorder=2)
ax.barh([0], [q_mean], height=0.52, color="#4A5D85", zorder=3)
# 实际值条
ax.barh([0], [q4], height=0.24, color=C_MAIN, zorder=4)
# 目标线
ax.axvline(q_target, color=C_RED, lw=2.5, zorder=5)
ax.text(q_target, 0.34, f"目标 {q_target:,.0f}", color=C_RED, fontsize=9, ha="center",
        fontweight="bold")
ax.text(q4 + maxv * 0.01, 0, f"实际 {q4:,.0f}", va="center", fontsize=10, color=FG_LABEL,
        fontweight="bold")
ax.text(q_mean, -0.34, f"季度均值 {q_mean:,.0f}", color=FG_SUB, fontsize=8.5, ha="center")
ax.set_yticks([])
ax.set_xlabel("销售额（万英镑）", color=FG_TICK)
ax.set_xlim(0, maxv)
ax.set_ylim(-0.5, 0.58)
ax.tick_params(colors=FG_TICK, labelsize=9)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color(GRID)
set_title(ax, "图15  2011Q4销售额子弹图",
          "Q4实际317.0万英镑已击穿目标线（Q3×1.05≈256.3万），数据截至12月9日")
save(fig, "fig15_子弹图_Q4销售.png")

print("\n第一批图（fig04-fig15）全部完成！")
