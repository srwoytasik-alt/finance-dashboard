import pandas as pd

df = pd.read_csv("transactions.csv")

print(df.head())
print("\nTotal Income:", df[df["Amount"] > 0]["Amount"].sum())
print("Total Expenses:", df[df["Amount"] < 0]["Amount"].sum())

# import pandas as pd

# df = pd.read_csv("transactions.csv")

# print(df.columns)

df['Date'] = pd.to_datetime(df['Date'])
df['Month'] = df['Date'].dt.to_period('M')

monthly_summary = df.groupby('Month')['Amount'].sum()
print("\nMonthly Totals:")
print(monthly_summary)


category_summary = df[df['Amount'] < 0].groupby('Category')['Amount'].sum().sort_values()
print("\nTop Spending Categories:")
print(category_summary.head(3))



import matplotlib.pyplot as plt

# Bar chart of monthly net
monthly_summary.plot(kind='bar', color='skyblue', title='Net Income per Month')
plt.ylabel('Amount ($)')
plt.xlabel('Month')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# # Pie chart of top spending categories
# spending = df[df['Amount'] < 0].groupby('Category')['Amount'].sum()
# spending.plot(kind='pie', autopct='%1.1f%%', startangle=90, title='Spending by Category', cmap='tab20')
# plt.ylabel('')
# plt.tight_layout()
# plt.show()


spending = df[df['Amount'] < 0].groupby('Category')['Amount'].sum()
spending = spending.abs()  # <-- flip negatives to positives

spending.plot(
    kind='pie',
    autopct='%1.1f%%',
    startangle=90,
    title='Spending by Category',
    cmap='tab20'
)
plt.ylabel('')
plt.tight_layout()
plt.show()




