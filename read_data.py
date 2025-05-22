"""
將VBA轉為python作業流程
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import openpyxl

from matplotlib import rcParams
rcParams['font.family'] = 'Microsoft JhengHei'
#%%
#sheet_cost = pd.read_excel(file_path,sheet_name="達成年成本資料(112成本參考)")
#sheet_supply = pd.read_excel(file_path,sheet_name="達成年供需圖")

def paste_cost_data(file_path):
    # 讀取 A:F, AN, AO 欄資料，從第 3 列開始，共 601 筆
    df = pd.read_excel(
        file_path,
        sheet_name="達成年成本資料(112成本參考)",
        usecols="A:F,AN,AO",
        skiprows=2,
        nrows=601,
        engine="openpyxl")
    core_data = df.iloc[:, :6]              # A:F
    col_an = df.iloc[:, 6]                  # AN → 115供電整理
    col_ao = df.iloc[:, 7]                  # AO → 115容量成本

    full_df = pd.concat([df.iloc[:, :6], col_an, col_ao], axis=1)

    return full_df

def get_supply_data(file_path):
    # 讀取民間競爭者供給資料
    df_platform = pd.read_excel(file_path, sheet_name="達成年供需圖", usecols="O,P,R", skiprows=11, nrows=14)
    # 移除不需要的欄位（單位欄）
    df_platform.columns = ["電廠", "容量成本", "供電容量"]
    # 容量成本轉換為實際金額（萬元 → 元）
    df_platform["容量成本"] = df_platform["容量成本"] * 10000

    return df_platform

def apply_total_supply(df_main, df_platform):
    # 全台學理總供給
    return df_main.copy(), df_platform.copy()

def apply_taipower_only(year, df_main, df_platform):
    # 純台電供給
    df_main_cleaned = df_main.copy()
    # 500:把電力交易平台的供給資料拿掉
    df_main_cleaned.loc[500:, [f"{year}供電整理", f"{year}容量成本"]] = np.nan
    df_platform_cleaned = df_platform.copy()
    df_platform_cleaned[["容量成本", "供電容量"]] = np.nan
    return df_main_cleaned, df_platform_cleaned

def exclude_range(year, df_main, df_platform, clear_supply=np.nan, clear_cost=np.nan, platform_start=np.nan, platform_end=np.nan):
    # 通用排除範圍處理
    df_main_result = df_main.copy()
    if clear_supply:
        df_main_result.loc[clear_supply[0]:clear_supply[1], f"{year}供電整理"] = np.nan
    if clear_cost:
        df_main_result.loc[clear_cost[0]:clear_cost[1], f"{year}容量成本"] = np.nan

    df_platform_result = df_platform.copy()
    if platform_start is not None and platform_end is not None:
        df_platform_result.loc[platform_start:platform_end, ["容量成本", "供電容量"]] = np.nan

    return df_main_result, df_platform_result


def exclude_platform_all(year,df_main, df_platform):
    # 排除平台業者
    # AG502:AH514 → 容量成本+供電整理 → index 500~512
    return exclude_range(year,df_main, df_platform, clear_supply=(500, 512), clear_cost=(500, 512), platform_start=0, platform_end=12)


def exclude_platform_storage(year,df_main, df_platform):
    # 排除平台儲能
    # AG502:AH512 → 容量成本+供電整理 → index 500~510
    return exclude_range(year,df_main, df_platform, clear_supply=(500, 510), clear_cost=(500, 510), platform_start=0, platform_end=10)


def exclude_platform_cogen(year,df_main, df_platform):
    # 排除平台汽電
    # AG513 → 只清容量成本 → index 511
    return exclude_range(year,df_main, df_platform, clear_supply=(511, 511), clear_cost=(511, 511), platform_start=11, platform_end=11)


def exclude_platform_demand(year,df_main, df_platform):
    # 排除平台需量
    # AH514 → 只清供電整理 → index 512
    return exclude_range(year,df_main, df_platform, clear_supply=(512, 512), clear_cost=(512, 512), platform_start=12, platform_end=12)


def exclude_platform_cogen_demand(year,df_main, df_platform):
    # 排除平台汽電需量
    # AG513:AH514 → 清容量成本 index 511 + 供電整理 index 512
    return exclude_range(year,df_main, df_platform, clear_cost=(511, 512), clear_supply=(511, 512), platform_start=11, platform_end=12)


def exclude_private_commitments(year,df_main, df_platform):
    # 排除民間義務者
    # AG515:AH601 → 清容量成本+供電整理 → index 513~599
    return exclude_range(year,df_main, df_platform, clear_cost=(513, 599), clear_supply=(513, 599))

def get_demand_value(year, file_path, demand_mode):
    df_demand = pd.read_excel(file_path, sheet_name="備用需求量(舊法114_117)", header=None)

    # 之後要改，不同年對應到不同index
    if demand_mode == "台電需求":
        return df_demand.iloc[3, 1+int(year)-114]  # B4
    elif demand_mode == "全國需求":
        return df_demand.iloc[2, 1+int(year)-114]  # B3
    else:
        raise ValueError("demand_mode must be '台電需求' or '全國需求'")
    
    

def sorted_data(year, df_main):
    """
    根據 AI 欄（容量成本 / 10000，即萬元）做排序，
    並根據排序後的供電整理欄做累積總和（cumsum）。
    不排除成本為 0 的資料。
    """
    df_plot = df_main.copy()

    # 僅排除 NaN，保留容量成本 = 0 的資料
    df_plot = df_plot.dropna(subset=[f"{year}容量成本", f"{year}供電整理"])

    # AI 欄：容量成本（萬元）
    df_plot["容量成本_萬元"] = df_plot[f"{year}容量成本"] / 10000

    # 根據容量成本（萬元）排序
    df_plot = df_plot.sort_values(by="容量成本_萬元", ascending=True).reset_index(drop=True)

    # 累積供電容量
    df_plot["容量累積"] = df_plot[f"{year}供電整理"].cumsum()

    return df_plot.drop(columns=["容量成本_萬元"])

def plot_supply_scatter(year, df_plot, df_demand=None, fig=None, ax=None, scatter_target="ax1"):
    if fig is None or ax is None:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 10), dpi=150, gridspec_kw={'height_ratios': [2, 1]})
    else:
        ax1, ax2 = ax
    fig.subplots_adjust(hspace=0.3)

    threshold = df_plot[f"{year}容量成本"].quantile(0.995)
    df_plot = df_plot[df_plot[f"{year}容量成本"] <= threshold]

    x = df_plot["容量累積"]
    y = df_plot[f"{year}容量成本"] / 10000  # 換成「萬元」

    # ===== ax1 全圖 =====
    for i in range(len(x) - 1):
        ax1.plot([x[i], x[i + 1]], [y[i], y[i]], color='blue', linestyle='-', linewidth=2)
        ax1.plot([x[i + 1], x[i + 1]], [y[i], y[i + 1]], color='blue', linestyle='--', linewidth=1)
    ax1.scatter(x, y, color='blue', s=10, alpha=0.7)
    ax1.vlines(df_demand, -500, 9000)
    ax1.set_xlim([-500, 60000])
    ax1.set_ylim([-500, 9000])
    ax1.set_ylabel("成本 (萬元)", fontsize=12)
    ax1.grid(alpha=0.5)
    ax1.tick_params(axis='both', labelsize=10)

    # ===== ax2 放大交點區段 =====
    for i in range(len(x) - 1):
        ax2.plot([x[i], x[i + 1]], [y[i], y[i]], color='blue', linestyle='-', linewidth=2)
        ax2.plot([x[i + 1], x[i + 1]], [y[i], y[i + 1]], color='blue', linestyle='--', linewidth=1)
    ax2.scatter(x, y, color='blue', s=10, alpha=0.7)
    ax2.vlines(df_demand, -500, 9000)

    x_min = df_demand - 2000
    x_max = df_demand + 2000

    for i in range(len(x) - 1):
        if x[i] <= df_demand < x[i + 1]:
            price_near_demand = y[i]
            break
    y_min = price_near_demand - 150
    y_max = price_near_demand + 150

    ax2.set_xlim([x_min, x_max])
    ax2.set_ylim([y_min, y_max])
    ax2.set_ylabel("成本 (萬元)", fontsize=12)
    ax2.set_xlabel("累積容量 (MW)", fontsize=12)
    ax2.grid(alpha=0.5)
    ax2.tick_params(axis='both', labelsize=10)

    fig.tight_layout()

    #  回傳 scatter 點（互動點）畫在 ax1 或 ax2
    if scatter_target == "ax1":
        scatter = ax1.scatter(x, y, s=60, color='red', alpha=0.001, picker=5)
    else:
        scatter = ax2.scatter(x, y, s=60, color='red', alpha=0.001, picker=5)
    
    # 找交點
    x_cross = df_demand
    for i in range(len(x) - 1):
        if x[i] <= x_cross < x[i + 1]:
            y_cross = y[i]
            site = df_plot["電廠"].iloc[i]
            num = df_plot["機組"].iloc[i]
            site = "" if pd.isna(site) else str(site)  # 如果有nan要轉成字串
            num = "" if pd.isna(num) else str(num)

            break
    else:
        y_cross = y.iloc[-1]  # fallback

        
    
    return scatter, x.values, y.values, x_cross, y_cross, site+num # 回傳的 y 就是「萬元」

if __name__ == "__main__":
    
    filepath = "./data/備用容量估計115-117達成年V3_20250324/備用容量估計116達成年V3_20250311.xlsm"
    
    year = 116
    df_main = paste_cost_data(filepath)
    df_platform = get_supply_data(filepath)
    df_main_cleaned, df_platform_cleaned = apply_total_supply(df_main, df_platform)
    df_main_cleaned, df_platform_cleaned = exclude_platform_cogen(year,df_main, df_platform)
    df_main_sorted  = sorted_data(year,df_main_cleaned) 
    df_demand = get_demand_value(year, filepath, "台電需求")
    scatter, x, y, x_cross, y_cross, site = plot_supply_scatter(year, df_main_sorted, df_demand, fig=None, ax=None, scatter_target="ax1")
