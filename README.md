# 基于UCI电商数据的客户价值与需求预测

《商业数据分析》期末大作业

## 一、项目简介

本项目使用英国一家在线零售商的真实交易数据（UCI Online Retail 数据集），完成了从
**数据合规获取 → 清洗治理 → 商业模型分析 → Python可视化 → 交互式大屏** 的完整流程：

- 绘制 **3 张** 数据清洗前后对比图，直观展示清洗对数据质量的改善
- 复现《Excel数据可视化——从图表到数据大屏》第二章 **12 种** 图表模板（Matplotlib）
- 应用 **5 类商业分析模型**：帕累托/ABC、RFM八分类、同期群留存、Apriori关联规则、Holt-Winters需求预测
- 用 Pyecharts 搭建 **1 个交互式销售分析大屏**（8 个组件，含时间轴联动）
- 全部图表与大屏均由 Python 代码生成，未使用任何 BI 软件

## 二、数据来源与合规声明

| 项目 | 内容 |
|---|---|
| 数据源名称 | UCI Machine Learning Repository — Online Retail 数据集 |
| 数据集页面 | https://archive.ics.uci.edu/dataset/352/online+retail |
| 下载地址 | https://archive.ics.uci.edu/static/public/352/online+retail.zip |
| 获取方式 | 白名单方式①：数据源官方提供的一次性下载文件（ZIP内含XLSX），未使用任何爬虫技术 |
| 获取日期 | 2026年11月5日 |
| 授权/License | Creative Commons Attribution 4.0 International (CC BY 4.0)，允许在署名前提下自由使用 |
| 数据规模 | 原始 541,909 条交易记录，清洗后 522,529 条（远超课程要求的500条） |
| 数据内容 | 英国某在线零售商 2010-12-01 至 2011-12-09 的全部交易流水，覆盖 38 个国家/地区、3,909 种商品、4,335 位注册客户 |

## 三、目录结构

```
商业数据分析大作业/
├── data/
│   ├── raw/                    # 原始数据（官方ZIP + Online Retail.xlsx）
│   └── clean/                  # 清洗后数据（CSV + SQLite + 清洗日志 + 模型结果）
├── code/                       # 全部分析代码（按步骤编号，按顺序运行即可）
│   ├── step1_load_clean.py     # 读取原始数据 + 清洗治理 + 拆维度表
│   ├── step1b_clean_compare.py # 数据清洗前后对比图 fig01–fig03
│   ├── step2_eda_figs.py       # 模板复现图 fig04–fig15
│   ├── step3_models.py         # 商业模型 + 业务图 fig16–fig22
│   └── step4_dashboard.py      # Pyecharts 交互式大屏
├── fig/                        # 全部图表（fig01–fig23，200dpi）
├── dashboard/                  # 销售分析大屏.html（浏览器打开即可交互）
│   └──MP4.zip                  # 交互大屏演示视频
├── docs/                       # 期末论文
├── requirements.txt            # 依赖清单
└── run_all.py                  # 一键复现入口
```

## 四、复现步骤

```bash
pip install -r requirements.txt
python run_all.py
```

运行完后：
- `fig/` 下生成 fig01–fig22 共 22 张图（fig23 为大屏截图）
- `dashboard/销售分析大屏.html` 用浏览器打开即可查看交互式大屏
  （拖动底部时间轴可切换月份，趋势图支持缩放滑块）

## 五、图表索引

| 编号 | 图名 | 对应模板/模型 |
|---|---|---|
| fig01 | 数据清洗流水线 | 数据治理 |
| fig02 | 清洗前后数据质量对比 | 数据治理 |
| fig03 | 清洗前后单价分布对比 | 数据治理 |
| fig04 | 渐变柱形图：国家销售额Top10 | 模板1 |
| fig05 | 带均值柱形图：月度销售额 | 模板2 |
| fig06 | 标注柱形图：商品销售额Top10 | 模板4 |
| fig07 | 层叠柱形图：Top4国家季度销售额 | 模板5 |
| fig08 | 蝴蝶图：英国本土vs海外月度对比 | 模板6 |
| fig09 | 甘特图：Top10客户活跃期 | 模板10 |
| fig10 | 平滑折线图：周销售额走势 | 模板11 |
| fig11 | 对比折线图：Top3国家月度走势 | 模板13 |
| fig12 | 单值圆环图：英国市场占比 | 模板14 |
| fig13 | 南丁格尔圆环图：海外Top8国家 | 模板20 |
| fig14 | 仪表盘图：12月目标达成 | 模板22 |
| fig15 | 子弹图：Q4销售额 | 模板25 |
| fig16 | 帕累托图：商品ABC分类 | 帕累托/ABC模型 |
| fig17 | RFM气泡图 | RFM模型 |
| fig18 | RFM八分类人数vs金额 | RFM模型 |
| fig19 | 同期群留存热力图 | 同期群分析 |
| fig20 | 关联规则散点图 | Apriori模型 |
| fig21 | Top10关联规则条形图 | Apriori模型 |
| fig22 | Holt-Winters预测（95%置信区间） | 预测模型 |
| fig23 | 交互式大屏截图 | Pyecharts大屏 |

## 六、分工说明

本人独立完成全部工作：数据获取与清洗、模型构建、图表绘制、大屏开发、论文撰写。

## 七、AI辅助说明

开发过程中使用 AI 编程助手辅助调试代码报错、优化图表样式细节，具体披露见论文第 7.3 节。
全部代码均经过本人逐行理解与实测运行，分析结论由本人核对数据后得出。
