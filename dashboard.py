import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Dashboard E-commerce",
    page_icon="📊",
    layout="wide"
)

st.title("Dashboard Analisis E-commerce")
st.markdown("Dashboard untuk visualisasi data e-commerce.")

@st.cache_data
def load_data():
    order_items_df = pd.read_csv('order_items_dataset.csv')
    customers_df = pd.read_csv('customers_dataset.csv')
    order_payments_df = pd.read_csv('order_payments_dataset.csv')
    products_df = pd.read_csv('products_dataset.csv')
    sellers_df = pd.read_csv('sellers_dataset.csv')
    category_translation_df = pd.read_csv('product_category_name_translation.csv')

    order_items_df['shipping_limit_date'] = pd.to_datetime(order_items_df['shipping_limit_date'])

    products_df = products_df.merge(
        category_translation_df, 
        on='product_category_name', 
        how='left'
    )

    products_df['product_category_name_english'] = products_df['product_category_name_english'].fillna(
        products_df['product_category_name']
    )
    
    return order_items_df, customers_df, order_payments_df, products_df, sellers_df

try:
    order_items_df, customers_df, order_payments_df, products_df, sellers_df = load_data()
    data_loaded = True
    st.success("Data berhasil dimuat!")
except Exception as e:
    st.error(f"Terjadi kesalahan saat memuat data: {e}")
    data_loaded = False

if data_loaded:
    st.sidebar.header("Filter")
    
    states = sorted(customers_df['customer_state'].unique().tolist())
    selected_states = st.sidebar.multiselect("Pilih State", states, default=states[:5])
    
    tab1, tab2, tab3, tab4 = st.tabs(["Pembayaran", "Kategori Produk", "Kota", "Produk Terlaris"])
    
    with tab1:
        st.header("Analisis Pembayaran")

        payment_counts = order_payments_df['payment_type'].value_counts()

        fig1 = px.bar(
            x=payment_counts.index,
            y=payment_counts.values,
            title='Jumlah Pengguna berdasarkan Tipe Pembayaran',
            labels={'x': 'Tipe Pembayaran', 'y': 'Jumlah Pengguna'},
            color=payment_counts.values,
            color_continuous_scale='Blues'
        )
        fig1.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)

        fig1_pie = px.pie(
            values=payment_counts.values,
            names=payment_counts.index,
            title='Distribusi Tipe Pembayaran',
            hole=0.4
        )
        st.plotly_chart(fig1_pie, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Transaksi", f"{len(order_payments_df):,}")
        with col2:
            avg_payment = order_payments_df['payment_value'].mean()
            st.metric("Rata-rata Nilai Pembayaran", f"R$ {avg_payment:.2f}")
        with col3:
            most_common = payment_counts.idxmax()
            st.metric("Metode Pembayaran Terpopuler", most_common)
    
    with tab2:
        st.header("Analisis Kategori Produk")

        product_price_by_category = order_items_df.merge(
            products_df[['product_id', 'product_category_name', 'product_category_name_english']], 
            on='product_id', 
            how='left'
        )
        
        category_avg_price = product_price_by_category.groupby(
            'product_category_name_english'
        )['price'].mean().sort_values()
        
        bottom5 = category_avg_price.head(5)
        top5 = category_avg_price.tail(5)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig2 = px.bar(
                x=top5.index,
                y=top5.values,
                title='5 Kategori Teratas berdasarkan Harga Rata-Rata',
                labels={'x': 'Kategori Produk', 'y': 'Harga Rata-Rata (R$)'},
                color=top5.values,
                color_continuous_scale='Greens'
            )
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            fig3 = px.bar(
                x=bottom5.index,
                y=bottom5.values,
                title='5 Kategori Terbawah berdasarkan Harga Rata-rata',
                labels={'x': 'Kategori Produk', 'y': 'Harga Rata-Rata (R$)'},
                color=bottom5.values,
                color_continuous_scale='Reds_r'
            )
            fig3.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)
    
    with tab3:
        st.header("Analisis Kota")

        filtered_customers = customers_df[customers_df['customer_state'].isin(selected_states)]
        filtered_sellers = sellers_df[sellers_df['seller_state'].isin(selected_states)]

        customer_top = (
            filtered_customers['customer_city']
            .value_counts()
            .head(5)
            .rename_axis('city')
            .reset_index(name='customer_count')
        )

        seller_top = (
            filtered_sellers['seller_city']
            .value_counts()
            .head(5)
            .rename_axis('city')
            .reset_index(name='seller_count')
        )

        combined = pd.merge(customer_top, seller_top, on='city', how='outer').fillna(0)

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=combined['city'],
            y=combined['customer_count'],
            name='Customers',
            marker_color='royalblue'
        ))
        fig4.add_trace(go.Bar(
            x=combined['city'],
            y=combined['seller_count'],
            name='Sellers',
            marker_color='orange'
        ))
        
        fig4.update_layout(
            title='Top 5 Cities: Customer & Seller Counts',
            xaxis_title='Kota',
            yaxis_title='Jumlah',
            xaxis_tickangle=-45,
            barmode='group'
        )
        
        st.plotly_chart(fig4, use_container_width=True)

      
    with tab4:
        st.header("Analisis Produk Terlaris")
        
        top5_products = (
            order_items_df
            .merge(
                products_df[['product_id', 'product_category_name', 'product_category_name_english']],
                on='product_id', 
                how='left'
            )
            .groupby(['product_id', 'product_category_name_english'])
            .size()
            .reset_index(name='sales_volume')
            .sort_values('sales_volume', ascending=False)
            .drop_duplicates(subset='product_category_name_english', keep='first')
            .sort_values('sales_volume', ascending=False)
            .head(5)
        )
        
        fig5 = px.bar(
            top5_products,
            x='product_category_name_english',
            y='sales_volume',
            title='Top 5 Produk Terlaris',
            labels={'product_category_name_english': 'Kategori Produk', 'sales_volume': 'Volume Penjualan'},
            color='sales_volume',
            color_continuous_scale='Viridis'
        )
        fig5.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig5, use_container_width=True)
        
        st.subheader("Insight Produk")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_products = len(products_df['product_id'].unique())
            st.metric("Total Produk", f"{total_products:,}")
        
        with col2:
            total_categories = len(products_df['product_category_name'].unique())
            st.metric("Total Kategori", f"{total_categories:,}")
        
        with col3:
            avg_product_price = order_items_df['price'].mean()
            st.metric("Harga Rata-rata", f"R$ {avg_product_price:.2f}")
            
        st.subheader("Sampel Data Produk Terlaris")
        st.dataframe(top5_products)

else:
    st.warning("Silakan upload file data terlebih dahulu untuk melihat dashboard.")
    
    uploaded_files = st.file_uploader(
        "Upload file CSV", 
        accept_multiple_files=True,
        type=['csv']
    )

st.markdown("---")
st.caption("Dashboard E-commerce Analytics")