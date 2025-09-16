import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Page setup
st.set_page_config(page_title="Detroit Axle Refund Calculator", layout="wide")
st.title("🚗 Detroit Axle Refund Calculator")

# Sidebar for theme selection
theme = st.sidebar.radio("Choose Theme:", ["Light", "Dark"])
if theme == "Dark":
    st.markdown(
        """
        <style>
        .stApp {background-color: #0e1117; color: #f0f0f0;}
        .css-1d391kg {color: #f0f0f0;}  /* headers */
        .stTextInput>div>div>input {background-color: #1f1f1f; color: #f0f0f0;}
        .stCheckbox>div>label {color: #f0f0f0;}
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        .stApp {background-color: #ffffff; color: #000000;}
        .css-1d391kg {color: #000000;}  /* headers */
        .stTextInput>div>div>input {background-color: #f9f9f9; color: #000000;}
        .stCheckbox>div>label {color: #000000;}
        </style>
        """,
        unsafe_allow_html=True
    )

kit_url = st.text_input("Paste the Detroit Axle Kit Link Here:")

def get_discounted_price(soup):
    selectors = ['.sale-price', '.product-price', '.price-red']
    for sel in selectors:
        tag = soup.select_one(sel)
        if tag and tag.text.strip():
            price_text = tag.text.strip().replace('$','').replace(',','')
            try:
                return float(price_text)
            except:
                continue
    return None

if kit_url:
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Fetch kit page
        res = requests.get(kit_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Kit total price
        kit_price = get_discounted_price(soup)
        if kit_price is None:
            st.error("Could not find kit price on this page. Check the link.")
            st.stop()
        st.subheader(f"Kit Price: ${kit_price}")

        # Component links & names
        component_links = []
        component_names = []
        for a in soup.select('a[href*="/product/"]'):
            href = a.get('href')
            name = a.text.strip()
            if href not in component_links and name != '':
                component_links.append(href)
                component_names.append(name)

        # Fetch component prices
        component_prices = []
        for link in component_links:
            try:
                res_c = requests.get(link, headers=headers)
                soup_c = BeautifulSoup(res_c.text, 'html.parser')
                price = get_discounted_price(soup_c)
                component_prices.append(price)
            except:
                component_prices.append(None)
            time.sleep(0.5)

        # Kit-adjusted prices
        valid_prices = [p for p in component_prices if p]
        total_individual = sum(valid_prices)
        kit_adjusted_prices = [round((p/total_individual)*kit_price,2) if p else None for p in component_prices]
        percentages = [round((p/total_individual)*100,1) if p else None for p in component_prices]

        # Build DataFrame
        df = pd.DataFrame({
            "Component": component_names,
            "Individual Price": component_prices,
            "Kit-Adjusted Price": kit_adjusted_prices,
            "% of Kit": percentages
        })

        # Refund table with checkboxes
        st.write("Select components to refund:")
        refund_total = 0
        refund_flags = []
        for idx, row in df.iterrows():
            flag = st.checkbox(f"{row['Component']} - ${row['Kit-Adjusted Price']} ({row['% of Kit']}%)", key=idx)
            refund_flags.append(flag)
            if flag:
                refund_total += row['Kit-Adjusted Price']

        st.markdown(f"<h2 style='color:green'>💰 Total Refund: ${round(refund_total,2)}</h2>", unsafe_allow_html=True)
        st.text_input("Copy Refund Total:", value=str(round(refund_total,2)), key="copy_refund")

        # Display full table with highlight
        def highlight_refund(val):
            return 'background-color: #d1f7d1;' if val in df['Component'][[i for i,f in enumerate(refund_flags) if f]] else ''

        st.dataframe(df.style.applymap(highlight_refund, subset=['Component']))

    except Exception as e:
        st.error(f"Error fetching kit data: {e}")
