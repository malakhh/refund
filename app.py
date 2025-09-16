import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.title("Detroit Axle Refund Calculator")

kit_url = st.text_input("Paste the Detroit Axle Kit Link Here:")

if kit_url:
    headers = {'User-Agent': 'Mozilla/5.0'}

    # Step 1: Fetch kit page
    res = requests.get(kit_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    # Step 2: Get kit price
    try:
        kit_price_text = soup.select_one('.product-price').text.strip().replace('$','')
        kit_price = float(kit_price_text)
    except:
        st.error("Could not find kit price on page.")
        kit_price = None

    if kit_price:
        # Step 3: Get component links and names
        component_links = []
        component_names = []
        for a in soup.select('a[href*="/product/"]'):
            href = a.get('href')
            name = a.text.strip()
            if href not in component_links and name != '':
                component_links.append(href)
                component_names.append(name)

        # Step 4: Fetch component prices
        component_prices = []
        for link in component_links:
            try:
                res_c = requests.get(link, headers=headers)
                soup_c = BeautifulSoup(res_c.text, 'html.parser')
                price_text = soup_c.select_one('.product-price').text.strip().replace('$','')
                component_prices.append(float(price_text))
            except:
                component_prices.append(None)

        # Step 5: Proportional allocation
        total_individual = sum([p for p in component_prices if p])
        kit_adjusted_prices = [round((p/total_individual)*kit_price,2) for p in component_prices]

        # Step 6: Create DataFrame
        df = pd.DataFrame({
            'Component': component_names,
            'Individual Price': component_prices,
            'Kit-Adjusted Price': kit_adjusted_prices
        })

        # Step 7: Show table with checkboxes for refund
        st.write(f"*Kit Price: ${kit_price}*")
        st.write("Select components to refund:")

        refund_total = 0
        refund_flags = []
        for idx, row in df.iterrows():
            flag = st.checkbox(f"{row['Component']} - ${row['Kit-Adjusted Price']}", key=idx)
            refund_flags.append(flag)
            if flag:
                refund_total += row['Kit-Adjusted Price']

        st.write(f"*Total Refund: ${round(refund_total,2)}*")
