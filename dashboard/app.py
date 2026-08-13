
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from data_loader import load_ratios_data, load_state_totals, load_geometry, get_national_daily_series



st.set_page_config(page_title="COVID-19 India Dashboard", layout="wide")

# ---------- Sidebar navigation ----------
page = st.sidebar.radio("Navigate", ["Overview", "Risk Analysis (Maps)"])

# ---------- Load data once, shared across both pages ----------
ratios_df = load_ratios_data()
state_totals = load_state_totals()

if page == "Overview":
    st.title("COVID-19 Surveillance — National Overview")
    st.caption("Data: Ministry of Health & Family Welfare, covid19india.org (Jan 2020 - Aug 2021)")

    total_confirmed = int(state_totals['Total_Confirmed'].sum())
    total_deaths = int(state_totals['Total_Deaths'].sum())
    national_cfr = total_deaths / total_confirmed

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Confirmed Cases", f"{total_confirmed:,}")
    col2.metric("Total Deaths", f"{total_deaths:,}")
    col3.metric("National CFR", f"{national_cfr:.2%}")

    st.subheader("Daily New Cases (National)")
    national_daily = get_national_daily_series(ratios_df)
    st.line_chart(national_daily.set_index('Date')['New_Cases'])

    st.subheader("Weekly Reporting Pattern")
    st.caption("Average deviation from trend by day of week — reveals a mid-week reporting lag, not a simple weekend dip")
    
    day_order = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    effects = [-781, -7028, -857, 2175, 2199, 2405, 1888]
    
    fig_weekly, ax_weekly = plt.subplots(figsize=(7, 3))
    fig_weekly.patch.set_alpha(0)    # transparent figure background
    ax_weekly.set_facecolor('none')  # transparent axes background
    
    colors = ['#ff6b6b' if e < 0 else '#4dabf7' for e in effects]
    ax_weekly.bar(day_order, effects, color=colors)
    ax_weekly.axhline(0, color='white', linewidth=0.8)
    
    # White text/lines so the chart stays legible against Streamlit's dark theme
    ax_weekly.set_ylabel('Deviation from trend', color='white')
    ax_weekly.tick_params(colors='white')
    for spine in ax_weekly.spines.values():
        spine.set_color('white')
    
    plt.tight_layout()
    st.pyplot(fig_weekly, use_container_width=False, transparent=True)

else:
    st.title("State-Level Risk Analysis")

    metric = st.selectbox(
        "Select metric to map:",
        ["Peak_Positivity_Rate", "Total_Confirmed", "CFR", "Vaccination_Rate"],
        format_func=lambda x: {
            "Peak_Positivity_Rate": "Peak Test Positivity Rate",
            "Total_Confirmed": "Total Confirmed Cases",
            "CFR": "Case Fatality Rate",
            "Vaccination_Rate": "Vaccination Coverage Rate"
        }[x]
    )

    gdf = load_geometry()

    if metric == "Peak_Positivity_Rate":
        peak_pos = ratios_df.groupby('State')['Positivity_Rate'].max().reset_index()
        peak_pos.columns = ['NAME_1', 'Peak_Positivity_Rate']
        gdf_merged = gdf.merge(peak_pos, on='NAME_1', how='left')
    else:
        gdf_merged = gdf.merge(state_totals, left_on='NAME_1', right_on='State_Mapped', how='left')

    cmap_choice = {"Peak_Positivity_Rate": "OrRd", "Total_Confirmed": "Reds", 
                   "CFR": "PuRd", "Vaccination_Rate": "Greens"}[metric]

    fig, ax = plt.subplots(figsize=(3, 2))
    gdf_merged.plot(column=metric, cmap=cmap_choice, linewidth=0.5, edgecolor='black',
                     legend=True, missing_kwds={'color': 'lightgrey', 'label': 'No data'}, ax=ax)
    ax.axis('off')
    cbar_ax = fig.axes[-1]
    cbar_ax.tick_params(labelsize=4)
    from matplotlib.ticker import FuncFormatter
    cbar_ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))
    st.pyplot(fig)

    st.subheader("Underlying data")
    display_col = 'State_Mapped' if metric != "Peak_Positivity_Rate" else 'NAME_1'
    table_source = state_totals if metric != "Peak_Positivity_Rate" else peak_pos
    st.dataframe(
        table_source[[display_col, metric]].sort_values(metric, ascending=False).reset_index(drop=True),
        use_container_width=True
    )