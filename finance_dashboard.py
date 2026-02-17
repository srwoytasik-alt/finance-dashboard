import pandas as pd
import streamlit as st
import plotly.express as px

#push to github 
# # git add finance_dashboard.py 
# # git commit -m "Add month-over-month insight engine" 
# # git push

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


def generate_month_over_month_insights(df):
    df_sorted = df.sort_values("Date")
    df_sorted["Month"] = df_sorted["Date"].dt.to_period("M")

    monthly_net = df_sorted.groupby("Month")["Amount"].sum()

    if len(monthly_net) < 2:
        return ["Not enough data for month-over-month analysis."]

    last_value = monthly_net.iloc[-1]
    prev_value = monthly_net.iloc[-2]

    change_percent = (
        ((last_value - prev_value) / abs(prev_value)) * 100
        if prev_value != 0 else 0
    )

    insights = []

    if change_percent > 0:
        insights.append(
            f"📈 Net income increased {change_percent:.1f}% compared to last month."
        )
    elif change_percent < 0:
        insights.append(
            f"📉 Net income decreased {abs(change_percent):.1f}% compared to last month."
        )
    else:
        insights.append("➡️ Net income remained stable compared to last month.")

    # Category comparison
    category_month = (
        df_sorted[df_sorted["Amount"] < 0]
        .groupby(["Month", "Category"])["Amount"]
        .sum()
        .abs()
        .unstack(fill_value=0)
    )

    if len(category_month) >= 2:
        last_cat = category_month.iloc[-1]
        prev_cat = category_month.iloc[-2]

        diff = last_cat - prev_cat
        top_increase = diff.sort_values(ascending=False).index[0]
        increase_value = diff.sort_values(ascending=False).iloc[0]

        if increase_value > 0:
            insights.append(
                f"⚠️ {top_increase} spending increased by ${increase_value:.2f} compared to last month."
            )

    return insights


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

st.set_page_config(page_title="Finance Dashboard", layout="wide")
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

    if start_date > end_date:
        st.error("Start date must be before end date.")
        st.stop()

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

    # -------- Insights Section --------
    st.subheader("📊 Month-over-Month Insights")

    df_for_insights = df_filtered[df_filtered["Account"] == selected_account]
    insights = generate_month_over_month_insights(df_for_insights)

    for insight in insights:
        st.write(insight)

    # -------- CSV Download --------
    st.subheader("Download Filtered Data")
    csv_data = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download CSV",
        csv_data,
        "filtered_transactions.csv",
        "text/csv"
    )


#push to github 
# # git add finance_dashboard.py 
# # git commit -m "Add month-over-month insight engine" 
# # git push
