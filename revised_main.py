
import streamlit as st
import pandas as pd
import kagglehub
import yfinance as yf
import matplotlib.pyplot as plt
import requests
import plotly.graph_objs as go
from datetime import datetime
from pathlib import Path

# Path to dataset folder
main_path = kagglehub.dataset_download("jacksoncrow/stock-market-dataset")
path = Path(main_path) / "stocks"
path_dict = kagglehub.dataset_download(
    "gonzalezfrancisco/full-nasdaq-stocks-data")

# Load the validation csv with company names
symbols_csv_path = Path(path_dict) / "full_financial_stocks_raw.csv"
symbols_df = pd.read_csv(symbols_csv_path)
symbols_df = symbols_df[~symbols_df["security_name"].str.contains("Associated Capital Group|ABB Ltd")]
combobox_df = symbols_df[symbols_df["security_name"].str.contains("Common Stock")]
cacib_logo = "https://upload.wikimedia.org/wikipedia/commons/7/72/Cr%C3%A9ditAgricoleCIB_logo.svg"

_, col2, _ = st.columns(3)

with col2:
    st.image(cacib_logo, use_container_width='auto')

st.write("# Python analytics project, Team Nasdaq")
st.write("""Welcome to our app :wave:!

This app allows users to look up certain stocks that are in the Nasdaq.

By filtering for the selected company, you are able to look at its past performance, get some more information about the company as well see how its stock compares to some of it's industry competitors.

It's worth noting that the data we are using from the charts come from a fixed datasource from Kaggle, and the chart data only comes up to april 2020.

Feel free to reach out to Tim or Nathan if you have any questions.

Enjoy :smiley:!""")

st.write("## Choose company to analyse")

# Create a dropdown for the end user to select a company
selected_company = st.selectbox(
    "Select company",
    combobox_df["security_name"].tolist(),
)

if selected_company:
    selected_industry = symbols_df[symbols_df["security_name"]
                                   == selected_company]["industry"].values[0]

    # Ensure the selected company is included and shown first
    selected_company_row = symbols_df[symbols_df["security_name"]
                                      == selected_company]
    top_symbols_df = symbols_df[symbols_df["industry"]
                                == selected_industry].head(4)
    top_symbols_df = pd.concat(
        [selected_company_row, top_symbols_df]).drop_duplicates().head(5)

    symbol_to_company = top_symbols_df.set_index(
        "symbol")["security_name"].to_dict()

    # Use pathlib for directory traversal and file name extraction
    csv_files = [file for file in path.iterdir() if file.stem in symbol_to_company]

    dfs = []
    for file in csv_files:
        # Extract the stock symbol from the filename
        symbol = file.stem
        df = pd.read_csv(file)
        df["Symbol"] = symbol
        df["Company Name"] = symbol_to_company.get(
            symbol, "Unknown")  # Add company name
        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)

    # Ensure the selected company rows are at the top
    combined_df = pd.concat([combined_df[combined_df["Symbol"] == selected_company_row["symbol"].values[0]],
                             combined_df[combined_df["Symbol"] != selected_company_row["symbol"].values[0]]])


combined_df["Date"] = pd.to_datetime(combined_df["Date"])

# Filter out any lines before 2000 so that the file isn't too big
combined_df = combined_df[combined_df["Date"] > "2000-01-01"]

# Make sure combined df only has stock dates from when the selected company started trading
sel_comp_min_date = combined_df[combined_df["Company Name"]==selected_company]["Date"].min()
combined_df = combined_df[combined_df["Date"]>= sel_comp_min_date]

selected_columns = ['symbol', 'security_name',
                    'industry', 'sector', 'city', 'state', 'country']
top_symbols_df = top_symbols_df[selected_columns]
