'''main page for forntend display'''

import streamlit as st
import pandas as pd



st.set_page_config(page_title="Data Viaulization Dashboard", layout="wide")

st.markdown('<div class="main-title">📁 Data Visualization Dashboard </div>', unsafe_allow_html=True)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Domine:wght@600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@600;700;800&display=swap');


/* Main title + section headers */
h1, h2, h3, h4, h5, h6,
.main-title, .card-title, .card-header,.subheader {
    font-family: 'Raleway', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px;
    justify-content: center;
}

/* General text for body + widgets */
body, p, div, span, label {
    font-family: 'Lato', sans-serif !important;
    font-weight: 400;
    color: #EAEAEA; /* makes text easier to read on dark background */
}

/* Inputs + text fields */
input, textarea, select {
    font-family: 'Lato', sans-serif !important;
    font-weight: 400;
    color: #FFFFFF;
    background-color: #1B2236 !important;
    border: 1px solid #394574 !important;
    border-radius: 6px;
    padding: 6px 10px;
}

/* Buttons */
.stButton>button, .stFileUploader button {
    font-family: 'Lato', sans-serif !important;
    font-weight: 500;
}     
             
/* App background */
.stApp {
    background-color: #13192A;
    color: #FFFFFF;
}

/* Sidebar background */
section[data-testid="stSidebar"] {
    background-color: #1B2236 !important;
    color: white;
}

/* Sidebar card container */
.stSidebar .stContainer {
    background-color: #1E2335;
    border: 1px solid #4964C5;
    border-radius: 12px;
    padding: 0;  /* no global padding, let header/content handle it */
    margin-bottom: 20px;
    box-shadow: 0px 6px 16px rgba(0,0,0,0.5);
    overflow: hidden; /* ensures rounded corners apply to header strip */
}

/* Card header */
.card-header {
    background-color: #6270a2; /* Indigo header strip */
    color: white;
    font-weight: 600;
    padding: 10px 16px;
    border-bottom: 1px solid #394574;
}

/* Card content */
.card-body {
    padding: 16px;
}
            
/* General button style */
.stButton>button, .stFileUploader button {
    background-color: #2A2F42;  /* same as inactive tabs */
    color: #FFFFFF;
    border: 1px solid #394574;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
    transition: 0.3s;
    width: 100%;  /* makes sidebar buttons full-width */
}

/* Button hover */
.stButton>button:hover, .stFileUploader button:hover {
    background-color: #C990B8;  /* purple highlight */
    color: white;
    border: 1px solid #C990B8;
}

/* Active button style (optional if you want to mark a "pressed" state) */
.stButton>button:active {
    background-color: #28A3D4; /* blue when clicked */
    border: 1px solid #28A3D4;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    background-color: #2A2F42;
    border-radius: 8px;
    padding: 8px 16px;
    color: #B0B3C6;
    font-weight: 500;
}
.stTabs [data-baseweb="tab-list"] {
    justify-content: center;
}
.stTabs [aria-selected="true"] {
    background-color: #C990B8;
    color: white !important;
    font-weight: 600;
}
/* Custom card style */
.card {
    background-color: #1E2335;
    border: 1px solid #4964C5;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 20px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
}
.main-title {
    font-family: 'Domine', sans-serif !important;
    color: #FFFFFF;
    font-size: 2rem;
    font-weight: 800;
    text-align: center;
    background-color: #1E2335; /* subtle dark block behind title */
    padding: 12px 20px;
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.6); /* pop-out shadow */
    margin-bottom: 25px;
}

/* Badges */
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
            
/* "keyboard_domain" text */
#keyboard-domain, 
[data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
}

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

with st.sidebar:
    st.title("Social Listening")

    # Upload card
    st.markdown('<div class="stContainer">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">📁 Upload Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-body">', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload a zip or txt file", type=["zip","txt"])
    if uploaded_file is not None: 
        st.success("File uploaded successfully!")
    else: 
        st.info("Please upload a zip or txt file to proceed.")

    st.markdown('</div></div>', unsafe_allow_html=True)

    # Search card
    st.markdown('<div class="stContainer">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">🔍 Search Database</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-body">', unsafe_allow_html=True)

    search_query = st.text_input("Enter file name in this format: year_quarter_name")
    if st.button("Search"):
        if search_query:
            st.success(f"Searching for '{search_query}'...")
        else:
            st.error("Please enter a valid search query.")

    st.markdown('</div></div>', unsafe_allow_html=True)


    st.markdown("---")
    st.markdown("### Settings")
    st.button("⚙️ Preferences")
    st.button("🔒 Logout")

tab1, tab2, tab3, tab4= st.tabs(["📈 General", "📊  Brand", "Time Comparison ", "Brand Comparison"])

with tab1:
    st.markdown(
    "<h4 style='text-align: center;'>Whole Chat Analysis</h4>", 
    unsafe_allow_html=True)

    with st.container(border=True):
        st.write("Keyword Frequency")
        left_placeholder = st.empty() #left empty placeholder for backend to send final chart

        #selecting chart type 
        option = st.selectbox(
            "Select chart type",
            ("Bar Chart", "Line Chart", "Pie Chart"),
            key="chart_type"
        )

        #mock data for testing
        df = pd.DataFrame({"Keyword": ["apple", "banana", "cherry"], "Count": [10, 20, 15]})
        left_placeholder.bar_chart(df.set_index("Keyword"))


        if "keyword1" not in st.session_state:
            st.session_state["keywords"]= []
        search_keyword = st.text_input("Search more keywords", key="keyword1")
        if st.button("Add", key="search1"):
            if search_keyword and search_keyword not in st.session_state.keywords:
                st.session_state.keywords.append(search_keyword)
            elif search_keyword in st.session_state.keywords:
                left_placeholder.warning(f"'{search_keyword}' is already in the list.")
            else:
                left_placeholder.error("Please enter a valid search query.")

        if st.session_state.keywords:
            st.markdown("**Added Keywords:**")
            for kw in st.session_state.keywords:
                # Render each keyword as a button
                if st.button(f"{kw } &nbsp; ╳", key=f"remove_{kw}"):
                    st.session_state.keywords.remove(kw)
                    st.success(f"Removed '{kw}'")
                    st.rerun()
    st.markdown("---")
    with st.container(border=True):
        st.write(" Trend Analysis")
        right_placeholder = st.empty()
        option = st.selectbox(
            "Select chart type",
            ("Bar Chart", "Line Chart", "Pie Chart"),
            key="charttype"
        )




