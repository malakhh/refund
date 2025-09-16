import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re

# Streamlit page setup
st.set_page_config(page_title="Detroit Axle Refund Calculator", layout="wide")
st.title("🚗 Detroit Axle Refund Calculator")

# Theme toggle
theme = st.sidebar.radio("Choose Theme:", ["Light", "Dark"])
if theme == "Dark":
    st.markdown("""
        <style>
        .stApp {background-color: #0e1117; color: #f0f0f0;}
        .stTextInput>div>div>input {background-color: #1f1f1f; color: #f0f0f0;}
        .stCheckbox>div>label {color: #f0f0f0;}
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp {background-color: #ffffff; color: #000000;}
        .stTextInput>div>div>input {background-color: #f9f9f9; color: #000000;}
        .stCheckbox>div>label {color: #000000;}
        </style>
        """, unsafe_allow_html=True)

# Input
kit_url = st.text_input("Paste the Detroit Axle Kit Link Here:")

# Function to extract second $ price from text
def extract_second_price(text):
    matches = re.findall(r'\$([0-9,]+(?:\.[0-9]{1,2})?)', text)
    if len(matches) >= 2:
        return float(matches[1].replace(',',''))
    elif matches:
        return float(matches[0].replace(',',''))
    else:
        return None

# Main processing
if kit_url:
    st.info("Fetching kit and component prices. Please wait...")
    try:
        # Selenium setup
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)

        # Load kit page
        driver.get(kit_url)
        time.sleep(3)

        # Extract kit price (second $ = red price)
        kit_text = driver.find_element(By.TAG_NAME, "body").text
        kit_price = extract_second_price(kit_text)
        if not kit_price:
            st.error("Could not detect kit price automatically.")
            driver.quit()
            st.stop()
        st.subheader(f"Kit Price: ${kit_price}")

        # Extract component links
        component_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")
        component_links = []
        component_names = []
        for el in component_elements:
            href = el.get_attribute("href")
            name = el.text.strip()
            if href not in component_links and name != '':
                component_links.append(href)
                component_names.append(name)

        # Extract component prices
        component_prices = []
        for link in component_links:
            driver.get(link)
            time.sleep(2)
            comp_text = driver.find_element(By.TAG_NAME, "body").text
            price = extract_second_price(comp_text)
            component_prices.append(price)

        driver.quit()

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

        # Refund selection
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

        # Highlight table
        def highlight_refund(val):
            return 'background-color: #d1f7d1;' if val in df['Component'][[i for i,f in enumerate(refund_flags) if f]] else ''

        st.dataframe(df.style.applymap(highlight_refund, subset=['Component']))

    except Exception as e:
        st.error(f"Error fetching kit or component prices: {e}")
