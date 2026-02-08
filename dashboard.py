"""Streamlit dashboard for grain price visualization."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

import database


st.set_page_config(
    page_title="Grain Prices - Rolla",
    page_icon="🌾",
    layout="wide"
)

st.title("Grain Price Dashboard - Rolla Location")
st.markdown("*Data from Legacy Cooperative*")


def load_data():
    """Load all price data from database."""
    data = database.get_price_history()
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


def main():
    # Load data
    df = load_data()

    if df.empty:
        st.warning("No data available yet. Run the scraper first:")
        st.code("python scraper.py")
        return

    # Sidebar filters
    st.sidebar.header("Filters")

    # Commodity filter
    commodities = database.get_commodities()
    selected_commodities = st.sidebar.multiselect(
        "Select Commodities",
        options=commodities,
        default=commodities
    )

    # Date range filter
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Filter data
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (
            (df['commodity'].isin(selected_commodities)) &
            (df['timestamp'].dt.date >= start_date) &
            (df['timestamp'].dt.date <= end_date)
        )
        filtered_df = df[mask]
    else:
        filtered_df = df[df['commodity'].isin(selected_commodities)]

    # Current prices section
    st.header("Current Prices")

    latest_prices = database.get_latest_prices()
    if latest_prices:
        latest_df = pd.DataFrame(latest_prices)

        # Display as metric cards
        cols = st.columns(min(len(latest_prices), 4))
        for i, price in enumerate(latest_prices):
            if price['commodity'] in selected_commodities:
                with cols[i % 4]:
                    cash_str = f"${price['cash_price']:.2f}" if price['cash_price'] else "N/A"
                    basis_str = f"Basis: {price['basis']}" if price['basis'] else ""
                    st.metric(
                        label=price['commodity'],
                        value=cash_str,
                        delta=basis_str if basis_str else None
                    )

        # Last updated
        if latest_prices:
            last_update = latest_prices[0].get('timestamp', 'Unknown')
            st.caption(f"Last updated: {last_update}")

    # Price history chart
    st.header("Price History")

    if not filtered_df.empty:
        fig = px.line(
            filtered_df,
            x='timestamp',
            y='cash_price',
            color='commodity',
            title='Cash Prices Over Time',
            labels={
                'timestamp': 'Date',
                'cash_price': 'Cash Price ($)',
                'commodity': 'Commodity'
            }
        )
        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Basis chart
        if 'basis' in filtered_df.columns and filtered_df['basis'].notna().any():
            fig_basis = px.line(
                filtered_df,
                x='timestamp',
                y='basis',
                color='commodity',
                title='Basis Over Time',
                labels={
                    'timestamp': 'Date',
                    'basis': 'Basis',
                    'commodity': 'Commodity'
                }
            )
            st.plotly_chart(fig_basis, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

    # Data table
    st.header("Price Data")

    if not filtered_df.empty:
        display_df = filtered_df[[
            'timestamp', 'commodity', 'cash_price', 'basis',
            'futures_change', 'delivery_start', 'delivery_end'
        ]].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # Export button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"grain_prices_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    # Stats section
    st.header("Statistics")

    if not filtered_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Price Summary")
            summary = filtered_df.groupby('commodity')['cash_price'].agg(['min', 'max', 'mean', 'count'])
            summary.columns = ['Min', 'Max', 'Average', 'Records']
            summary = summary.round(2)
            st.dataframe(summary, use_container_width=True)

        with col2:
            st.subheader("Data Collection")
            st.metric("Total Records", len(df))
            st.metric("Date Range", f"{min_date} to {max_date}")
            st.metric("Commodities Tracked", len(commodities))


if __name__ == "__main__":
    main()
