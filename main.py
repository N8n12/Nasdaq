import os
import streamlit as st
import pandas as pd
import kagglehub
import yfinance as yf
import matplotlib.pyplot as plt
import requests
import plotly.graph_objs as go
from datetime import datetime

# Path to dataset folder
main_path = kagglehub.dataset_download("jacksoncrow/stock-market-dataset")
path = main_path + "/stocks"
path_dict = kagglehub.dataset_download(
    "gonzalezfrancisco/full-nasdaq-stocks-data")

# Load the validation csv with company names
symbols_csv_path = path_dict + "/full_financial_stocks_raw.csv"
symbols_df = pd.read_csv(symbols_csv_path)
symbols_df = symbols_df[~symbols_df["security_name"].str.contains("Associated Capital Group|ABB Ltd")
                        ]
combobox_df = symbols_df[symbols_df["security_name"].str.contains(
    "Common Stock")]
cacib_logo = "https://upload.wikimedia.org/wikipedia/commons/7/72/Cr%C3%A9ditAgricoleCIB_logo.svg"

_, col2, _ = st.columns(3)

with col2:
    st.image(cacib_logo, use_container_width='auto')

st.write("# Python analytics project, Team Nasdaq")
st.write("""Welcome to our app :wave:!

This app allows users to look up certain stocks that are in the Nasdaq.

By filtering for the selected company, you are able to look at its past performance, get some more information about the company as well see how its stock compares to some of it's industry competitors.

It's worth noting that the data we are using from the charts come from a fixed datasource from Kaggle, and the chart data only comes up to april 2020.

Feel free to reach out to Tim (tim.stott@ca-cib.com) or Nathan (nathan.birnbaum@ca-cib.com) if you have any questions.

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
    csv_files = [f for f in os.listdir(path) if os.path.splitext(f)[
        0] in symbol_to_company]

    dfs = []
    for file in csv_files:
        # Extract the stock symbol from the filename
        symbol = os.path.splitext(file)[0]
        df = pd.read_csv(os.path.join(path, file))
        df["Symbol"] = symbol
        df["Company Name"] = symbol_to_company.get(
            symbol, "Unknown")  # Add company name
        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)

    # Ensure the selected company rows are at the top
    combined_df = pd.concat([combined_df[combined_df["Symbol"] == selected_company_row["symbol"].values[0]],
                             combined_df[combined_df["Symbol"] != selected_company_row["symbol"].values[0]]])


combined_df["Date"] = pd.to_datetime(combined_df["Date"])

#filter out any lines before 2000 so that the file isn't too big
combined_df = combined_df[combined_df["Date"] > "2000-01-01"]

#make sure combined df only has stock dates from when the selected company started trading
sel_comp_min_date = combined_df[combined_df["Company Name"]==selected_company]["Date"].min()
combined_df = combined_df[combined_df["Date"]>= sel_comp_min_date]

selected_columns = ['symbol', 'security_name',
                    'industry', 'sector', 'city', 'state', 'country']
top_symbols_df = top_symbols_df[selected_columns]


def get_company_info(symbol):
    company = yf.Ticker(symbol)
    info = company.info
    
    company_row = top_symbols_df[top_symbols_df['symbol'] == symbol]

    values = top_symbols_df.loc[top_symbols_df["symbol"] == symbol, ["industry", "sector", "city", "state", "country"]].iloc[0].fillna("Not Available")
    
    currency = info.get("financialCurrency")

    total_revenue = "{:,.2f}".format(info.get("totalRevenue")/1_000_000) if isinstance(info.get("totalRevenue"), (int, float)) else ""
    
    company_info = {
        "website": info.get("website", "Not available"),
        "Industry": values['sector'] + ", " + values['industry'],
        "Full Time Employees": "{:,.0f}".format(info.get("fullTimeEmployees")) if isinstance(info.get("fullTimeEmployees"), (int, float)) else "Not available",
        "Headquarter": values['city'] + ", " + values['state'] + ", " + values['country'],
        "Business Description": info.get("longBusinessSummary", "Not available"),
        "Currency": info.get("currency", "Not available"),
        "Latest Total Revenue (Millions)": f"{currency} {total_revenue}",
        "Gross Margin": "{:.2%}".format(info.get("grossMargins")) if isinstance(info.get("grossMargins"), (int, float)) else "Not available",
        "Net Margin": "{:.2%}".format(info.get("profitMargins")) if isinstance(info.get("profitMargins"), (int, float)) else "Not available",
        "MarketCap (Millions)": "{:,.2f}".format(info.get("marketCap")/1_000_000) if isinstance(info.get("marketCap"), (int, float)) else "Not available"
    }

    return company_info


company_info = get_company_info(combined_df.iloc[0]["Symbol"])
# get company logo


def get_company_logo_url(company_domain):
    api_url = f"https://logo.clearbit.com/{company_domain}"
    response = requests.get(api_url)

    if response.status_code == 200:
        return api_url
    else:
        return None


logo_url = get_company_logo_url(company_info["website"])

# create 2 columns, one for the title that is larger, and a smaller one for the company logo
col1, col2 = st.columns([8, 2])
with col1:
    st.write("## Company Information")

with col2:
    if logo_url is not None:
        st.image(logo_url, width=70)
# display company information in streamlit

if selected_company:
    company_info = get_company_info(combined_df.iloc[0]["Symbol"])
    for key, value in company_info.items():
        st.write(f"****{key}:**** *{value}*")


# Candlestick chart
st.write("## Candle stick graph")
st.write("##### Looking at how the stock performs over time")

filtered_df = combined_df[
    (combined_df["Symbol"] == combined_df.iloc[0]["Symbol"]) &
    (combined_df["Date"] > "2010-01-01")
]
# Display candlestick chart
if filtered_df.empty:
    st.error(
        "Failed to fetch historical data. Please check your API key and selected instrument.")
else:
    # Extract data for plotting
    dates = filtered_df["Date"].tolist()
    open_prices = filtered_df["Open"].tolist()
    high_prices = filtered_df["High"].tolist()
    low_prices = filtered_df["Low"].tolist()
    close_prices = filtered_df["Close"].tolist()

    # Create candlestick chart using Plotly
    candlestick = go.Candlestick(x=dates,
                                 open=open_prices,
                                 high=high_prices,
                                 low=low_prices,
                                 close=close_prices)

    layout = go.Layout(xaxis=dict(title='Date'),
                       yaxis=dict(title='Price'))

    fig = go.Figure(data=[candlestick], layout=layout)

    # Display the chart using Streamlit
    st.plotly_chart(fig)


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

    filtered_df = filtered_df[filtered_df["Date"] >= filtered_df[filtered_df["Symbol"] == filtered_df.iloc[0]["Symbol"]]["Date"].min()]  

    
    # Recalculate the Rebased Adj Close based on the selected start_date
    for symbol in filtered_df["Symbol"].unique():
        symbol_df = filtered_df[filtered_df["Symbol"] == symbol]
        if not symbol_df.empty:
            # Find the closest date to start_date if it's not present in the data
            start_date_index = symbol_df["Date"].eq(start_date).idxmax()

            # Handle the case where idxmax returns 0 (start of dataframe) but start_date is not the first date
            if start_date_index == 0 and symbol_df["Date"].iloc[0] != start_date:
                start_date_index = symbol_df["Date"].searchsorted(start_date)[0]

            start_close = symbol_df.loc[start_date_index, "Close"]
            filtered_df.loc[filtered_df["Symbol"] == symbol, "Rebased Adj Close"] = (
                filtered_df.loc[filtered_df["Symbol"] ==
                                symbol, "Close"] / start_close * 100
            )
    chart_data = filtered_df.pivot(
        index="Date", columns="Company Name", values="Rebased Adj Close")
    st.line_chart(chart_data)

# Display the chart
if selected_company:
    st.write("## Industry stock comparison")
    st.write("Rebasing the adjusted close for each stock to 100")
    # Date filter using Streamlit slider
    date_range = st.slider(
        "Select Date Range",
        min_value=combined_df["Date"].min().date(),
        max_value=combined_df["Date"].max().date(),
        # Default to full range
        value=(combined_df["Date"].min().date(),
               combined_df["Date"].max().date()),
        format="YYYY-MM-DD")

    # Extract start and end dates from the slider
    start_date, end_date = date_range

    # Filter and plot the data
    plot_filtered_chart(pd.Timestamp(start_date), pd.Timestamp(end_date))
st.write(
    f"Companies in the same industry as {selected_company} ({selected_industry}):")
top_symbols_df.security_name


def download_csv(df, filename):
    csv = df.to_csv(index=False).encode()
    return csv

# Add download buttons
col3, col4 = st.columns([5, 5])
with col3:
    st.download_button(
        label="Download stock Data",
        data=download_csv(combined_df, "stock_data"),
        file_name="stock_data.csv",
        mime="text/csv")
with col4:
    st.download_button(
        label="Download Companies Data",
        data=download_csv(top_symbols_df, "company_data"),
        file_name="company_data.csv",
        mime="text/csv")

lewagon_logo = "https://cdn.prod.website-files.com/59ef1c38722dc900018cec11/5d42ef3384e9f900ba77e16f_le-wagon-color.png"

col1,col2,col3= st.columns([2,1,2])

with col2:
    st.image(lewagon_logo,width = 200,use_column_width=True )
st.write( 
    '<p style="text-align: center;">'"""
This is a fake disclaimer that I have created for no reason.    
I just wanted to see how this would look with this text here.
    """,unsafe_allow_html=True)
