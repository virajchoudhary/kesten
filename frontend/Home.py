import streamlit as st
import os, sys
from api_client import client as requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from branding import PRODUCT_NAME, page_title
from components.style import inject_css

API_URL = requests.api_url

st.set_page_config(
    page_title=page_title("Research"),
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
  .block-container { padding-top: 2rem; }
  .module-card {
      border: 1px solid #1E2D3D;
      border-radius: 12px;
      padding: 1.5rem;
      background: #0A0E14;
      height: 100%;
  }
  .module-card h4 { color: #00D4FF; margin-bottom: 0.5rem; }
  .module-card p  { color: #7A9BB5; font-size: 0.9rem; line-height: 1.5; }
  .tag {
      display: inline-block;
      background: #1E2D3D;
      color: #00D4FF;
      border-radius: 4px;
      padding: 2px 8px;
      font-size: 0.75rem;
      margin-right: 4px;
      margin-top: 6px;
  }
  .hero-label {
      letter-spacing: 0.2em;
      font-size: 0.75rem;
      color: #7A9BB5;
      text-transform: uppercase;
      margin-top: 1rem;
      display: block;
  }
  .divider { border-top: 1px solid #1E2D3D; margin: 2rem 0; }
</style>
""", unsafe_allow_html=True)

# --- Hero ---------------------------------------------------------------
st.title(PRODUCT_NAME)
st.subheader("Quantitative research workspace")
st.markdown(
    "Explore market data, technical studies, portfolio scenarios, options "
    "calculations, and historical model experiments. Data sources and methods "
    "vary across these preserved tools; some paths may use delayed, synthetic, "
    "or otherwise unqualified inputs. Check each workflow's source disclosure "
    "and assumptions before interpreting its outputs. These tools are exploratory "
    "research and do not establish predictive performance or provide investment advice."
)

# --- Module cards -------------------------------------------------------
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('''
    <div class="module-card">
      <h4>Dashboard</h4>
      <p>Explore market data and technical analysis for a selected symbol. Forecast outputs use legacy experimental methods and should not be treated as validated performance.</p>
      <span class="tag">Market Data</span>
      <span class="tag">Technical Analysis</span>
    </div>
    ''', unsafe_allow_html=True)

with col2:
    st.markdown('''
    <div class="module-card">
      <h4>Portfolio Optimizer</h4>
      <p>Compare allocation scenarios under selected risk and market assumptions. Results are analytical estimates, not investment recommendations.</p>
      <span class="tag">Allocation Scenarios</span>
      <span class="tag">Portfolio Methods</span>
    </div>
    ''', unsafe_allow_html=True)

with col3:
    st.markdown('''
    <div class="module-card">
      <h4>Options Analysis</h4>
      <p>Inspect model-based option prices and Greeks using the inputs shown. Some options inputs may be synthetic; check provenance before interpreting results.</p>
      <span class="tag">Option Models</span>
      <span class="tag">Greeks</span>
    </div>
    ''', unsafe_allow_html=True)

with col4:
    st.markdown('''
    <div class="module-card">
      <h4>Backtest Engine</h4>
      <p>Run preserved historical comparisons and inspect forecast paths. Legacy models and data sources are not independently qualified for out-of-sample performance.</p>
      <span class="tag">Historical Analysis</span>
      <span class="tag">Model Comparison</span>
    </div>
    ''', unsafe_allow_html=True)

# --- Methodology --------------------------------------------------------
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("## How It Works")

m1, m2, m3 = st.columns(3)

with m1:
    st.markdown("### Market Data")
    st.markdown(
        "Legacy workflows may use different data sources and adjustment "
        "conventions. Availability and timestamps vary. Confirm the source "
        "and assumptions shown by the individual tool."
    )

with m2:
    st.markdown("### Research Methods")
    st.markdown(
        "The workspace preserves statistical, machine-learning, portfolio, "
        "and options methods from earlier development. Availability and "
        "validation differ by workflow; no legacy model is presented as "
        "independently qualified."
    )

with m3:
    st.markdown("### Interpretation")
    st.markdown(
        "Historical outputs are exploratory unless the selected workflow "
        "documents data provenance, target alignment, point-in-time access, "
        "and train/test controls. Past results do not establish future "
        "performance."
    )

# --- System status ------------------------------------------------------
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("## System Status")
try:
    r = requests.get(f"{API_URL}/hpo-status/?symbol=AAPL", timeout=3)
    if r.status_code == 200:
        st.success("Backend API is online and responding.")
    else:
        st.warning("Backend API returned an unexpected response.")
except:
    st.error("Backend API is offline. Start the Django server to use this platform.")
