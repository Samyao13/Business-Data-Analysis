# -*- coding: utf-8 -*-
"""
第4步：交互式销售数据驾驶舱（浅色 BI 风格）
参照"驾驶舱"设计：顶部标题栏 + 时间轴滑杆 + 5张KPI卡(含环比涨跌) + 摘要结论条
+ 主图区(组合图 / 正负柱 / 堆叠柱 / 多系列折线 / 占比图)，时间轴全局联动 + 自动播放。
输出：dashboard/销售分析大屏.html
"""
import os
import json
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "dashboard")
os.makedirs(OUT, exist_ok=True)

sales = pd.read_csv(os.path.join(BASE, "data", "clean", "sales_clean.csv"),
                    parse_dates=["InvoiceDate"])

# ==================== 数据准备 ====================
months = sorted(sales["YearMonth"].unique())          # 13 个月
months_long = [f"{m[:4]}年{int(m[5:])}月" for m in months]
months_short = [m[2:].replace("-", "/") for m in months]   # "10/12"

m = sales.groupby("YearMonth").agg(
    销售额=("Amount", "sum"),
    订单数=("InvoiceNo", "nunique"),
).reindex(months).reset_index(drop=True)
m["客单价"] = m["销售额"] / m["订单数"]
m["销售额环比"] = m["销售额"].pct_change() * 100
m["订单数环比"] = m["订单数"].pct_change() * 100
m["客单价环比"] = m["客单价"].pct_change() * 100

uk = sales[sales.Country == "United Kingdom"].groupby("YearMonth")["Amount"].sum().reindex(months)
m["英国占比"] = uk.values / m["销售额"] * 100
m["英国占比变化"] = m["英国占比"].diff()
m["累计销售额"] = m["销售额"].cumsum()

# 环比（首月无 → None，用于前端显示"—"）
def safe(x):
    return None if (x is None or pd.isna(x)) else round(float(x), 1)

sales_w = [round(v / 10000, 1) for v in m["销售额"]]          # 万英镑
growth = [safe(v) for v in m["销售额环比"]]
orders = [int(v) for v in m["订单数"]]
orders_g = [safe(v) for v in m["订单数环比"]]
aov = [round(v, 0) for v in m["客单价"]]
aov_g = [safe(v) for v in m["客单价环比"]]
uk_pct = [round(v, 1) for v in m["英国占比"]]
uk_delta = [safe(v) for v in m["英国占比变化"]]
cum = [round(v / 10000, 1) for v in m["累计销售额"]]

# 最后一个月(2011-12)仅统计至12月9日，环比不可比 → 置 None
for _arr in [growth, orders_g, aov_g, uk_delta]:
    _arr[-1] = None

# 工作日 vs 周末（堆叠柱）—— 体现 B2B 特征
sales["周末"] = sales["Weekday"].isin([5, 6])
workday = sales[~sales["周末"]].groupby("YearMonth")["Amount"].sum().reindex(months).fillna(0)
weekend = sales[sales["周末"]].groupby("YearMonth")["Amount"].sum().reindex(months).fillna(0)
workday_w = [round(float(v) / 10000, 1) for v in workday]
weekend_w = [round(float(v) / 10000, 1) for v in weekend]

# 海外 Top3（多系列折线）—— 去掉英国，三条线更均衡
piv = sales.pivot_table(index="YearMonth", columns="Country",
                        values="Amount", aggfunc="sum", fill_value=0).reindex(months)
oversea3 = [("Netherlands", "荷兰", "#14b8a6"), ("EIRE", "爱尔兰", "#f59e0b"),
            ("Germany", "德国", "#8b5cf6")]
oversea3_series = []
for en, cn, color in oversea3:
    vals = [round(float(piv.loc[mo, en]) / 10000, 1) if en in piv.columns else 0 for mo in months]
    oversea3_series.append({"name": cn, "color": color, "data": vals})

# 英国 vs 海外 占比（100% 堆叠）
uk_ratio = [round(v, 1) for v in m["英国占比"]]
oversea_ratio = [round(100 - v, 1) for v in uk_ratio]

# 每月摘要（结论条，含彩色高亮关键词）
HIGHLIGHTS = {2: "全年最低、传统淡季", 11: "圣诞备货季冲上全年峰值", 12: "仅统计至 12月9日"}
def make_summary(i):
    mo = months_long[i]
    trend = ""
    if i == 0:
        trend = "数据起点月"
    elif i == 12:
        trend = "仅统计至 12月9日"
    else:
        g = growth[i]
        trend = (f'环比 <b class="up">+{g:.0f}%</b>' if g >= 0
                 else f'环比 <b class="down">{g:.0f}%</b>')
    note = HIGHLIGHTS.get(i, "")
    note_html = f'，<b class="hl">{note}</b>' if note else ""
    return (f'<span class="mo">{mo}</span> 销售额 <b class="num">{sales_w[i]:.0f}万</b> 英镑（{trend}），'
            f'订单 <b class="num">{orders[i]:,}</b> 单、客单价 <b class="num">£{aov[i]:.0f}</b>，'
            f'英国市场占比 <b class="num">{uk_pct[i]:.1f}%</b>{note_html}。')
summary = [make_summary(i) for i in range(len(months))]

DATA = {
    "months": months,
    "months_long": months_long,
    "months_short": months_short,
    "sales_w": sales_w,
    "growth": growth,
    "orders": orders,
    "orders_g": orders_g,
    "aov": aov,
    "aov_g": aov_g,
    "uk_pct": uk_pct,
    "uk_delta": uk_delta,
    "cum": cum,
    "workday": workday_w,
    "weekend": weekend_w,
    "oversea3": oversea3_series,
    "uk_ratio": uk_ratio,
    "oversea_ratio": oversea_ratio,
    "summary": summary,
    "default_idx": 11,   # 默认选中 2011-11（峰值月）
}

# ==================== HTML 模板 ====================
HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>英国在线零售 · 销售数据驾驶舱</title>
<script src="./echarts.min.js"></script>
<style>
  * { box-sizing: border-box; }
  body {
    background: #eef1f6; margin: 0; padding: 20px;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif; color: #1f2937;
  }
  .dash { max-width: 1400px; margin: 0 auto; }
  .card {
    background: #fff; border-radius: 14px;
    box-shadow: 0 2px 10px rgba(30, 60, 120, .07);
  }
  /* 顶部标题栏 */
  .header { display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; }
  .title-area { display: flex; align-items: center; gap: 14px; }
  .logo {
    width: 46px; height: 46px; border-radius: 12px; flex: 0 0 auto;
    background: linear-gradient(135deg, #3b82f6, #14b8a6);
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; color: #fff;
  }
  h1 { font-size: 21px; margin: 0; letter-spacing: 1px; }
  .subtitle { font-size: 12px; color: #8a94a6; margin-top: 4px; }
  .controls { display: flex; align-items: center; gap: 10px; }
  .ctrl-label { font-size: 13px; color: #5b6472; }
  .cur-month {
    font-size: 16px; font-weight: 700; color: #3b82f6; min-width: 86px; text-align: center;
  }
  .btn {
    border: none; border-radius: 9px; padding: 8px 16px; cursor: pointer;
    font-size: 13px; font-weight: 600; background: #3b82f6; color: #fff;
    transition: background .15s;
  }
  .btn:hover { background: #2f6fe0; }
  .btn.pause { background: #f59e0b; }
  /* 时间轴 */
  .timeline-bar { margin-top: 14px; padding: 12px 24px 10px; }
  .tl-row { display: flex; align-items: center; gap: 14px; }
  .tl-ends { font-size: 12px; color: #8a94a6; }
  input[type=range] { flex: 1; accent-color: #3b82f6; height: 4px; }
  /* KPI */
  .kpi-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-top: 14px; }
  .kpi { padding: 16px 14px; text-align: center; }
  .kpi-lab { font-size: 12px; color: #8a94a6; margin-bottom: 8px; }
  .kpi-val { font-size: 26px; font-weight: 700; color: #1f2937; }
  .kpi-val small { font-size: 14px; color: #5b6472; font-weight: 500; }
  .kpi-delta { font-size: 12px; margin-top: 6px; font-weight: 600; }
  .up { color: #e5484d; }
  .down { color: #12a36f; }
  .flat { color: #9aa3b2; }
  /* 摘要结论条 */
  .summary {
    margin-top: 14px; padding: 13px 18px; font-size: 14px; color: #374151;
    border-left: 4px solid #3b82f6; line-height: 1.7;
  }
  .summary .mo { font-weight: 700; color: #3b82f6; }
  .summary .num { color: #1f2937; }
  .summary .hl { color: #f59e0b; }
  .summary .up { color: #e5484d; }
  .summary .down { color: #12a36f; }
  /* 主图区 */
  .grid-main { display: grid; grid-template-columns: 2fr 1fr; gap: 14px; margin-top: 14px; }
  .grid-sub { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; margin-top: 14px; }
  .cell { padding: 14px 16px 10px; }
  .chart-title { font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 4px; }
  .chart-title small { font-weight: 400; color: #9aa3b2; font-size: 11px; margin-left: 6px; }
  #c1, #c2 { height: 320px; }
  #c3, #c4, #c5 { height: 300px; }
  .foot { text-align: center; color: #a5adbb; font-size: 12px; margin: 16px 0 4px; }
</style>
</head>
<body>
<div class="dash">
  <!-- 顶部标题栏 -->
  <div class="card header">
    <div class="title-area">
      <div class="logo">📊</div>
      <div>
        <h1>英国在线零售 · 销售数据驾驶舱</h1>
        <div class="subtitle">2010-12 ~ 2011-12 · 13 个月 · 月度数据 · 清洗后 52.2 万条交易记录</div>
      </div>
    </div>
    <div class="controls">
      <span class="ctrl-label">当前月份</span>
      <span class="cur-month" id="curMonth">—</span>
      <button class="btn" id="playBtn" onclick="togglePlay()">▶ 播放</button>
    </div>
  </div>

  <!-- 时间轴控制条 -->
  <div class="card timeline-bar">
    <div class="tl-row">
      <span class="tl-ends">2010-12</span>
      <input type="range" id="slider" min="0" max="12" step="1" value="10">
      <span class="tl-ends">2011-12</span>
    </div>
  </div>

  <!-- KPI 卡片 -->
  <div class="kpi-row">
    <div class="card kpi">
      <div class="kpi-lab">月销售额</div>
      <div class="kpi-val"><span id="k1">—</span><small> 万£</small></div>
      <div class="kpi-delta" id="d1">—</div>
    </div>
    <div class="card kpi">
      <div class="kpi-lab">订单数</div>
      <div class="kpi-val"><span id="k2">—</span><small> 单</small></div>
      <div class="kpi-delta" id="d2">—</div>
    </div>
    <div class="card kpi">
      <div class="kpi-lab">客单价</div>
      <div class="kpi-val"><span id="k3">—</span><small> £</small></div>
      <div class="kpi-delta" id="d3">—</div>
    </div>
    <div class="card kpi">
      <div class="kpi-lab">英国市场占比</div>
      <div class="kpi-val"><span id="k4">—</span><small> %</small></div>
      <div class="kpi-delta" id="d4">—</div>
    </div>
    <div class="card kpi">
      <div class="kpi-lab">累计销售额</div>
      <div class="kpi-val"><span id="k5">—</span><small> 万£</small></div>
      <div class="kpi-delta flat" id="d5">自 2010-12 累计</div>
    </div>
  </div>

  <!-- 摘要结论条 -->
  <div class="card summary" id="summary">—</div>

  <!-- 主图区 第一行 -->
  <div class="grid-main">
    <div class="card cell">
      <div class="chart-title">月度销售额与环比增速 <small>柱 = 销售额(万£) · 线 = 环比增速(%)</small></div>
      <div id="c1"></div>
    </div>
    <div class="card cell">
      <div class="chart-title">环比增长动能 <small>正=增长 · 负=回落</small></div>
      <div id="c2"></div>
    </div>
  </div>
  <!-- 主图区 第二行 -->
  <div class="grid-sub">
    <div class="card cell">
      <div class="chart-title">工作日 vs 周末销售结构 <small>堆叠柱 · 周末占比低=批发特征</small></div>
      <div id="c3"></div>
    </div>
    <div class="card cell">
      <div class="chart-title">海外 Top3 国家月度走势 <small>多系列折线 · 万£</small></div>
      <div id="c4"></div>
    </div>
    <div class="card cell">
      <div class="chart-title">英国 vs 海外占比 <small>100% 堆叠</small></div>
      <div id="c5"></div>
    </div>
  </div>

  <div class="foot">拖动时间轴或点击「播放」按钮，各图表与指标卡将随月份联动刷新</div>
</div>

<script>
const DATA = __DATA__;
const M = DATA.months_short;
const N = M.length;
const RED = '#e5484d', GREEN = '#12a36f', BLUE = '#3b82f6', ORANGE = '#f59e0b', PURPLE = '#8b5cf6';

// ==================== 图表初始化 ====================
const c1 = echarts.init(document.getElementById('c1'));
const c2 = echarts.init(document.getElementById('c2'));
const c3 = echarts.init(document.getElementById('c3'));
const c4 = echarts.init(document.getElementById('c4'));
const c5 = echarts.init(document.getElementById('c5'));
const charts = [c1, c2, c3, c4, c5];

const axisLabel = { color: '#8a94a6', fontSize: 11 };
const splitLine = { lineStyle: { color: '#eef1f6' } };
const tooltip = { trigger: 'axis', axisPointer: { type: 'shadow' } };

// 图1：组合图（柱 + 折线双轴）
c1.setOption({
  animation: false,
  color: [BLUE, ORANGE],
  tooltip: { trigger: 'axis' },
  legend: { data: ['销售额', '环比增速'], right: 10, top: 0, itemWidth: 14, itemHeight: 9, textStyle: { fontSize: 11 } },
  grid: { left: 48, right: 52, top: 34, bottom: 28 },
  xAxis: { type: 'category', data: M, axisLabel: Object.assign({}, axisLabel, { rotate: 30 }) },
  yAxis: [
    { type: 'value', name: '万£', axisLabel, splitLine, nameTextStyle: { color: '#9aa3b2' } },
    { type: 'value', name: '%', axisLabel, splitLine: { show: false }, nameTextStyle: { color: '#9aa3b2' } }
  ],
  series: [
    { name: '销售额', type: 'bar', data: DATA.sales_w, barMaxWidth: 22, itemStyle: { color: BLUE, borderRadius: [4,4,0,0] } },
    { name: '环比增速', type: 'line', yAxisIndex: 1, data: DATA.growth, smooth: true,
      symbol: 'circle', symbolSize: 6, lineStyle: { width: 2.5, color: ORANGE }, itemStyle: { color: ORANGE } }
  ]
});

// 图2：正负柱（环比增长动能）
c2.setOption({
  animation: false,
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: 44, right: 16, top: 24, bottom: 28 },
  xAxis: { type: 'category', data: M, axisLabel: Object.assign({}, axisLabel, { rotate: 30 }) },
  yAxis: { type: 'value', name: '%', axisLabel, splitLine, nameTextStyle: { color: '#9aa3b2' } },
  series: [{
    type: 'bar', barMaxWidth: 22,
    data: DATA.growth.map(v => v === null ? { value: 0, itemStyle: { color: '#d1d5db' } }
        : { value: v, itemStyle: { color: v >= 0 ? RED : GREEN, borderRadius: v >= 0 ? [4,4,0,0] : [0,0,4,4] } })
  }]
});

// 图3：工作日 vs 周末 堆叠柱
c3.setOption({
  animation: false,
  color: [BLUE, ORANGE],
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  legend: { right: 6, top: 0, itemWidth: 13, itemHeight: 9, textStyle: { fontSize: 11 } },
  grid: { left: 44, right: 12, top: 30, bottom: 26 },
  xAxis: { type: 'category', data: M, axisLabel: Object.assign({}, axisLabel, { rotate: 30 }) },
  yAxis: { type: 'value', name: '万£', axisLabel, splitLine, nameTextStyle: { color: '#9aa3b2' } },
  series: [
    { name: '工作日', type: 'bar', stack: 's', data: DATA.workday, barMaxWidth: 24, itemStyle: { color: BLUE } },
    { name: '周末', type: 'bar', stack: 's', data: DATA.weekend, barMaxWidth: 24, itemStyle: { color: ORANGE } }
  ]
});

// 图4：海外 Top3 国家多系列折线
c4.setOption({
  animation: false,
  color: DATA.oversea3.map(s => s.color),
  tooltip: { trigger: 'axis' },
  legend: { right: 6, top: 0, itemWidth: 13, itemHeight: 9, textStyle: { fontSize: 11 } },
  grid: { left: 44, right: 16, top: 30, bottom: 26 },
  xAxis: { type: 'category', data: M, axisLabel: Object.assign({}, axisLabel, { rotate: 30 }) },
  yAxis: { type: 'value', name: '万£', axisLabel, splitLine, nameTextStyle: { color: '#9aa3b2' } },
  series: DATA.oversea3.map(s => ({ name: s.name, type: 'line', data: s.data, smooth: true, symbolSize: 5,
    lineStyle: { width: 2 } }))
});

// 图5：英国 vs 海外占比（100% 堆叠）
c5.setOption({
  animation: false,
  color: [BLUE, '#cbd5e1'],
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
    valueFormatter: v => v == null ? '-' : v + '%' },
  legend: { right: 6, top: 0, itemWidth: 13, itemHeight: 9, textStyle: { fontSize: 11 } },
  grid: { left: 44, right: 16, top: 30, bottom: 26 },
  xAxis: { type: 'category', data: M, axisLabel: Object.assign({}, axisLabel, { rotate: 30 }) },
  yAxis: { type: 'value', max: 100, axisLabel, splitLine, nameTextStyle: { color: '#9aa3b2' } },
  series: [
    { name: '英国', type: 'bar', stack: 'r', data: DATA.uk_ratio, barMaxWidth: 24,
      itemStyle: { color: BLUE, borderRadius: [0,0,0,0] } },
    { name: '海外', type: 'bar', stack: 'r', data: DATA.oversea_ratio, barMaxWidth: 24,
      itemStyle: { color: '#cbd5e1' } }
  ]
});

// ==================== 联动更新 ====================
function fmtDelta(v, unit) {
  if (v === null || v === undefined) return '<span class="flat">— 无上期数据</span>';
  if (v >= 0) return '<span class="up">▲ 环比 +' + v.toFixed(1) + unit + '</span>';
  return '<span class="down">▼ 环比 ' + v.toFixed(1) + unit + '</span>';
}

function update(idx) {
  document.getElementById('curMonth').textContent = DATA.months_long[idx];
  document.getElementById('k1').textContent = DATA.sales_w[idx].toFixed(0);
  document.getElementById('k2').textContent = DATA.orders[idx].toLocaleString();
  document.getElementById('k3').textContent = DATA.aov[idx].toFixed(0);
  document.getElementById('k4').textContent = DATA.uk_pct[idx].toFixed(1);
  document.getElementById('k5').textContent = DATA.cum[idx].toFixed(0);
  document.getElementById('d1').innerHTML = fmtDelta(DATA.growth[idx], '%');
  document.getElementById('d2').innerHTML = fmtDelta(DATA.orders_g[idx], '%');
  document.getElementById('d3').innerHTML = fmtDelta(DATA.aov_g[idx], '%');
  document.getElementById('d4').innerHTML = fmtDelta(DATA.uk_delta[idx], 'pp');
  document.getElementById('summary').innerHTML = DATA.summary[idx];

  // 图表联动：显示当前月 tooltip + 组合图竖线标记
  charts.forEach(c => c.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: idx }));
  c1.setOption({ series: [{ markLine: { silent: true, symbol: 'none',
      lineStyle: { color: ORANGE, width: 2, type: 'dashed' },
      label: { show: false }, data: [{ xAxis: M[idx] }] } }] });
  // 正负柱当前月加边框强调
  c2.dispatchAction({ type: 'downplay', seriesIndex: 0 });
  c2.dispatchAction({ type: 'highlight', seriesIndex: 0, dataIndex: idx });
}

// ==================== 时间轴 + 播放 ====================
const slider = document.getElementById('slider');
slider.addEventListener('input', () => update(+slider.value));

let playing = false, timer = null;
function togglePlay() {
  playing = !playing;
  const btn = document.getElementById('playBtn');
  btn.textContent = playing ? '⏸ 暂停' : '▶ 播放';
  btn.classList.toggle('pause', playing);
  if (playing) {
    timer = setInterval(() => {
      let next = (+slider.value + 1) % N;
      slider.value = next;
      update(next);
    }, 1600);
  } else {
    clearInterval(timer);
  }
}

// 初始渲染
update(DATA.default_idx);
slider.value = DATA.default_idx;
window.addEventListener('resize', () => charts.forEach(c => c.resize()));
</script>
</body>
</html>
"""

# ==================== 注入数据并写出 ====================
html = HTML.replace("__DATA__", json.dumps(DATA, ensure_ascii=False))
out_html = os.path.join(OUT, "销售分析大屏.html")
with open(out_html, "w", encoding="utf-8") as f:
    f.write(html)
print("大屏已生成:", out_html)
print("默认月份:", months_long[DATA["default_idx"]],
      "| 峰值月销售额", round(sales_w[DATA["default_idx"]]), "万£")
