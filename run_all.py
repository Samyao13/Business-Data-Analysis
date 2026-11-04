# -*- coding: utf-8 -*-
"""
一键复现脚本：按顺序跑完 数据清洗 -> 模板复现图 -> 模型分析图 -> 大屏
使用方法：python run_all.py
注意：step1 需要 data/raw/Online Retail.xlsx 已存在（下载方式见 README）
"""
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
steps = [
    "code/step1_load_clean.py",         # 第1步：读数据+清洗
    "code/step1b_clean_compare.py",     # 第1步补充：清洗前后对比图 fig01-fig03
    "code/step2_eda_figs.py",           # 第2步：fig04-fig15 模板复现图
    "code/step3_models.py",             # 第3步：fig16-fig22 业务模型图
    "code/step4_dashboard.py",          # 第4步：交互式大屏
]

for s in steps:
    path = os.path.join(BASE, s)
    print("\n" + "#" * 60)
    print("正在运行:", s)
    print("#" * 60)
    r = subprocess.run([sys.executable, path], cwd=BASE)
    if r.returncode != 0:
        print("出错了:", s, "—— 请检查上面的报错信息")
        sys.exit(1)

print("\n全部跑完！图表在 fig/ 文件夹，大屏在 dashboard/ 文件夹")
