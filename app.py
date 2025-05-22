import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from read_data import *
from utils_plot import plot_supply_scatter
import re

st.set_page_config(layout="wide")

st.title("📊 成本與供給資料分析工具")

uploaded_file = st.file_uploader("📂 選擇 Excel 檔案", type=["xlsx", "xls", "xlsm"])
if uploaded_file:
    df_main = paste_cost_data(uploaded_file)
    df_platform = get_supply_data(uploaded_file)
    
    match = re.search(r'(\d{3})', uploaded_file.name)
    year = match.group(1) if match else "116"  # 預設 116

    st.success(f"✅ 已載入檔案（年分：{year}）")

    supply_mode = st.radio("2️⃣ 選擇供給資料來源", ["全台供給", "台電供給"])
    if supply_mode == "台電供給":
        df_main, df_platform = apply_taipower_only(year, df_main, df_platform)
    else:
        df_main, df_platform = apply_total_supply(df_main, df_platform)

    exclusion = st.selectbox("📌 排除來源（可選）", [
        "不排除", "平台全部", "平台儲能", "平台汽電", "平台需量", "汽電+需量", "民間義務者"
    ])
    if exclusion != "不排除":
        exclude_funcs = {
            "平台全部": exclude_platform_all,
            "平台儲能": exclude_platform_storage,
            "平台汽電": exclude_platform_cogen,
            "平台需量": exclude_platform_demand,
            "汽電+需量": exclude_platform_cogen_demand,
            "民間義務者": exclude_private_commitments,
        }
        df_main, df_platform = exclude_funcs[exclusion](year, df_main, df_platform)

    demand_mode = st.radio("3️⃣ 選擇需求模式", ["台電需求", "全國需求"])
    if st.button("📈 畫互動式雙圖供給曲線"):
        df_main_sorted = sorted_data(year, df_main)
        demand_val = get_demand_value(year, uploaded_file, demand_mode)
    
        fig = plot_supply_scatter(year, df_main_sorted, demand_val)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 檢視處理後資料（前300筆）"):
            st.dataframe(df_main_sorted.head(300))

