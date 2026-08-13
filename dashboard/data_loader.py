"""
Reusable data-loading functions for the COVID Surveillance dashboard.
Centralizes access to pre-processed outputs from the analysis notebooks 
(01-04), so the Streamlit app doesn't duplicate cleaning logic inline.
"""
import pandas as pd
import geopandas as gpd
import streamlit as st

DATA_DIR = "../"  # analysis outputs live one level up, in covid_project/

@st.cache_data
def load_ratios_data() -> pd.DataFrame:
    """Load the Day 2 output: cases + testing + vaccine merged, with epi ratios."""
    df = pd.read_csv(f"{DATA_DIR}covid_with_ratios.csv", parse_dates=["Date"])
    return df

@st.cache_data
def load_state_totals() -> pd.DataFrame:
    """Load Day 5 output: per-state cumulative totals used for choropleths."""
    return pd.read_csv(f"{DATA_DIR}state_totals_for_maps.csv")

@st.cache_data
def load_geometry() -> gpd.GeoDataFrame:
    """Load the cleaned, name-matched India state boundaries (Day 5)."""
    return gpd.read_file(f"{DATA_DIR}india_states_cleaned.geojson")

@st.cache_data
def get_national_daily_series(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate state-day data into a national daily new-cases series."""
    df = df.sort_values(["State", "Date"]).copy()
    df["New_Cases"] = df.groupby("State")["Confirmed"].diff()
    national = df.groupby("Date")["New_Cases"].sum().reset_index()
    return national