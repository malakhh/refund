import streamlit as st
import pandas as pd
import re
import asyncio
import subprocess
import sys

# --- Automatically install Playwright Chromium on Streamlit Cloud ---
subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

from playwright.async_api import async_playwright

# --- Streamlit page setup ---
st.set_page_config(page_title="Detroit Axle Refund Calculator", layout="wide")
st.title("🚗 Detroit Axle Refund Calculator")

# --- Theme toggle ---
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

# --- Choose kit price mode ---
mode = st.radio("Choose kit price mode:", ["Automatic from Kit", "Manual Entry"])
if mode == "Manual Entry":
    manual_kit_price = st.number_input("Enter Kit Price ($):", min_value=0.0, format="%.2f")
else:
    manual_kit_price = None

# --- Kit link input ---
kit_url = st.text_input("Paste the Detroit Axle Kit Link Here:")

# --- Function to extract second $ price ---
def extract_second_price(text):
    matches = re.findall(r'\$([0-9,]+(?:\.[0-9]{1,2})?)', text)
    if len(matches) >= 2:
        return float(matches[1].replace(',',''))
    elif matches:
        return float(matches[0].replace(',',''))
    else:
        return None

# --- Function to fetch kit and component prices using Playwright ---
async def fetch_prices(kit_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(kit_url)
        await page.wait_for_timeout(3000)  # wait for JS to load

        # Kit price (automatic)
        kit_price_auto = extract_second_price(await page.content())

        # Component links
        component_elements = await page.query_selector_all("a[href*='/product/']")
        component_links = []
        component_names = []
        for el in component_elements:
            href = await el.get_attribute("href")
            name = await el.inner_text()
            name = name.strip()
            if href not in component_links and name != '':
                component_links.append(href)
                component_names.append(name)

        # Component prices
        component_prices = []
        for link in component_links:
            await page.goto(link)
            await page.wait_for_timeout(2000)
            comp_text = await page.content()
            price = extract_second_price(comp_text)
            component_prices.append(price)

        await browser.close()
        return kit_price_auto, component_names, component_prices

# --- Main logic ---
if kit_url:
    st.info("Fetching kit and component prices. Please wait...")

    # Fetch automatic prices only if needed
    if mode == "Automatic from Kit":
        try:
            kit_price_auto, component_names, component_prices = asyncio.run(fetch_prices(kit_url))
            kit_price = kit_price_auto
        except Exception as e:
            st.error(f"Error fetching kit or component prices: {e}")
            st.stop()
    else:
        kit_price = manual_kit_price
        # Still need component names and prices
        try:
            _, component_names, component_prices = asyncio.run(fetch_prices(kit_url))
        except Exception as e:
            st.error(f"Error fetching component prices: {e}")
            st.stop()

    st.subheader(f"Kit Price: ${kit_price}")

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
