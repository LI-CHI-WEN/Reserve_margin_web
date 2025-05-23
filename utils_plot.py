import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_supply_scatter(year, df_plot, df_demand):
    df_plot = df_plot.copy()
    df_plot["成本_萬元"] = df_plot[f"{year}容量成本"] / 10000
    df_plot["累積容量"] = df_plot["容量累積"]

    # 去除極端成本（PR 99.5 以上）
    cost_threshold = df_plot["成本_萬元"].quantile(0.995)
    df_plot = df_plot[df_plot["成本_萬元"] <= cost_threshold]

    df_plot["hover"] = df_plot.apply(lambda row: f"容量: {row['累積容量']:.0f} MW<br>成本: {row['成本_萬元']:.2f} 萬元<br>機組: {row['電廠'] or ''}{row['機組'] or ''}", axis=1)

    # 建立階梯線條資料（主圖與放大圖共用）
    def get_step_xy(df):
        x_vals, y_vals = [], []
        for i in range(len(df) - 1):
            x_vals += [df["累積容量"].iloc[i], df["累積容量"].iloc[i + 1]]
            y_vals += [df["成本_萬元"].iloc[i], df["成本_萬元"].iloc[i]]
        return x_vals, y_vals

    x_vals, y_vals = get_step_xy(df_plot)

    # 建立雙圖：主圖（row=1）與放大圖（row=2）
    fig = make_subplots(rows=2, cols=1, shared_xaxes=False, subplot_titles=("供給曲線（總圖）", "交點放大圖"))

    # 主圖
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines", name="", line=dict(color="blue")), row=1, col=1)  # 階梯上的點
    fig.add_trace(go.Scatter(x=df_plot["累積容量"], y=df_plot["成本_萬元"], mode="markers", text=df_plot["hover"],
                             hoverinfo="text", marker=dict(size=5, color="blue"), name="資料點"), row=1, col=1)
    fig.add_vline(x=df_demand, line_dash="dash", line_color="red", row=1, col=1)

    # 找交點
    for i in range(len(df_plot) - 1):
        if df_plot["累積容量"].iloc[i] <= df_demand < df_plot["累積容量"].iloc[i + 1]:
            y_cross = df_plot["成本_萬元"].iloc[i]
            site = str(df_plot["電廠"].iloc[i] or "")
            num = str(df_plot["機組"].iloc[i] or "")
            label = f"需求交點<br>容量: {df_demand:.0f} MW<br>價格: {y_cross:.2f} 萬元<br>機組: {site + num}"
            break
    else:
        y_cross = df_plot["成本_萬元"].iloc[-1]
        label = f"需求交點<br>容量: {df_demand:.0f} MW<br>價格: {y_cross:.2f} 萬元"

    # 放大圖範圍
    x_min = df_demand - 2000
    x_max = df_demand + 2000
    y_min = y_cross - 150
    y_max = y_cross + 150

    # 放大圖
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines", name="", line=dict(color="blue")), row=2, col=1)  #階梯上的點
    fig.add_trace(go.Scatter(x=df_plot["累積容量"], y=df_plot["成本_萬元"], mode="markers", text=df_plot["hover"],
                             hoverinfo="text", marker=dict(size=5, color="blue"), name="資料點"), row=2, col=1)
    fig.add_vline(x=df_demand, line_dash="dash", line_color="red", row=2, col=1)

    cross_hover_text = f"容量: {df_demand:.0f} MW<br>價格: {y_cross:.2f} 萬元<br>機組: {site + num}"
    
    fig.add_trace(go.Scatter(
        x=[df_demand],
        y=[y_cross],
        mode="markers+text",
        marker=dict(size=10, color="red"),
        text=["🔺"],
        textposition="top center",
        hoverinfo="text",
        hovertext=[cross_hover_text],
        showlegend=False
    ), row=2, col=1)

    fig.update_xaxes(title_text="累積容量 (MW)", row=2, col=1, range=[x_min, x_max])
    fig.update_yaxes(title_text="成本 (萬元)", row=1, col=1)
    fig.update_yaxes(title_text="成本 (萬元)", row=2, col=1, range=[y_min, y_max])

    fig.update_layout(
        height=800,
        title_text="📈 電力供給曲線（含需求交點放大區）",
        hovermode="closest",
        showlegend=False
    )

    return fig
