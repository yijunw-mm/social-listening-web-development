
import streamlit as st

def apply_custom_style():
    """Injects global CSS styles for the Streamlit dashboard."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Domine:wght@600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Raleway:wght@600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;500;600;700&display=swap');

    /* --- GLOBAL COLORS & LAYOUT --- */
    .stApp { background-color: #13192A; color: #FFFFFF; }
    section[data-testid="stSidebar"] { background-color: #1B2236 !important; color: white; }

    /* --- TYPOGRAPHY --- */
    h1, h2, h3, h4, h5, h6, .main-title, .card-title, .card-header, .subheader {
        font-family: 'Raleway', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        justify-content: center;
    }
    body, p, div, span, label {
        font-family: 'Lato', sans-serif !important;
        font-weight: 400;
        color: #EAEAEA;
    }

    /* --- MAIN TITLE --- */
    .main-title {
        font-family: 'Domine', sans-serif !important;
        color: #FFFFFF;
        font-size: 2rem;
        font-weight: 800;
        text-align: center;
        background-color: #1E2335;
        padding: 12px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.6);
        margin-bottom: 25px;
    }

    /* --- CARDS --- */
    .card, .stSidebar .stContainer {
        background-color: #1E2335;
        border: 1px solid #4964C5;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
    }
    .stSidebar .stContainer {
        padding: 0;
        box-shadow: 0px 6px 16px rgba(0,0,0,0.5);
        overflow: hidden;
    }

    .card-header {
        background-color: #6270a2;
        color: white;
        font-weight: 600;
        padding: 10px 16px;
        border-bottom: 1px solid #394574;
    }
    .card-body { padding: 16px; }

    /* --- INPUTS --- */
    input, textarea, select {
        font-family: 'Lato', sans-serif !important;
        font-weight: 400;
        color: #FFFFFF;
        background-color: #1B2236 !important;
        border: 1px solid #394574 !important;
        border-radius: 6px;
        padding: 6px 10px;
    }

    /* --- BUTTONS --- */
    .stButton>button, .stFileUploader button {
        background-color: #2A2F42;
        color: #FFFFFF;
        border: 1px solid #394574;
        border-radius: 8px;
        padding: 8px 16px;
        font-family: 'Lato', sans-serif !important;
        font-weight: 500;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover, .stFileUploader button:hover {
        background-color: #C990B8;
        color: white;
        border: 1px solid #C990B8;
    }
    .stButton>button:active {
        background-color: #28A3D4;
        border: 1px solid #28A3D4;
    }

    /* --- TABS --- */
    .stTabs [data-baseweb="tab"] {
        background-color: #2A2F42;
        border-radius: 8px;
        padding: 8px 16px;
        color: #B0B3C6;
        font-weight: 500;
    }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    .stTabs [aria-selected="true"] {
        background-color: #C990B8;
        color: white !important;
        font-weight: 600;
    }

    /* --- BADGES --- */
    .badge-yellow {
        background-color: #F6C90E;
        color: #2E2E3A;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 8px;
        display: inline-block;
    }
    .badge-blue {
        background-color: #28A3D4;
        color: white;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 8px;
        display: inline-block;
    }

    /* --- MISC / CLEANUP --- */
    #keyboard-domain, [data-testid="stDecoration"] { display: none !important; visibility: hidden !important; }
    .keyword-chip {
        display: inline-block;
        background-color: #2A2F42;
        border: 1px solid #394574;
        border-radius: 20px;
        padding: 6px 14px;
        margin: 4px 6px 4px 0;
        color: #FFFFFF;
        font-size: 0.9rem;
        font-family: 'Inter', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)
