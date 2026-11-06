import streamlit as st
from api_client import client as requests
import os

# Configuration
API_URL = requests.api_url

st.set_page_config(
    page_title="Cadrisyn Research",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Cadrisyn Research")
st.subheader("AI-Driven Intraday Market Trend Predictor & Investment Advisor")

st.markdown("""
Welcome to **Cadrisyn Research**. This app leverages advanced AI to provide:
*   **Intraday Trend Predictions** for Indian Equities.
*   **Personalized Portfolio Optimization**.
*   **AI Financial Advisor Chatbot**.

Navigate using the sidebar to access different features.
""")

# Sidebar
st.sidebar.title("Navigation")
st.sidebar.info("Select a module from the pages above.")
