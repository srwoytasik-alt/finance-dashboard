import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------
# DATA FUNCTIONS
# -----------------------

def load_data(file):
    df = pd.read_csv(file, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')

    if 'Account' not in df.columns:
        df['Account'] = 'Unknown'

    return df


def summarize(df, account=None):
    if account:
        df = df[df['Account'] == account]

    total_income = df[df['Amount'] > 0]['Amount'].sum()
    total_expenses = df[df['Amount'] < 0]['Amount'].sum()
    monthly_summary = df.groupby('Month')['Amount'].sum()
    spending = (
        df[df['Amount'] < 0]
        .groupby('Category')['Amount']
        .sum()
        .abs()
    )

    return total_income, total_expenses, monthly_summary, spending


# -----------------------
# PLOTLY CHARTS
# -----------------------

def plot_monthly_summary(monthly_summary):
    df_plot = monthly_summary.reset_index()
    df_plot.columns = ['Month', 'Net Amount']
    df_plot['Month'] = df_plot['Month'].astype(str)

    fig = px.bar(
        df_plot,
        x='Month',
        y='Net Amount',
        title='Net Income per Month'
    )

    return fig


def plot_spending_pie(spending):
    df_plot = spending.reset_index()
    df_plot.columns = ['Category', 'Amount']

    fig = px.pie(
        df_plot,
        names='Category',
        values='Amount',
        title='Spending by Category'
    )

    return fig


# -----------------------
# STREAMLIT APP
# -----------------------

st.title("💰 Personal Finance Dashboard")

uploaded_file = st.file_uploader("Upload your transactions CSV", type="csv")

if uploaded_file:

    df = load_data(uploaded_file)

    # Account selector
    accounts = df['Account'].unique().tolist()
    selected_account = st.selectbox("Select Account", accounts)

    # Date filter
    start_date = st.date_input("Start Date", df['Date'].min())
    end_date = st.date_input("End Date", df['Date'].max())

    df_filtered = df[
        (df['Date'] >= pd.to_datetime(start_date)) &
        (df['Date'] <= pd.to_datetime(end_date))
    ]

    total_income, total_expenses, monthly_summary, spending = summarize(
        df_filtered,
        selected_account
    )

    st.subheader("Summary")
    st.write(f"**Total Income:** ${total_income:,.2f}")
    st.write(f"**Total Expenses:** ${total_expenses:,.2f}")

    st.subheader("Monthly Net Income")
    st.plotly_chart(plot_monthly_summary(monthly_summary))

    st.subheader("Spending by Category")
    st.plotly_chart(plot_spending_pie(spending))

    # CSV Download
    st.subheader("Download Filtered Data")
    csv_data = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download CSV",
        csv_data,
        "filtered_transactions.csv",
        "text/csv"
    )
