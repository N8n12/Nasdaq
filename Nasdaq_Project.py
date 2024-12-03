#!/usr/bin/env python
# coding: utf-8

# In[2]:


pip install kagglehub


# In[4]:


pip install yfinance


# In[ ]:


pip install ipywidgets


# In[6]:


pip install streamlit


# In[7]:


import os
import pandas as pd
import kagglehub
import dask.dataframe as dd
import matplotlib.pyplot as plt
import seaborn as sns
from ipywidgets import widgets, interact
from datetime import datetime
import yfinance as yf
import streamlit as st


# In[8]:


# Path to dataset folder
main_path = kagglehub.dataset_download("jacksoncrow/stock-market-dataset")
path = main_path + "/stocks"
path_dict = kagglehub.dataset_download("gonzalezfrancisco/full-nasdaq-stocks-data")
# Load the validation csv with company names
symbols_csv_path = path_dict + "/dividend_stocks_only.csv"
symbols_df = pd.read_csv(symbols_csv_path)

# Initialize combined_df as an empty dataframe
combined_df = pd.DataFrame()

# Create a dropdown for the end user to select a company
company_selector = widgets.Combobox(
    placeholder="Choose company to analyse",
    options=symbols_df["security_name"].tolist(),
    description="Combobox:",
    ensure_option=True,
    disabled=False
)

# Function to update based on the selected company
def update(selected_company):
    global combined_df #makes sure it updates Combined_df outside the function
    if selected_company:
        selected_industry = symbols_df[symbols_df["security_name"] == selected_company]["sector"].values
        if selected_industry.size > 0:
            selected_industry = selected_industry[0]
            
            # Ensure the selected company is included and shown first
            selected_company_row = symbols_df[symbols_df["security_name"] == selected_company]
            top_symbols_df = symbols_df[symbols_df["sector"] == selected_industry].head(4)
            top_symbols_df = pd.concat([selected_company_row, top_symbols_df]).drop_duplicates().head(5)
            
            symbol_to_company = top_symbols_df.set_index("symbol")["security_name"].to_dict()
            csv_files = [f for f in os.listdir(path) if os.path.splitext(f)[0] in symbol_to_company]

            dfs = []
            for file in csv_files:
                symbol = os.path.splitext(file)[0]  # Extract the stock symbol from the filename
                df = pd.read_csv(os.path.join(path, file))
                df["Symbol"] = symbol
                df["Company Name"] = symbol_to_company.get(symbol, "Unknown")  # Add company name
                dfs.append(df)

            combined_df = pd.concat(dfs, ignore_index=True)
            
            # Ensure the selected company rows are at the top
            combined_df = pd.concat([combined_df[combined_df["Symbol"] == selected_company_row["symbol"].values[0]], 
                                     combined_df[combined_df["Symbol"] != selected_company_row["symbol"].values[0]]])

            print(f"Companies in the same industry as {selected_company} ({selected_industry}):")
            display(top_symbols_df)
        else:
            print("Selected company not found. Please choose a valid company from the dropdown.")
    else:
        print("Please select a company from the dropdown.")

# Add observer to the combobox to trigger update on change
company_selector.observe(lambda change: update(change.new), names="value")

# Display the combobox
display(company_selector)


# In[9]:


#Use Yfinance to get basic company info based on the selected company based on the company symbol

def get_company_info(symbol):
    company = yf.Ticker(symbol)
    info = company.info

    company_info = {
        "Business Description": info.get("longBusinessSummary", "Not available"),
        "Full Time Employees": info.get("fullTimeEmployees", "Not available"),
        "Latest Total Revenue (Millions)": round(info.get("totalRevenue","Not available")/1_000_000,2),
        "Currency": info.get("currency","Not available"),
        "industry": info.get("industry","Not available")
    }
    
    return company_info

get_company_info(combined_df.iloc[0]["Symbol"])


# In[13]:


#add the Rebased Adj Close Column

# Ensure the Date column is in datetime format
combined_df["Date"] = pd.to_datetime(combined_df["Date"])

# Calculate the Rebased Adj Close column with proper index alignment
combined_df = combined_df.set_index("Date")
combined_df["Rebased Adj Close"] = combined_df.groupby("Symbol")["Close"].transform(
    lambda x: (x / x.iloc[0]) * 100).values

# Reset the index to restore the original dataframe structure
combined_df = combined_df.reset_index()

# Function to plot the chart based on selected date range and recalculate Rebased Adj Close based on slider

def plot_filtered_chart(start_date, end_date):

    # Filter the dataframe for the selected date range
    filtered_df = combined_df[(combined_df["Date"] >= start_date) & (combined_df["Date"] <= end_date)].copy()
    
    # Recalculate the Rebased Adj Close based on the selected start_date
    for symbol in filtered_df["Symbol"].unique():
        symbol_df = filtered_df[filtered_df["Symbol"] == symbol]
        if not symbol_df.empty:
            start_close = symbol_df[symbol_df["Date"] == start_date]["Close"]
            if not start_close.empty:
                start_close = start_close.iloc[0]
                filtered_df.loc[filtered_df["Symbol"] == symbol, "Rebased Adj Close"] = (
                    filtered_df.loc[filtered_df["Symbol"] == symbol, "Close"] / start_close * 100
                )
    
    # Plot the filtered data
    plt.figure(figsize=(14, 7))
    sns.lineplot(data=filtered_df, x="Date", y="Rebased Adj Close", hue="Company Name")
    
    plt.xlabel("Date")
    plt.ylabel("Rebased Adj Close")
    plt.legend(title="Company Name")
    plt.grid(True)
    plt.show();

# Date filter sliders using ipywidgets
date_range_slider = widgets.SelectionRangeSlider(
    options=[datetime.strftime(d, "%Y-%m-%d") for d in combined_df["Date"].sort_values().unique()],
    index=(0, len(combined_df["Date"].unique())-1),
    description="Date Range",
    orientation="horizontal",
    layout={"width": "1200px"}
)

# Interactive plot with the sliders
def update_plot(date_range):
    start_date = datetime.strptime(date_range[0], "%Y-%m-%d")
    end_date = datetime.strptime(date_range[1], "%Y-%m-%d")
    plot_filtered_chart(start_date, end_date)

# Display the date range slider and interactive plot
interact(update_plot, date_range=date_range_slider);


# In[ ]:


#export to CSV to understand the data
combined_df.to_csv("combined_data.csv", index=False)

