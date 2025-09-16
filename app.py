import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

st.set_page_config(page_title="Detroit Axle Refund Calculator", layout="wide")
st.title("🚗 Detroit Axle Refund Calculator (Cloud-Friendly)")

kit_url = st.text_input("Paste the Detroit Axle Kit Link Here:")

if kit_url:
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # Step 1: Fetch kit page
        res = requests.get(kit_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Step 2: Get kit price
        price_tag = soup.select_one('.product-price')
        if price_tag:
            kit_price = float(price_tag.text.strip().replace('$',''))
        else:
            st.error("Could not find kit price on this page.")
            kit_price = None

        # Step 3: Get component links and names
        component_links = []
        component_names = []
        for a in soup.select('a[href*="/product/"]'):
            href = a.get('href')
            name = a.text.strip()
            if href not in component_links and name != '':
                component_links.append(href)
                component_names.append(name)

        # Step 4: Fetch each component price
        component_prices = []
        for link in component_links:
            try:
                res_c = requests.get(link, headers=headers)
                soup_c = BeautifulSoup(res_c.text, 'html.parser')
                price_tag = soup_c.select_one('.product-price')
                if price_tag:
                    component_prices.append(float(price_tag.text.strip().replace('$','')))
                else:
                    component_prices.append(None)
            except:
                component_prices.append(None)
            time.sleep(0.5)  # polite delay

        # Step 5: Calculate kit-adjusted prices
        total_individual = sum([p for p in component_prices if p])
        kit_adjusted_prices = [round((p/total_individual)*kit_price,2) if p else None for p in component_prices]

        # Step 6: Build DataFrame
        df = pd.DataFrame({
            "Component": component_names,
            "Individual Price": component_prices,
            "Kit-Adjusted Price": kit_adjusted_prices
        })

        # Step 7: Show table with checkboxes
        st.subheader(f"Kit Price: ${kit_price}")
        st.write("Select components to refund:")

        refund_total = 0
        for idx, row in df.iterrows():
            flag = st.checkbox(f"{row['Component']} - ${row['Kit-Adjusted Price']}", key=idx)
            if flag:
                refund_total += row['Kit-Adjusted Price']

        st.markdown(f"### 💰 Total Refund: ${round(refund_total,2)}")

        with st.expander("View Full Component Table"):
            st.dataframe(df)

    except Exception as e:
        st.error(f"Error fetching kit data: {e}")
