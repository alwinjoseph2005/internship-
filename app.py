import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Nassau Candy Distributor Dashboard", layout="wide", page_icon="🍬")

# --- CUSTOM CSS FOR WARM TONE & PREMIUM AESTHETIC ---
st.markdown("""
<style>
    /* Main Background & Text */
    .stApp {
        background-color: #FAFAFA;
        color: #4A3B32;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #D48C70;
        font-weight: 700;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #FFF1E6;
        border-right: 1px solid #F0B3A6;
    }
    
    /* Metrics / KPIs */
    [data-testid="stMetricValue"] {
        color: #8A5A44;
        font-size: 1.8rem !important;
        font-weight: 800;
    }
    [data-testid="stMetricLabel"] {
        color: #6D4C41;
        font-size: 1rem !important;
        font-weight: 600;
    }

    /* DataFrame custom borders */
    .dataframe {
        border: 1px solid #F0B3A6 !important;
    }
    
    hr {
        border-top: 2px solid #F0B3A6;
    }
</style>
""", unsafe_allow_html=True)

# --- FACTORY DATA ---
factory_data = {
    "Factory": ["Lot's O' Nuts", "Wicked Choccy's", "Sugar Shack", "Secret Factory", "The Other Factory"],
    "Latitude": [32.881893, 32.076176, 48.11914, 41.446333, 35.1175],
    "Longitude": [-111.768036, -81.088371, -96.18115, -90.565487, -89.971107]
}
factories_df = pd.DataFrame(factory_data)

product_factory_map = {
    "Wonka Bar - Nutty Crunch Surprise": "Lot's O' Nuts",
    "Wonka Bar - Fudge Mallows": "Lot's O' Nuts",
    "Wonka Bar -Scrumdiddlyumptious": "Lot's O' Nuts",
    "Wonka Bar - Milk Chocolate": "Wicked Choccy's",
    "Wonka Bar - Triple Dazzle Caramel": "Wicked Choccy's",
    "Laffy Taffy": "Sugar Shack",
    "SweeTARTS": "Sugar Shack",
    "Nerds": "Sugar Shack",
    "Fun Dip": "Sugar Shack",
    "Fizzy Lifting Drinks": "Sugar Shack",
    "Everlasting Gobstopper": "Secret Factory",
    "Hair Toffee": "The Other Factory",
    "Lickable Wallpaper": "Secret Factory",
    "Wonka Gum": "Secret Factory",
    "Kazookles": "The Other Factory"
}

# --- DATA LOADING ---
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau Candy Distributor.csv")
    
    # Cleaning
    df = df[(df['Sales'] > 0) & (df['Cost'] > 0)]
    df = df.dropna(subset=['Units'])
    df = df[df['Units'] > 0]
    
    # Standardization
    df['Product Name'] = df['Product Name'].str.strip()
    df['Division'] = df['Division'].str.strip()
    
    # Dates
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y', errors='coerce')
    df = df.dropna(subset=['Order Date'])
    
    # KPIs per row
    df['Gross Margin %'] = (df['Gross Profit'] / df['Sales']) * 100
    df['Profit per unit'] = df['Gross Profit'] / df['Units']
    
    # Map Factories
    df['Factory'] = df['Product Name'].map(product_factory_map)
    df = pd.merge(df, factories_df, on='Factory', how='left')

    return df

data = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2619/2619565.png", width=100)
st.sidebar.title("Nassau Controls")
st.sidebar.markdown("Use the filters below to slice the dashboard data.")

# Date Filter
min_date = data['Order Date'].min().date()
max_date = data['Order Date'].max().date()
date_range = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

if len(date_range) == 2:
    start_date, end_date = date_range
    mask_date = (data['Order Date'].dt.date >= start_date) & (data['Order Date'].dt.date <= end_date)
else:
    mask_date = pd.Series(True, index=data.index)

# Division Filter
divisions = ['All'] + list(data['Division'].unique())
selected_division = st.sidebar.selectbox("Select Division", divisions)
mask_div = (data['Division'] == selected_division) if selected_division != 'All' else pd.Series(True, index=data.index)

# Product Search
product_search = st.sidebar.text_input("Product Search", "")
if product_search:
    mask_prod = data['Product Name'].str.contains(product_search, case=False, na=False)
else:
    mask_prod = pd.Series(True, index=data.index)

# Margin Threshold Slider
margin_thresh = st.sidebar.slider("Minimum Gross Margin % Threshold", min_value=0, max_value=100, value=0, step=5)

# APPLY FILTERS
filtered_data = data[mask_date & mask_div & mask_prod]
# Apply margin threshold at the aggregated product level, not individual row level

# --- DATA AGGREGATION based on filters ---
if filtered_data.empty:
    st.warning("No data matches the current filters. Please adjust the sidebar controls.")
    st.stop()

prod_agg = filtered_data.groupby(['Product Name', 'Division', 'Factory']).agg(
    Total_Sales=('Sales', 'sum'),
    Total_Profit=('Gross Profit', 'sum'),
    Total_Units=('Units', 'sum'),
    Total_Cost=('Cost', 'sum'),
    Latitude=('Latitude', 'first'),
    Longitude=('Longitude', 'first')
).reset_index()

prod_agg['Gross Margin %'] = (prod_agg['Total_Profit'] / prod_agg['Total_Sales']) * 100
prod_agg['Profit per unit'] = prod_agg['Total_Profit'] / prod_agg['Total_Units']

# Final threshold filter
prod_agg = prod_agg[prod_agg['Gross Margin %'] >= margin_thresh]

if prod_agg.empty:
    st.warning("No products meet the required Gross Margin threshold. Please adjust the slider.")
    st.stop()

# Re-filter raw data based on products that passed the threshold
valid_products = prod_agg['Product Name'].unique()
filtered_data = filtered_data[filtered_data['Product Name'].isin(valid_products)]


# --- MAIN DASHBOARD LAYOUT ---
st.title("🍬 Product Line Profitability & Margin Performance Analysis")
st.markdown("**Nassau Candy Distributor** - *Internship Final Year Project*")
st.markdown("---")

# TOP HIGHLIGHT KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${prod_agg['Total_Sales'].sum():,.2f}")
col2.metric("Total Gross Profit", f"${prod_agg['Total_Profit'].sum():,.2f}")
col3.metric("Avg Gross Margin", f"{(prod_agg['Total_Profit'].sum() / prod_agg['Total_Sales'].sum()) * 100:.1f}%")
col4.metric("Total Units Sold", f"{int(prod_agg['Total_Units'].sum()):,}")

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Product Profitability", 
    "📊 Division Performance", 
    "⚠️ Cost Diagnostics", 
    "🎯 Concentration Risk",
    "🗺️ Factory Geospatial"
])

# WARM COLORS PALETTE
warm_colors = ['#D48C70', '#E5A585', '#F0B3A6', '#8A5A44', '#C37A61']

# ==========================================
# TAB 1: PRODUCT PROFITABILITY OVERVIEW
# ==========================================
with tab1:
    st.header("Product Profitability Overview")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Margin Leaderboard (%)")
        st.dataframe(prod_agg[['Product Name', 'Division', 'Gross Margin %', 'Profit per unit']]
                     .sort_values(by='Gross Margin %', ascending=False)
                     .head(10)
                     .style.format({"Gross Margin %": "{:.1f}%", "Profit per unit": "${:.2f}"}),
                     use_container_width=True)
                     
    with c2:
        st.subheader("Profit Contribution")
        fig1 = px.pie(prod_agg, values='Total_Profit', names='Product Name', 
                      color_discrete_sequence=px.colors.sequential.Oranges,
                      hole=0.4)
        fig1.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#FAFAFA', width=2)))
        st.plotly_chart(fig1, use_container_width=True)

# ==========================================
# TAB 2: DIVISION PERFORMANCE DASHBOARD
# ==========================================
with tab2:
    st.header("Division Performance Dashboard")
    div_agg = prod_agg.groupby('Division').agg(
        Total_Sales=('Total_Sales', 'sum'),
        Total_Profit=('Total_Profit', 'sum')
    ).reset_index()
    div_agg['Gross Margin %'] = (div_agg['Total_Profit'] / div_agg['Total_Sales']) * 100

    c1, c2 = st.columns(2)
    
    with c1:
        fig_div = go.Figure(data=[
            go.Bar(name='Revenue', x=div_agg['Division'], y=div_agg['Total_Sales'], marker_color='#E5A585'),
            go.Bar(name='Profit', x=div_agg['Division'], y=div_agg['Total_Profit'], marker_color='#8A5A44')
        ])
        fig_div.update_layout(barmode='group', title="Revenue vs Profit Imbalance by Division",
                              plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_div, use_container_width=True)

    with c2:
        fig_margin = px.bar(div_agg, x='Division', y='Gross Margin %', 
                            color='Division', color_discrete_sequence=warm_colors,
                            title="Average Margin Distribution")
        fig_margin.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        fig_margin.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
        st.plotly_chart(fig_margin, use_container_width=True)

# ==========================================
# TAB 3: COST VS MARGIN DIAGNOSTICS
# ==========================================
with tab3:
    st.header("Cost vs Margin Diagnostics")
    st.markdown("Identify cost-heavy, margin-poor products. Products in the **Bottom Right** represent significant margin risk.")
    
    fig_scatter = px.scatter(prod_agg, x='Total_Cost', y='Gross Margin %', 
                             size='Total_Sales', color='Division', hover_name='Product Name',
                             color_discrete_sequence=warm_colors,
                             labels={"Total_Cost": "Total Manufacturing Cost ($)", "Gross Margin %": "Gross Margin (%)"})
    
    avg_margin = prod_agg['Total_Profit'].sum() / prod_agg['Total_Sales'].sum() * 100
    avg_cost = prod_agg['Total_Cost'].mean()
    
    fig_scatter.add_hline(y=avg_margin, line_dash="dash", line_color="gray", annotation_text="Avg Margin")
    fig_scatter.add_vline(x=avg_cost, line_dash="dash", line_color="gray", annotation_text="Avg Cost")
    fig_scatter.update_layout(plot_bgcolor='#FAFAFA', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Risk Flags
    risk_products = prod_agg[(prod_agg['Gross Margin %'] < avg_margin) & (prod_agg['Total_Cost'] > avg_cost)]
    if not risk_products.empty:
        st.error(f"🚩 **Margin Risk Flags Detected:** {len(risk_products)} product(s) require repricing or discontinuation review.")
        st.dataframe(risk_products[['Product Name', 'Total_Cost', 'Gross Margin %', 'Total_Profit']]
                     .style.format({"Total_Cost": "${:,.2f}", "Gross Margin %": "{:.1f}%", "Total_Profit": "${:,.2f}"}),
                     use_container_width=True)
    else:
        st.success("✅ No extreme margin risks detected in the current view.")

# ==========================================
# TAB 4: PROFIT CONCENTRATION (PARETO)
# ==========================================
with tab4:
    st.header("Profit Concentration (80/20 Rule)")
    
    # Pareto Chart for Sales
    prod_pareto = prod_agg.sort_values(by='Total_Sales', ascending=False)
    prod_pareto['CumPercentage'] = 100 * prod_pareto['Total_Sales'].cumsum() / prod_pareto['Total_Sales'].sum()
    
    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Bar(x=prod_pareto['Product Name'], y=prod_pareto['Total_Sales'], name='Sales', marker_color='#E5A585'))
    fig_pareto.add_trace(go.Scatter(x=prod_pareto['Product Name'], y=prod_pareto['CumPercentage'], name='Cumulative %', 
                                    mode='lines+markers', line=dict(color='#8A5A44', width=3), yaxis='y2'))
    
    fig_pareto.update_layout(
        title="Revenue Pareto Chart", 
        yaxis=dict(title='Sales ($)'),
        yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0, 105]),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified"
    )
    fig_pareto.add_hline(y=80, line_dash="solid", line_color="red", yref="y2", annotation_text="80% Threshold")
    st.plotly_chart(fig_pareto, use_container_width=True)
    
    # State Dependency Indicator
    st.subheader("Geographic Dependency")
    state_agg = filtered_data.groupby('State/Province').agg(Total_Sales=('Sales', 'sum')).reset_index()
    state_agg = state_agg.sort_values(by='Total_Sales', ascending=False)
    
    top_5_percent = (state_agg['Total_Sales'].head(5).sum() / state_agg['Total_Sales'].sum()) * 100
    if top_5_percent > 40:
        st.warning(f"⚠️ **High Geographic Hazard:** The top 5 states drive **{top_5_percent:.1f}%** of total selected revenue. This represents significant systemic risk.")
    
    st.dataframe(state_agg.head(10).style.format({"Total_Sales": "${:,.2f}"}), use_container_width=True)

# ==========================================
# TAB 5: FACTORY GEOSPATIAL CORRELATION
# ==========================================
with tab5:
    st.header("Factory Source & Profitability")
    st.markdown("Visualizing origin factories. Point size indicates total profit generated by products manufactured there.")
    
    fac_agg = prod_agg.groupby(['Factory', 'Latitude', 'Longitude']).agg(
        Total_Profit=('Total_Profit', 'sum'),
        Total_Sales=('Total_Sales', 'sum'),
        Products_Manufactured=('Product Name', 'count')
    ).reset_index()

    fig_map = px.scatter_mapbox(fac_agg, lat="Latitude", lon="Longitude", hover_name="Factory",
                                hover_data=["Total_Profit", "Total_Sales", "Products_Manufactured"],
                                size="Total_Profit", color="Total_Profit", 
                                color_continuous_scale=px.colors.sequential.Oranges,
                                zoom=3, height=500)
    
    fig_map.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)
