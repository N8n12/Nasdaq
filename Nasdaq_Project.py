
import os
import pandas as pd
import kagglehub
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from datetime import datetime

# Streamlit title and description
st.title("Stock Market Analysis with Kaggle Data")
st.write("Analyze stocks using datasets downloaded with KaggleHub and Yahoo Finance.")

# Download datasets using kagglehub
@st.cache_data
def download_datasets():
    """Download datasets from Kaggle using kagglehub."""
    main_path = kagglehub.dataset_download("jacksoncrow/stock-market-dataset")
    stocks_path = os.path.join(main_path, "stocks")
    symbols_csv_path = kagglehub.dataset_download("gonzalezfrancisco/full-nasdaq-stocks-data") + "/dividend_stocks_only.csv"
    symbols_df = pd.read_csv(symbols_csv_path)
    return stocks_path, symbols_df

# Load datasets
stocks_path, symbols_df = download_datasets()

# Dropdown for selecting a company
selected_company = st.selectbox(
    "Choose a company to analyze",
    options=symbols_df["security_name"].tolist()
)

# Display details of the selected company
if selected_company:
    selected_industry = symbols_df[symbols_df["security_name"] == selected_company]["sector"].values[0]
    st.write(f"Selected company belongs to the industry: {selected_industry}")

    # Filter companies in the same industry
    top_symbols_df = symbols_df[symbols_df["sector"] == selected_industry].head(4)
    top_symbols_df = pd.concat(
        [symbols_df[symbols_df["security_name"] == selected_company], top_symbols_df]
    ).drop_duplicates().head(5)
    st.write("Top companies in the same industry:")
    st.dataframe(top_symbols_df)

    # Load stock data for the selected companies
    symbol_to_company = top_symbols_df.set_index("symbol")["security_name"].to_dict()
    csv_files = [f for f in os.listdir(stocks_path) if os.path.splitext(f)[0] in symbol_to_company]
    dfs = []
    for file in csv_files:
        symbol = os.path.splitext(file)[0]
        df = pd.read_csv(os.path.join(stocks_path, file))
        df["Symbol"] = symbol
        df["Company Name"] = symbol_to_company.get(symbol, "Unknown")
        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)

    # Display combined data
    st.write("Combined stock data for selected companies:")
    st.dataframe(combined_df.head())

    # Add the Rebased Adj Close Column
    combined_df["Date"] = pd.to_datetime(combined_df["Date"])
    combined_df = combined_df.set_index("Date")
    combined_df["Rebased Adj Close"] = combined_df.groupby("Symbol")["Close"].transform(
        lambda x: (x / x.iloc[0]) * 100).values
    combined_df = combined_df.reset_index()

    # Plot data based on selected date range
    st.write("Select a date range to filter data:")
    start_date = st.date_input("Start Date", combined_df["Date"].min())
    end_date = st.date_input("End Date", combined_df["Date"].max())

    if start_date and end_date:
        filtered_df = combined_df[
            (combined_df["Date"] >= pd.to_datetime(start_date)) & 
            (combined_df["Date"] <= pd.to_datetime(end_date))
        ]

        # Plot the filtered data
        st.write("Rebased Adjusted Close Price Over Time:")
        plt.figure(figsize=(14, 7))
        sns.lineplot(data=filtered_df, x="Date", y="Rebased Adj Close", hue="Company Name")
        plt.xlabel("Date")
        plt.ylabel("Rebased Adj Close")
        plt.legend(title="Company Name")
        plt.grid(True)
        st.pyplot(plt)
