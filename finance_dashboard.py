import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Financial Insight Dashboard", layout="wide")
st.title("📊 Financial Insight Dashboard")
st.caption("Upload transaction exports → get automated health analysis & insights")

# ── DATA LOADING ──────────────────────────────────────────────────────────
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date']) # drop invalid dates early
        if 'Account' not in df.columns:
            df['Account'] = 'Main Account'
        if 'Category' not in df.columns:
            df['Category'] = 'Uncategorized'
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


# ── ANALYSIS HELPERS ──────────────────────────────────────────────────────
def calculate_savings_health(total_income, total_expenses):
    if total_income <= 0:
        return "No meaningful income detected in selected period."

    net_savings = total_income + total_expenses # expenses are negative
    savings_rate = (net_savings / total_income) * 100

    if net_savings < 0:
        return f"🚨 Deficit — spending {abs(savings_rate):.1f}% more than income"
    elif savings_rate >= 25:
        return f"🟢 Excellent — saving {savings_rate:.1f}% of income"
    elif savings_rate >= 15:
        return f"🟢 Good — saving {savings_rate:.1f}% of income"
    elif savings_rate >= 5:
        return f"🟡 Moderate — saving {savings_rate:.1f}% of income"
    else:
        return f"🔴 Low — saving only {savings_rate:.1f}% of income"


def generate_month_over_month_insights(df):
    if df.empty:
        return ["No data for analysis."]
    
    df_sorted = df.sort_values("Date").copy()
    df_sorted["Month"] = df_sorted["Date"].dt.to_period("M")
    monthly_net = df_sorted.groupby("Month")["Amount"].sum()

    if len(monthly_net) < 2:
        return ["Not enough months for comparison."]

    last = monthly_net.iloc[-1]
    prev = monthly_net.iloc[-2]

    if abs(prev) < 1: # avoid division by near-zero
        return ["Previous month net was near zero — % change not reliable."]

    pct_change = ((last - prev) / abs(prev)) * 100

    if pct_change > 5:
        return [f"📈 Net improved significantly (+{pct_change:.1f}%) vs last month."]
    elif pct_change > 0:
        return [f"📈 Net up slightly (+{pct_change:.1f}%) vs last month."]
    elif pct_change < -5:
        return [f"📉 Net worsened significantly ({pct_change:.1f}%) vs last month."]
    elif pct_change < 0:
        return [f"📉 Net down slightly ({pct_change:.1f}%) vs last month."]
    else:
        return ["➡️ Net remained stable vs last month."]


def detect_spending_concentration(spending):
    if spending.empty or spending.sum() == 0:
        return "No spending in selected period."

    total = spending.sum()
    top_cat = spending.idxmax()
    top_val = spending.max()
    pct = (top_val / total) * 100

    n_cats = len(spending)

    if pct >= 50:
        risk = f"🚨 High concentration: {top_cat} = {pct:.1f}% of spending"
    elif pct >= 35:
        risk = f"⚠️ Notable: {top_cat} = {pct:.1f}% of spending"
    else:
        risk = f"📊 Largest is {top_cat} at {pct:.1f}%"

    if n_cats <= 3:
        risk += f" (only {n_cats} categories — consider better categorization)"

    return risk


def benchmark_spending(spending):
    if spending.empty or spending.sum() == 0:
        return ["No spending to benchmark."]

    benchmarks = {"Housing": 30, "Transportation": 15, "Groceries": 15}
    total = spending.sum()
    messages = []

    for cat, val in spending.items():
        if cat in benchmarks:
            pct = (val / total) * 100
            thresh = benchmarks[cat]
            if pct > thresh + 5:
                diff = pct - thresh
                messages.append(f"⚠️ {cat} is {pct:.1f}% (over by {diff:.1f}%)")

    return messages if messages else ["✅ Categories mostly within common guidelines."]


def calculate_spending_opportunity(spending):
    if spending.empty or spending.sum() == 0:
        return ["No spending reduction opportunities to calculate."]

    benchmarks = {"Housing": 30, "Transportation": 15, "Groceries": 15}
    total = spending.sum()
    messages = []

    for cat, val in spending.items():
        if cat in benchmarks:
            pct = (val / total) * 100
            thresh = benchmarks[cat]
            if pct > thresh + 5:
                recommended = (thresh / 100) * total
                savings = val - recommended
                messages.append(f"💡 Cut {cat} → \~${savings:,.0f}/mo potential")

    return messages if messages else ["✅ No clear quick wins detected."]


def detect_deficit_and_runway(df):
    if df.empty:
        return "No data."
    df_sorted = df.sort_values("Date").copy()
    df_sorted["Month"] = df_sorted["Date"].dt.to_period("M")
    monthly_net = df_sorted.groupby("Month")["Amount"].sum()
    if monthly_net.empty:
        return "No monthly summary available."
    latest = monthly_net.iloc[-1]
    if latest >= 0:
        return "✅ Latest month positive or balanced."
    return f"🚨 Latest month deficit: ${abs(latest):,.0f}"


# ── FINANCIAL ANALYZER ────────────────────────────────────────────────────
class FinancialAnalyzer:
    def __init__(self, df, selected_account):
        self.df = df[df["Account"] == selected_account].copy()
        self.df["Month"] = self.df["Date"].dt.to_period("M")

        self.total_income = 0.0
        self.total_expenses = 0.0 # will be negative
        self.monthly_summary = None
        self.spending_by_cat = None
        self.cumulative_flow = None

        self.savings_health = ""
        self.mom_insights = []
        self.concentration = ""
        self.benchmarks = []
        self.opportunities = []
        self.deficit_info = ""

    def run(self):
        if self.df.empty:
            return

        self.total_income = self.df[self.df["Amount"] > 0]["Amount"].sum()
        self.total_expenses = self.df[self.df["Amount"] < 0]["Amount"].sum() # negative

        self.monthly_summary = self.df.groupby("Month")["Amount"].sum()
        self.spending_by_cat = (
            self.df[self.df["Amount"] < 0]
            .groupby("Category")["Amount"]
            .sum()
            .abs()
            .sort_values(ascending=False)
        )

        # Cumulative cash flow (proxy for net worth change)
        sorted_df = self.df.sort_values("Date")
        self.cumulative_flow = sorted_df.assign(
            Cumulative=sorted_df["Amount"].cumsum()
        )

        # Run insights
        self.savings_health = calculate_savings_health(self.total_income, self.total_expenses)
        self.mom_insights = generate_month_over_month_insights(self.df)
        self.concentration = detect_spending_concentration(self.spending_by_cat)
        self.benchmarks = benchmark_spending(self.spending_by_cat)
        self.opportunities = calculate_spending_opportunity(self.spending_by_cat)
        self.deficit_info = detect_deficit_and_runway(self.df)


# ── PLOTS ─────────────────────────────────────────────────────────────────
def plot_monthly_summary(monthly_summary):
    if monthly_summary is None or monthly_summary.empty:
        return None
    dfp = monthly_summary.reset_index().rename(columns={"Month": "Month", "Amount": "Net"})
    dfp["Month"] = dfp["Month"].astype(str)
    return px.bar(dfp, x="Month", y="Net", title="Monthly Net Flow")


def plot_spending_pie(spending):
    if spending is None or spending.empty:
        return None
    dfp = spending.reset_index().rename(columns={"Category": "Category", "Amount": "Spent"})
    return px.pie(dfp, names="Category", values="Spent", title="Spending Breakdown")


def plot_cumulative_flow(cum_df):
    if cum_df is None or cum_df.empty:
        return None
    return px.line(
        cum_df, x="Date", y="Cumulative",
        title="Cumulative Cash Flow (Net Worth Proxy)"
    )


# ── MAIN APP ──────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload transactions CSV", type="csv")

if uploaded_file:
    with st.spinner("Loading and preparing data..."):
        raw_df = load_data(uploaded_file)

    if raw_df is not None and not raw_df.empty:
        accounts = sorted(raw_df["Account"].unique())
        selected_account = st.selectbox("Select Account", accounts, index=0)

        # Date range
        min_d = raw_df["Date"].min().date()
        max_d = raw_df["Date"].max().date()

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            start_date = st.date_input("Start", min_d, min_value=min_d, max_value=max_d)
        with col2:
            end_date = st.date_input("End", max_d, min_value=min_d, max_value=max_d)
        with col3:
            if st.button("Last 12 months", use_container_width=True):
                from dateutil.relativedelta import relativedelta
                default_end = max_d
                default_start = (datetime.combine(default_end, datetime.min.time()) - relativedelta(months=12)).date()
                st.session_state["start_override"] = default_start
                st.rerun()

        # Override if button was pressed
        if "start_override" in st.session_state:
            start_date = st.session_state["start_override"]
            del st.session_state["start_override"]

        if start_date > end_date:
            st.error("Start date must be before or equal to end date.")
            st.stop()

        df_filtered = raw_df[
            (raw_df["Date"].dt.date >= start_date) &
            (raw_df["Date"].dt.date <= end_date)
        ]

        with st.spinner("Analyzing finances..."):
            analyzer = FinancialAnalyzer(df_filtered, selected_account)
            analyzer.run()

        # ── KEY METRICS ───────────────────────────────────────────────────
        st.subheader("Key Numbers")
        cols = st.columns(4)
        net_savings = analyzer.total_income + analyzer.total_expenses

        cols[0].metric("Income", f"${analyzer.total_income:,.0f}")
        cols[1].metric("Expenses", f"${abs(analyzer.total_expenses):,.0f}")
        cols[2].metric("Net Savings", f"${net_savings:,.0f}",
                       delta_color="normal" if net_savings >= 0 else "inverse")
        savings_rate = (net_savings / analyzer.total_income * 100) if analyzer.total_income > 0 else 0
        cols[3].metric("Savings Rate", f"{savings_rate:.1f}%")

        # ── HEALTH & FLAGS ────────────────────────────────────────────────
        st.subheader("Financial Health")
        st.markdown(analyzer.savings_health)

        st.subheader("Concentration Risk")
        st.write(analyzer.concentration)

        # ── CHARTS ────────────────────────────────────────────────────────
        st.subheader("Trends")
        tab1, tab2, tab3 = st.tabs(["Monthly Net", "Category Breakdown", "Cumulative Flow"])

        with tab1:
            fig = plot_monthly_summary(analyzer.monthly_summary)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data for monthly chart.")

        with tab2:
            fig = plot_spending_pie(analyzer.spending_by_cat)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No categorized spending data.")

        with tab3:
            fig = plot_cumulative_flow(analyzer.cumulative_flow)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data for cumulative view.")

        # ── INSIGHTS & OPPORTUNITIES ──────────────────────────────────────
        st.subheader("Insights & Alerts")
        for msg in analyzer.mom_insights:
            st.write(msg)

        st.write(analyzer.deficit_info)

        for msg in analyzer.benchmarks:
            st.write(msg)

        for msg in analyzer.opportunities:
            st.write(msg)

        # ── RAW DATA ──────────────────────────────────────────────────────
        with st.expander("View Filtered Transactions"):
            st.dataframe(
                df_filtered.sort_values("Date", ascending=False)
                .style.format({"Amount": "${:,.2f}", "Date": "{:%Y-%m-%d}"})
            )

        # ── DOWNLOAD ──────────────────────────────────────────────────────
        st.subheader("Export")
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Filtered Transactions CSV",
            data=csv,
            file_name="filtered_financials.csv",
            mime="text/csv"
        )

    else:
        st.info("Upload a valid CSV file to begin.")
else:
    st.info("Please upload your transaction CSV file.")
