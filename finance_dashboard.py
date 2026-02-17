import pandas as pd
import streamlit as st
import plotly.express as px

# 17FEB2026

# -----------------------
# DATA LOADING
# -----------------------

def load_data(file):
    df = pd.read_csv(file, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'])

    if 'Account' not in df.columns:
        df['Account'] = 'Unknown'

    return df


# -----------------------
# ANALYSIS HELPERS
# -----------------------

def calculate_savings_health(total_income, total_expenses):
    if total_income == 0:
        return "No income data available."

    savings = total_income + total_expenses
    savings_rate = (savings / total_income) * 100

    if savings < 0:
        return f"🚨 You are running a deficit. Savings rate: {savings_rate:.1f}%"
    elif savings_rate >= 20:
        return f"🟢 Strong financial health. Savings rate: {savings_rate:.1f}%"
    elif savings_rate >= 10:
        return f"🟡 Moderate savings rate: {savings_rate:.1f}%"
    else:
        return f"🔴 Low savings rate: {savings_rate:.1f}%"


def generate_month_over_month_insights(df):
    df_sorted = df.sort_values("Date").copy()
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

    return insights


def detect_spending_concentration(spending):
    if spending.empty:
        return "No spending data available."

    total_spending = spending.sum()
    largest_category = spending.idxmax()
    largest_value = spending.max()

    percentage = (largest_value / total_spending) * 100

    if percentage >= 50:
        return f"🚨 {largest_category} represents {percentage:.1f}% of total expenses. High concentration risk."
    elif percentage >= 35:
        return f"⚠️ {largest_category} represents {percentage:.1f}% of total expenses."
    else:
        return f"📊 {largest_category} is your largest expense at {percentage:.1f}% of total spending."


def detect_deficit_and_runway(df):
    df_sorted = df.sort_values("Date").copy()
    df_sorted["Month"] = df_sorted["Date"].dt.to_period("M")

    monthly_net = df_sorted.groupby("Month")["Amount"].sum()

    if len(monthly_net) == 0:
        return "No financial data available."

    latest_month_value = monthly_net.iloc[-1]

    if latest_month_value >= 0:
        return "✅ No deficit detected in the latest month."

    deficit_amount = abs(latest_month_value)
    return f"🚨 You ran a ${deficit_amount:,.2f} deficit this month."


def benchmark_spending(spending):
    if spending.empty:
        return ["No spending data available."]

    benchmarks = {
        "Housing": 30,
        "Transportation": 15,
        "Groceries": 15
    }

    total = spending.sum()
    messages = []

    for category, value in spending.items():
        percent = (value / total) * 100

        if category in benchmarks:
            threshold = benchmarks[category]
            if percent > threshold:
                diff = percent - threshold
                messages.append(
                    f"⚠️ {category} exceeds recommended {threshold}% threshold by {diff:.1f}%."
                )

    if not messages:
        messages.append("✅ Spending categories are within recommended thresholds.")

    return messages


def calculate_spending_opportunity(spending):
    if spending.empty:
        return ["No spending data available."]

    benchmarks = {
        "Housing": 30,
        "Transportation": 15,
        "Groceries": 15
    }

    total_spending = spending.sum()
    messages = []

    for category, value in spending.items():
        percent = (value / total_spending) * 100

        if category in benchmarks:
            threshold = benchmarks[category]
            if percent > threshold:
                recommended_amount = (threshold / 100) * total_spending
                opportunity = value - recommended_amount

                messages.append(
                    f"💡 Reducing {category} to {threshold}% would free approximately ${opportunity:,.2f} per month."
                )

    if not messages:
        messages.append("✅ No immediate spending reduction opportunities detected.")

    return messages


# -----------------------
# FINANCIAL ANALYZER CLASS
# -----------------------

class FinancialAnalyzer:

    def __init__(self, df, selected_account):
        self.df = df[df["Account"] == selected_account].copy()
        self.df["Month"] = self.df["Date"].dt.to_period("M")

        self.total_income = 0
        self.total_expenses = 0
        self.monthly_summary = None
        self.spending = None

        self.savings_health = None
        self.insights = None
        self.concentration = None
        self.benchmarks = None
        self.opportunities = None
        self.runway = None

    def run(self):
        self._calculate_core_metrics()
        self._run_analyses()

    def _calculate_core_metrics(self):
        self.total_income = self.df[self.df["Amount"] > 0]["Amount"].sum()
        self.total_expenses = self.df[self.df["Amount"] < 0]["Amount"].sum()

        self.monthly_summary = self.df.groupby("Month")["Amount"].sum()

        self.spending = (
            self.df[self.df["Amount"] < 0]
            .groupby("Category")["Amount"]
            .sum()
            .abs()
        )

    def _run_analyses(self):
        self.savings_health = calculate_savings_health(
            self.total_income,
            self.total_expenses
        )

        self.insights = generate_month_over_month_insights(self.df)
        self.concentration = detect_spending_concentration(self.spending)
        self.benchmarks = benchmark_spending(self.spending)
        self.opportunities = calculate_spending_opportunity(self.spending)
        self.runway = detect_deficit_and_runway(self.df)


# -----------------------
# PLOTLY CHARTS
# -----------------------

def plot_monthly_summary(monthly_summary):
    df_plot = monthly_summary.reset_index()
    df_plot.columns = ['Month', 'Net Amount']
    df_plot['Month'] = df_plot['Month'].astype(str)

    return px.bar(
        df_plot,
        x='Month',
        y='Net Amount',
        title='Net Income per Month'
    )


def plot_spending_pie(spending):
    df_plot = spending.reset_index()
    df_plot.columns = ['Category', 'Amount']

    return px.pie(
        df_plot,
        names='Category',
        values='Amount',
        title='Spending by Category'
    )


# -----------------------
# STREAMLIT APP
# -----------------------

st.set_page_config(page_title="Financial Insight Dashboard", layout="wide")
st.title("📊 Financial Insight Dashboard")
st.caption("Upload transaction exports to receive automated financial health analysis and trend insights.")

uploaded_file = st.file_uploader("Upload your transactions CSV", type="csv")

if uploaded_file:

    df = load_data(uploaded_file)

    accounts = df['Account'].unique().tolist()
    selected_account = st.selectbox("Select Account", accounts)

    start_date = st.date_input("Start Date", df['Date'].min())
    end_date = st.date_input("End Date", df['Date'].max())

    if start_date > end_date:
        st.error("Start date must be before end date.")
        st.stop()

    df_filtered = df[
        (df['Date'] >= pd.to_datetime(start_date)) &
        (df['Date'] <= pd.to_datetime(end_date))
    ]

    engine = FinancialAnalyzer(df_filtered, selected_account)
    engine.run()

    # Summary
    st.subheader("Summary")
    st.write(f"**Total Income:** ${engine.total_income:,.2f}")
    st.write(f"**Total Expenses:** ${engine.total_expenses:,.2f}")

    # Financial Health
    st.subheader("💡 Financial Health")
    st.write(engine.savings_health)

    # Concentration
    st.subheader("📌 Spending Concentration")
    st.write(engine.concentration)

    # Benchmarks
    st.subheader("📏 Benchmark Comparison")
    for msg in engine.benchmarks:
        st.write(msg)

    # Opportunities
    st.subheader("💡 Optimization Opportunities")
    for msg in engine.opportunities:
        st.write(msg)

    # Charts
    st.subheader("Monthly Net Income")
    st.plotly_chart(plot_monthly_summary(engine.monthly_summary))

    st.subheader("Spending by Category")
    st.plotly_chart(plot_spending_pie(engine.spending))

    # Insights
    st.subheader("📊 Month-over-Month Insights")
    for insight in engine.insights:
        st.write(insight)

    # Runway
    st.subheader("🚨 Deficit & Runway Analysis")
    st.write(engine.runway)

    # Download
    st.subheader("Download Filtered Data")
    csv_data = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download CSV",
        csv_data,
        "filtered_transactions.csv",
        "text/csv"
    )
