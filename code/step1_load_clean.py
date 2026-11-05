# -*- coding: utf-8 -*-
"""
第1步：读取原始数据 + 清洗治理
数据来源：UCI Machine Learning Repository - Online Retail 数据集
官方下载地址：https://archive.ics.uci.edu/static/public/352/online+retail.zip
做的事情：
  1. 读取 xlsx 原始文件
  2. 处理缺失值、重复值、异常值
  3. 把退货单（C开头的发票）单独拆出来
  4. 拆成 订单事实表 + 商品维度表 + 客户维度表（星型结构）
  5. 导出 CSV 和 SQLite，方便后面复用
"""
import os
import pandas as pd
import numpy as np
import sqlite3

# ========== 路径设置 ==========
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根目录
RAW = os.path.join(BASE, "data", "raw", "Online Retail.xlsx")
CLEAN_DIR = os.path.join(BASE, "data", "clean")
os.makedirs(CLEAN_DIR, exist_ok=True)

print("=" * 60)
print("第1步：读取原始数据")
print("=" * 60)

# ========== 1. 读取原始数据 ==========
df = pd.read_excel(RAW)
print("原始数据形状:", df.shape)
print("字段:", list(df.columns))
print(df.head(3))
print("\n各字段缺失数量:")
print(df.isna().sum())

# 记录清洗日志，最后打印出来写进报告
log = []
log.append(f"原始记录数: {len(df)}")

# ========== 2. 基础治理 ==========
# 2.1 去重：完全重复的行直接删掉
n0 = len(df)
df = df.drop_duplicates()
log.append(f"删除完全重复行: {n0 - len(df)} 条")

# 2.2 类型统一：日期转成 datetime，文本去掉首尾空格
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
df["StockCode"] = df["StockCode"].astype(str).str.strip()
df["Description"] = df["Description"].astype(str).str.strip()

# 2.3 拆退货单：发票号以 C 开头的是取消/退货单，单独存一张表
is_return = df["InvoiceNo"].str.startswith("C")
returns = df[is_return].copy()
sales = df[~is_return].copy()
log.append(f"退货/取消单: {len(returns)} 条（单独存 returns 表）")
log.append(f"正常销售单: {len(sales)} 条")

# 2.4 剔除非商品编码：POST(邮费)、DOT、M、BANK、PADS、CRUK 等是费用或内部标记
fee_codes = ["POST", "DOT", "M", "BANK", "PADS", "CRUK", "C2", "DCGSSBOY", "DCGSSGIRL", "gift_0001"]
mask_fee = sales["StockCode"].isin(fee_codes) | sales["StockCode"].str.contains("gift", case=False, na=False)
sales = sales[~mask_fee]
log.append(f"剔除邮费/赠品等非商品记录: {mask_fee.sum()} 条")

# 2.5 异常值：数量为0或单价为0的记录没有分析价值
bad = (sales["Quantity"] <= 0) | (sales["UnitPrice"] <= 0)
sales = sales[~bad]
log.append(f"删除数量或单价<=0的异常记录: {bad.sum()} 条")

# 2.6 极端单价：单价超过10000英镑的记录明显是录入错误，做截断处理
extreme = sales["UnitPrice"] > 10000
sales = sales[~extreme]
log.append(f"删除极端单价(>10000英镑)记录: {extreme.sum()} 条")

# 2.7 商品描述缺失的用 StockCode 补上，避免后面画图出现空标签
sales["Description"] = sales["Description"].replace(["nan", "None", ""], np.nan)
sales["Description"] = sales["Description"].fillna("商品" + sales["StockCode"])

# 2.8 派生指标：销售额 = 数量 x 单价；再拆出年月日星期小时，方便趋势分析
sales["Amount"] = sales["Quantity"] * sales["UnitPrice"]
sales["YearMonth"] = sales["InvoiceDate"].dt.to_period("M").astype(str)
sales["Date"] = sales["InvoiceDate"].dt.date
sales["Year"] = sales["InvoiceDate"].dt.year
sales["Month"] = sales["InvoiceDate"].dt.month
sales["Weekday"] = sales["InvoiceDate"].dt.dayofweek  # 0=周一
sales["Hour"] = sales["InvoiceDate"].dt.hour

# 2.9 客户ID缺失说明：约1/4记录没有客户ID（游客下单）
#     销售趋势类分析保留全部记录；RFM等客户级分析只用有ID的子集
n_missing_cid = sales["CustomerID"].isna().sum()
log.append(f"销售表中客户ID缺失: {n_missing_cid} 条（游客订单，趋势分析保留，客户分析剔除）")
sales["CustomerID"] = sales["CustomerID"].astype("Int64")  # 允许空值的整数类型

# ========== 3. 拆维度表（星型结构） ==========
# 商品维度表：一个商品编码对应一条
products = (sales.groupby("StockCode")
            .agg(商品名称=("Description", lambda x: x.mode().iat[0] if len(x.mode()) else x.iloc[0]),
                 平均单价=("UnitPrice", "mean"),
                 总销量=("Quantity", "sum"),
                 总销售额=("Amount", "sum"))
            .reset_index())
products.columns = ["StockCode", "Description", "AvgPrice", "TotalQty", "TotalAmount"]

# 客户维度表：一个客户一条
cust = sales.dropna(subset=["CustomerID"])
customers = (cust.groupby("CustomerID")
             .agg(国家=("Country", lambda x: x.mode().iat[0] if len(x.mode()) else x.iloc[0]),
                  首单日期=("InvoiceDate", "min"),
                  末单日期=("InvoiceDate", "max"),
                  订单数=("InvoiceNo", "nunique"),
                  消费总额=("Amount", "sum"))
             .reset_index())
customers.columns = ["CustomerID", "Country", "FirstDate", "LastDate", "OrderCount", "TotalAmount"]

# ========== 4. 导出 ==========
sales.to_csv(os.path.join(CLEAN_DIR, "sales_clean.csv"), index=False, encoding="utf-8-sig")
returns.to_csv(os.path.join(CLEAN_DIR, "returns.csv"), index=False, encoding="utf-8-sig")
products.to_csv(os.path.join(CLEAN_DIR, "dim_products.csv"), index=False, encoding="utf-8-sig")
customers.to_csv(os.path.join(CLEAN_DIR, "dim_customers.csv"), index=False, encoding="utf-8-sig")

db = sqlite3.connect(os.path.join(CLEAN_DIR, "retail.db"))
sales.to_sql("sales", db, if_exists="replace", index=False)
returns.to_sql("returns", db, if_exists="replace", index=False)
products.to_sql("dim_products", db, if_exists="replace", index=False)
customers.to_sql("dim_customers", db, if_exists="replace", index=False)
db.close()

# ========== 5. 清洗日志输出 ==========
log.append(f"清洗后销售主表: {len(sales)} 条")
log.append(f"商品数: {len(products)} | 客户数: {len(customers)}")
log.append(f"时间范围: {sales['InvoiceDate'].min()} ~ {sales['InvoiceDate'].max()}")
log.append(f"覆盖国家/地区数: {sales['Country'].nunique()}")

print("\n" + "=" * 60)
print("清洗日志（写报告用）:")
print("=" * 60)
for line in log:
    print(" -", line)

# 把日志存成文本文件，写报告时直接引用数字
with open(os.path.join(CLEAN_DIR, "clean_log.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log))
print("\n清洗完成，文件已存到 data/clean/")
