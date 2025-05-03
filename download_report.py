import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import base64
from io import BytesIO
import json
from fpdf import FPDF

def download_report():
    # ---- HEADER SECTION ----
    st.title("Download Report")

    # Current date and last fetch time
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    last_fetch = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # In a real app, this would come from your database

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Today's Date:** {today}")
    with col2:
        st.info(f"**Last Data Fetch:** {last_fetch}")

    # Sample data - Replace this with your actual data loading logic
    @st.cache_data
    def load_data():
        # Sample data generation - replace with your actual data source
        np.random.seed(42)
        dates = pd.date_range(end=datetime.datetime.now(), periods=100).tolist()
        data = {
            'Date': dates,
            'Customer': np.random.choice(['A', 'B', 'C', 'D', 'E'], size=100),
            'Sales': np.random.randint(100, 1000, size=100),
            'Units': np.random.randint(1, 50, size=100),
            'Region': np.random.choice(['North', 'South', 'East', 'West'], size=100)
        }
        df = pd.DataFrame(data)
        return df

    df = load_data()

    # ---- DATA PREVIEW SECTION ----
    st.header("Data Preview")
    st.dataframe(df.head(10), use_container_width=True)

    # Basic stats
    st.subheader("Basic Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Records", df.shape[0])
        st.metric("Total Sales", f"${df['Sales'].sum():,.2f}")
    with col2:
        st.metric("Average Sales", f"${df['Sales'].mean():,.2f}")
        st.metric("Total Units Sold", df['Units'].sum())

    # ---- CHARTS SECTION ----
    st.header("Key Insights")

    tab1, tab2, tab3 = st.tabs(["Sales by Region", "Sales Trend", "Customer Distribution"])

    with tab1:
        # Sales by Region chart
        fig, ax = plt.subplots(figsize=(7, 4))
        region_sales = df.groupby('Region')['Sales'].sum().reset_index()
        sns.barplot(x='Region', y='Sales', data=region_sales, ax=ax)
        ax.set_title('Total Sales by Region')
        ax.set_ylabel('Sales ($)')
        st.pyplot(fig)

    with tab2:
        # Sales Trend chart
        fig, ax = plt.subplots(figsize=(7, 4))
        df['Date'] = pd.to_datetime(df['Date'])
        sales_trend = df.groupby(df['Date'].dt.strftime('%Y-%m-%d'))['Sales'].sum().reset_index()
        sales_trend = sales_trend.tail(30)  # Last 30 days
        plt.plot(sales_trend['Date'], sales_trend['Sales'])
        plt.xticks(rotation=45)
        ax.set_title('Sales Trend (Last 30 Days)')
        ax.set_ylabel('Sales ($)')
        st.pyplot(fig)

    with tab3:
        # Customer Distribution chart
        fig, ax = plt.subplots(figsize=(7, 4))
        customer_sales = df.groupby('Customer')['Sales'].sum().reset_index()
        sns.barplot(x='Customer', y='Sales', data=customer_sales, ax=ax)
        ax.set_title('Sales by Customer')
        ax.set_ylabel('Sales ($)')
        st.pyplot(fig)

    # ---- DOWNLOAD SECTION ----
    st.header("Export Options")

    # Helper functions for file downloads
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Sheet1', index=False)
        processed_data = output.getvalue()
        return processed_data

    def get_csv_download_link(df):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        return b64

    def get_json_download_link(df):
        json_str = df.to_json(orient='records')
        b64 = base64.b64encode(json_str.encode()).decode()
        return b64

    def create_download_report(df):
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Download Report', 0, 1, 'C')
        
        # Date
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Generated on: {today}', 0, 1)
        pdf.cell(0, 10, f'Last Data Fetch: {last_fetch}', 0, 1)
        
        # Data Summary
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Data Summary', 0, 1)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Total Records: {df.shape[0]}', 0, 1)
        pdf.cell(0, 10, f'Total Sales: ${df["Sales"].sum():,.2f}', 0, 1)
        pdf.cell(0, 10, f'Average Sales: ${df["Sales"].mean():,.2f}', 0, 1)
        
        # Region breakdown
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Sales by Region', 0, 1)
        pdf.set_font('Arial', '', 12)
        
        region_sales = df.groupby('Region')['Sales'].sum().reset_index()
        for _, row in region_sales.iterrows():
            pdf.cell(0, 10, f'{row["Region"]}: ${row["Sales"]:,.2f}', 0, 1)
        
        # Output PDF as bytes
        pdf_output = BytesIO()
        pdf.output(dest='S').encode('latin-1')
        return pdf_output.getvalue()

    # Download buttons in a nice layout
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False),
            file_name=f"report_data_{today}.csv",
            mime="text/csv",
        )

    with col2:
        st.download_button(
            label="Download JSON",
            data=df.to_json(orient='records'),
            file_name=f"report_data_{today}.json",
            mime="application/json",
        )

    with col3:
        st.download_button(
            label="Download PDF Report",
            data=create_download_report(df),
            file_name=f"full_report_{today}.pdf",
            mime="application/pdf",
        )

    # Excel download as a separate button (since Excel is often preferred)
    st.download_button(
        label="Download Excel",
        data=to_excel(df),
        file_name=f"report_data_{today}.xlsx",
        mime="application/vnd.ms-excel",
    )

    # Footer with filtering options
    st.header("Filter Data")
    st.caption("Filter the data before downloading")

    # Simple filter options
    selected_regions = st.multiselect("Select Regions", df['Region'].unique(), df['Region'].unique())
    selected_customers = st.multiselect("Select Customers", df['Customer'].unique(), df['Customer'].unique())

    # Filter the data
    filtered_df = df[(df['Region'].isin(selected_regions)) & (df['Customer'].isin(selected_customers))]

    # Show filtered data
    if len(filtered_df) > 0:
        st.subheader("Filtered Data Preview")
        st.dataframe(filtered_df.head(10), use_container_width=True)
        st.info(f"Filtered results: {len(filtered_df)} records")
        
        # Download filtered data
        st.subheader("Download Filtered Data")
        st.download_button(
            label="Download Filtered CSV",
            data=filtered_df.to_csv(index=False),
            file_name=f"filtered_report_{today}.csv",
            mime="text/csv",
        )
    else:
        st.warning("No data matches your filter criteria")