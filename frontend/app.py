import streamlit as st
from api_client import client as requests
import os
from branding import PRODUCT_NAME, page_title

# Configuration
API_URL = requests.api_url

st.set_page_config(
    page_title=page_title("Research"),
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title(PRODUCT_NAME)
st.subheader("Quantitative research workspace")

st.markdown("""
Explore market data, technical studies, portfolio scenarios, options calculations,
and historical model experiments. Data sources and methods vary across these
preserved tools; some paths may use delayed, synthetic, or otherwise unqualified
inputs. Check each workflow's source disclosure and assumptions before interpreting
its outputs. These tools are exploratory research and do not establish predictive
performance or provide investment advice.

Navigate using the sidebar to access different features.
""")

# Sidebar
st.sidebar.title("Navigation")
st.sidebar.info("Select a module from the pages above.")
