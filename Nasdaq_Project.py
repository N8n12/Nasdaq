import os
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from datetime import datetime

st.title("Stock Market Analysis")
st.write("Analyze stocks using data from Kaggle and Yahoo Finance.")

# Path to dataset folder
main_path = "/path/to/dataset"  # Update with your actual path
path = os.path.join(main_path, "stocks")
symbols_csv_path = os.path.join(main_path, "dividend_stocks_only.csv")
symbols_df = pd.read_csv(symbols_csv_path)

# Dropdown for selecting company
selected_company = st.selectbox(
    "Choose a company to analyze",
    options=symbols_df["security_name"].tolist()
)

# Display selected company details
if selected_company:
    selected_industry = symbols_df[symbols_df["security_name"] == selected_company]["sector"].values[0]
    st.write(f"Selected company belongs to the industry: {selected_industry}")

def plot_filtered_chart(filtered_df, start_date, end_date):
    # Plot the filtered data
    plt.figure(figsize=(14, 7))
    sns.lineplot(data=filtered_df, x="Date", y="Rebased Adj Close", hue="Company Name")
    plt.xlabel("Date")
    plt.ylabel("Rebased Adj Close")
    plt.legend(title="Company Name")
    plt.grid(True)
    st.pyplot(plt)

start_date = st.date_input("Select Start Date")
end_date = st.date_input("Select End Date")
if start_date and end_date:
    # Call your data processing logic here
    filtered_df = combined_df[(combined_df["Date"] >= start_date) & (combined_df["Date"] <= end_date)]
    plot_filtered_chart(filtered_df, start_date, end_date)

st.write("Preview of combined data:")
st.dataframe(combined_df.head())
