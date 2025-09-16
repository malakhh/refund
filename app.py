import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(page_title="Detroit Axle Refund Calculator", layout="wide")
st.title("🚗 Detroit Axle Refund Calculator")

kit_url = st.text_input("Paste the Detroit Axle Kit Link Here:")

if kit_url:
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # Fetch kit page
        res = requests.get(kit_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Get kit price
        kit_price_text = soup.select_one('.product-price').text.strip().replace('$','')
        kit_price = float(kit_price_text)
        st.subheader(f"Kit Price: ${kit_price}")

        # Get component links and names
        component_links = []
        component_names = []
        for a in soup.select('a[href*="/product/"]'):
            href = a.get('href')
            name = a.text.strip()
            if href not in component_links and name != '':
                component_links.append(href)
                component_names.append(name)

        # Fetch individual component prices
        component_prices = []
        for link in component_links:
            try:
                res_c = requests.get(link, headers=headers)
                soup_c = BeautifulSoup(res_c.text, 'html.parser')
                price_text = soup_c.select_one('.product-price').text.strip().replace('$','')
                component_prices.append(float(price_text))
            except:
                component_prices.append(None)

        # Proportional allocation
        total_individual = sum([p for p in component_prices if p])
        kit_adjusted_prices = [round((p/total_individual)*kit_price,2) if p else None for p in component_prices]

        # Create DataFrame
        df = pd.DataFrame({
            'Component': component_names,
            'Individual Price': component_prices,
            'Kit-Adjusted Price': kit_adjusted_prices
        })

        # Show table with checkboxes for refund
        st.write("### Select components to refund:")
        refund_total = 0
        for idx, row in df.iterrows():
            flag = st.checkbox(f"{row['Component']} - ${row['Kit-Adjusted Price']}", key=idx)
            if flag:
                refund_total += row['Kit-Adjusted Price']

        st.markdown(f"### 💰 Total Refund: ${round(refund_total,2)}")

        # Optional: show full table for reference
        with st.expander("View Full Component Table"):
            st.dataframe(df)

    except Exception as e:
        st.error(f"Error fetching kit data: {e}")
