import pandas as pd
import numpy as np

file_path = "Nassau Candy Distributor.csv"

# 1. Load Data
df = pd.read_csv(file_path)
print(f"Original shape: {df.shape}")

# 2. Data Cleaning & Validation
# Validate cost and sales values (>0)
df = df[(df['Sales'] > 0) & (df['Cost'] > 0)]

# Handle missing/invalid units 
df = df.dropna(subset=['Units'])
df = df[df['Units'] > 0]

# Standardize product and division labels
df['Product Name'] = df['Product Name'].str.strip()
df['Division'] = df['Division'].str.strip()

# Print missing profit records if any, wait profit is calculated
# Calculate Profitability metrics
df['Gross Margin %'] = (df['Gross Profit'] / df['Sales']) * 100
df['Profit per unit'] = df['Gross Profit'] / df['Units']

print(f"Cleaned shape: {df.shape}")

# 3. Product-Level Profitability Analysis
product_grouped = df.groupby(['Division', 'Product Name']).agg(
    Total_Sales=('Sales', 'sum'),
    Total_Profit=('Gross Profit', 'sum'),
    Total_Units=('Units', 'sum'),
    Total_Cost=('Cost', 'sum')
).reset_index()

product_grouped['Gross Margin %'] = (product_grouped['Total_Profit'] / product_grouped['Total_Sales']) * 100
product_grouped['Profit per unit'] = product_grouped['Total_Profit'] / product_grouped['Total_Units']

print("\n--- PRODUCT LEADERBOARD BY PROFIT ---")
print(product_grouped.sort_values(by='Total_Profit', ascending=False)[['Product Name', 'Total_Profit', 'Gross Margin %']].head(10).to_string(index=False))

print("\n--- PRODUCT LEADERBOARD BY MARGIN ---")
print(product_grouped.sort_values(by='Gross Margin %', ascending=False)[['Product Name', 'Total_Profit', 'Gross Margin %']].head(10).to_string(index=False))

# 4. Division-Level Performance
div_grouped = df.groupby('Division').agg(
    Total_Sales=('Sales', 'sum'),
    Total_Profit=('Gross Profit', 'sum')
).reset_index()
div_grouped['Average Margin %'] = (div_grouped['Total_Profit'] / div_grouped['Total_Sales']) * 100

print("\n--- DIVISION PERFORMANCE ---")
print(div_grouped.to_string(index=False))

# 5. Profit Concentration (Pareto)
product_grouped = product_grouped.sort_values(by='Total_Sales', ascending=False)
product_grouped['Cum_Sales'] = product_grouped['Total_Sales'].cumsum()
product_grouped['Cum_Sales_%'] = 100 * product_grouped['Cum_Sales'] / product_grouped['Total_Sales'].sum()

prod_sales_80 = product_grouped[product_grouped['Cum_Sales_%'] <= 80]
print(f"\n--- PARETO (SALES) ---")
print(f"Products driving 80% of revenue: {len(prod_sales_80)} out of {len(product_grouped)} ({(len(prod_sales_80)/len(product_grouped))*100:.1f}%)")

product_grouped = product_grouped.sort_values(by='Total_Profit', ascending=False)
product_grouped['Cum_Profit'] = product_grouped['Total_Profit'].cumsum()
product_grouped['Cum_Profit_%'] = 100 * product_grouped['Cum_Profit'] / product_grouped['Total_Profit'].sum()

prod_profit_80 = product_grouped[product_grouped['Cum_Profit_%'] <= 80]
print(f"\n--- PARETO (PROFIT) ---")
print(f"Products driving 80% of profit: {len(prod_profit_80)} out of {len(product_grouped)} ({(len(prod_profit_80)/len(product_grouped))*100:.1f}%)")

# Congestion/Dependency by State
state_grouped = df.groupby('State/Province').agg(Total_Sales=('Sales', 'sum')).reset_index()
state_grouped = state_grouped.sort_values(by='Total_Sales', ascending=False)
top_5_states = state_grouped.head(5)
top_5_sales_pct = (top_5_states['Total_Sales'].sum() / state_grouped['Total_Sales'].sum()) * 100
print(f"\n--- DEPENDENCY RISK ---")
print(f"Top 5 states drive {top_5_sales_pct:.1f}% of total revenue:")
print(top_5_states.to_string(index=False))

# 6. Cost vs Margin Diagnostics (Identify cost-heavy, margin-poor)
avg_margin = df['Gross Profit'].sum() / df['Sales'].sum() * 100
avg_cost = product_grouped['Total_Cost'].mean()

risk_products = product_grouped[(product_grouped['Gross Margin %'] < avg_margin) & (product_grouped['Total_Cost'] > avg_cost)]
print(f"\n--- MARGIN RISK PRODUCTS (Below avg margin & above avg cost) ---")
print(risk_products[['Product Name', 'Total_Cost', 'Gross Margin %', 'Total_Profit']].to_string(index=False))
