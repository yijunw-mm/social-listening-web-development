'''main page for forntend display'''

from datetime import datetime
import calendar
import streamlit as st
import pandas as pd
import api_client as api
import matplotlib.pyplot as plt
import altair as alt
from style import apply_custom_style
import numpy as np


st.set_page_config(page_title="Data Viaulization Dashboard", layout="wide")

st.markdown('<div class="main-title">📁 Data Visualization Dashboard </div>', unsafe_allow_html=True)

apply_custom_style()

# Track which tab is active
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "General"

tab_labels = ["📈 General", "📊 Brand", "Time Comparison", "Brand Comparison"]
tab1, tab2, tab3, tab4 = st.tabs(tab_labels)

# Simple helper to switch state when tab changes
def set_active_tab(label):
    st.session_state.active_tab = label


with st.sidebar:
    st.title("Social Listening")

    st.markdown("---") 
    st.write("Select Data Files")
    try: 
        response = api.group_chat()
        groups = response.get("groups", [])
        if not groups:
            st.warning("No data groups available.")
        else:
            selected_group =[]
            for grp in groups:
                gid = grp["id"]
                checked = st.checkbox(f"Group {gid}" ,key=f"chk_{gid}")
                if checked: 
                    selected_group.append(gid)
            st.session_state["selected_groups"] = selected_group
            st.caption(f"{len(selected_group)} groups selected")
    except Exception as e:
        st.error(f"Failed to fetch data groups: {e}")
    st.markdown("---")

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
            # Here you would typically call your backend API to perform the search
        else:
            st.error("Please enter a valid search query.")

    st.markdown('</div></div>', unsafe_allow_html=True)


    st.markdown("---")
    st.markdown("### Settings")
    st.button("⚙️ Preferences")
    st.button("🔒 Logout")



#TAB 1 - General Analysis
custom_colors = [
    "#C990B8",  # Viola (theme primary)
    "#28A3D4",  # Cyan
    "#F6C90E",  # Yellow
    "#A7C7E7",  # Soft Light Blue
    "#6270A2",  # Indigo/Navy
    "#FF7B72",  # Coral
    "#8FD694",  # Mint Green
    "#FFB347",  # Orange
    "#9B6BDF",  # Purple
    "#E57373",  # Soft Red
    "#6DD3CE",  # Aqua Green
    "#FFD166",  # Amber
    "#EF476F",  # Bright Pink
    "#06D6A0",  # Teal Green
    "#118AB2",  # Blue
    "#073B4C",  # Deep Navy
    "#F9844A",  # Warm Orange
    "#43AA8B",  # Sage Green
    "#90BE6D",  # Olive
    "#577590",  # Steel Blue
]

sentiment_colors = {
    "positive": "#C990B8",  # Green
    "neutral": "#118AB2",   # Blue
    "negative": "#E57373"   # Red
}


#group ids
def get_selected_group_ids(params: dict = None) -> dict:
    params = params.copy() if params else {}
    selected_group = st.session_state.get("selected_groups", [])
    if selected_group:
        params["group_id"] = ",".join(map(str, selected_group))
    return params

#render chart
def render_chart(df, chart_type, x_field, y_field, color="#A7C7E7",key_prefix=""):
    import altair as alt
    if df.empty:
        st.warning("No keyword data returned.")
        return None
    
    df = df.sort_values(by=y_field, ascending=False).copy()
    if chart_type =="Bar Chart" and "time_period" in df.columns and "x_field" != "time_period":
        df_plot = df.copy()
        df_plot["time_period"] = df_plot["time_period"].astype(str)

        x_label = x_field.capitalize() if x_field != "sentiment" else "Sentiment"
        y_label = "Mentions" if y_field == "count" else y_field.capitalize()

        chart = (
            alt.Chart(df_plot)
            .mark_bar()
            .encode(
                x=alt.X(f"{x_field}:N",
                        sort="-y",
                        axis=alt.Axis(title=x_label, labelAngle=-35, labelLimit =0, labelOverlap=False)),
                y=alt.Y(f"{y_field}:Q", axis=alt.Axis(title=y_label)),
                color=alt.Color("time_period:N", title="Period"),
                xOffset="time_period:N",
                tooltip=[x_field, "time_period", y_field]
            )
        )
        text = (
            alt.Chart(df_plot)
            .mark_text(align="center", baseline="bottom", dy=-3, color="white")
            .encode(
                x=alt.X(f"{x_field}:N"),
                y=alt.Y(f"{y_field}:Q"),
                text=alt.Text(f"{y_field}:Q", format=".2f")
            )
        )

        return (chart + text).properties(height=400)

    if chart_type == "Bar Chart":
        bar_color = st.color_picker("Pick a color for the bars", "#A7C7E7",key=f"{key_prefix}_color")
        chart = (
            alt.Chart(df)
            .mark_bar(color=bar_color)
            .encode(
                x=alt.X(f"{x_field}:N",
                        sort="-y",
                        axis=alt.Axis(title=x_field.capitalize(), labelAngle=-45, labelLimit=0,labelOverlap=False)),
                y=alt.Y(f"{y_field}:Q",
                        axis=alt.Axis(title=y_field.capitalize())),
                tooltip=[x_field, y_field]
            )
        )
        text = (
            alt.Chart(df)
            .mark_text(align="center", baseline="middle", dy=-6, color="white")
            .encode(
                x=alt.X(f"{x_field}:N", sort="-y"),
                y=alt.Y(f"{y_field}:Q"),
                text=alt.Text(f"{y_field}:Q", format=".2f")
            )
        )
        return (chart + text).properties(height=400)
    elif chart_type == "Pie Chart":
        # --- handle missing values and compute percentages ---
        df = df.dropna(subset=[x_field, y_field]).copy()
        df["percent"] = (df[y_field] / df[y_field].sum() * 100).round(1)
        df["label"] = df[x_field] + " (" + df["percent"].astype(str) + "%)"

        # --- color mapping (for sentiment or generic) ---
        if set(df[x_field].str.lower()) >= {"positive", "neutral", "negative"}:
            color_scale = alt.Scale(
                domain=["positive", "neutral", "negative"],
                range=[sentiment_colors["positive"], sentiment_colors["neutral"], sentiment_colors["negative"]]
            )
        else:
            color_scale = alt.Scale(range=custom_colors)

        # --- compute mid-angles for each slice ---
        df["cumsum"] = df[y_field].cumsum()
        df["middle_angle"] = (df["cumsum"] - df[y_field] / 2) / df[y_field].sum() * 2 * np.pi

        num_slices = len(df)
        outer_r = 180  
        if num_slices <= 3:
            label_r = outer_r * 0.5
        elif num_slices <= 6:
            label_r = outer_r * 0.8
        else:
            label_r = outer_r * 0.9

        df["x"] = df["middle_angle"].apply(lambda a: label_r *np.cos(a - np.pi / 2))
        df["y"] = df["middle_angle"].apply(lambda a: label_r *np.sin(a - np.pi / 2))

        # --- Base pie chart ---
        pie = (
            alt.Chart(df)
            .mark_arc(outerRadius=180)
            .encode(
                theta=alt.Theta(field=y_field, type="quantitative"),
                color=alt.Color(field=x_field, type="nominal", scale=color_scale, title=x_field.capitalize()),
                tooltip=[
                    alt.Tooltip(x_field, title=x_field.capitalize()),
                    alt.Tooltip(y_field, title="Value"),
                    alt.Tooltip("percent:Q", title="Percentage", format=".1f")
                ],
            )
        )

        # --- Text layer with custom positions ---
        text = (
            alt.Chart(df)
            .mark_text(size=13, color="white",stroke="white")
            .encode(
                x= alt.X("x:Q",axis=None),
                y= alt.Y("y:Q",axis = None),
                text="label:N"
            )
            .transform_filter(alt.datum.percent > 4)
        )

        return (pie + text).properties(height=420)



    else:
        st.error("Unsupported chart type selected.")
        return None

    
#TIME RANGE SELECTOR
def time_range_selector(label,key):

    col1, col2 = st.columns([2, 1])
    with col1:
        month_options = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        start,end = st.select_slider(
            "Select month or quarter",
            options=month_options,
            value=("Jan", "Dec"),
            key=f"{key}_month_range"

        )
        start_idx = month_options.index(start) + 1
        end_idx = month_options.index(end) + 1
        quarter_map = {1:1, 1:1, 2:1, 3:2, 4:2, 5:2, 6:2, 7:3, 8:3, 9:3, 10:4, 11:4, 12:4}
        same_quarter = (quarter_map[start_idx] == quarter_map[end_idx])
    with col2:
        year = st.number_input("Year", min_value=2000, max_value=2100, value=datetime.now().year, step=1, key=f"{key}_year_input")

    if start_idx == 1 and end_idx == 12:
        return {"year": year}
    if start_idx == end_idx:
        return {"month": start_idx, "year": year}
    if same_quarter:
        return {"quarter": quarter_map[start_idx], "year": year}
    if (start_idx, end_idx) in [(1,3),(4,6),(7,9),(10,12)]:
        return {"quarter": quarter_map[start_idx], "year": year}
    else:
        return {"year": year, "month": list(range(start_idx, end_idx + 1))}


#def manage keywords 
def manage_keywords(placeholder, session_key, brand_name):
    if session_key not in st.session_state:
        st.session_state[session_key] = []

    with placeholder.container():
        search_keyword = st.text_input("Search more keywords", key=f"input_{session_key}")

        if st.button("Add", key=f"add_{session_key}"):
            if not search_keyword:
                st.warning("Please enter a keyword to add.")
                return
            if search_keyword in st.session_state[session_key]:
                st.warning(f"'{search_keyword}' is already added.")
                return

            try:
                api.add_keyword({"brand_name": brand_name, "keyword": search_keyword})
                st.session_state[session_key].append(search_keyword)
                st.success(f"Added '{search_keyword}'")
                st.rerun()  
            except Exception as e:
                st.error(f"Failed to add '{search_keyword}': {e}")

        if st.session_state[session_key]:
            st.markdown("**Added Keywords:**")
            for kw in st.session_state[session_key]:
                col1, _ = st.columns([1, 5])
                with col1:
                    if st.button(f"{kw} ╳", key=f"remove_{session_key}_{kw}"):
                        try:
                            api.remove_keyword({"brand_name": brand_name, "keyword": kw})
                            st.session_state[session_key].remove(kw)
                            st.success(f"Removed '{kw}'")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to remove '{kw}': {e}")
def build_stage_params(stage: str, time_range: dict) -> dict:
    params = time_range.copy() if time_range else {}
    if stage and stage.lower() != "none":
        params["stage"] = stage
    return params


#THIS IS TAB 1 - General Analysis
with tab1:
    set_active_tab("General")
    if st.session_state.active_tab == "General":
        st.markdown(
        "<h4 style='text-align: center;'>Whole Chat Analysis</h4>", 
        unsafe_allow_html=True)

        #KEYWORD FREQUENCY
        with st.container(border=True):
            st.write("Keyword Frequency")
            left_placeholder = st.empty() 
            
            stage = st.selectbox("Select Stage", ("None","Pregnant","Pre-Pregnancy","Infant/Preschool","Weaning","Preschool","Enrinchment","Other"), key="stage_select", index=0)
            if stage == "None":
                params = {}
            #selecting chart type 
            col1, col2 = st.columns(2)
            with col1:
                option = st.selectbox(
                    "Select chart type",
                    ("Bar Chart", "Pie Chart"),
                    key="chart1_type",
                    index = 0
                )
                chart_type = st.session_state.chart1_type
            with col2:
                   time_range = time_range_selector("Time",key="time1")
            if time_range:
                params = build_stage_params(stage, time_range)
            else: 
                params = build_stage_params(stage)
            try:
                params = get_selected_group_ids(params)
                df = api.get_keyword_frequency(params=params)
                chart = render_chart(df, option, "keyword", "count",key_prefix="chart1")
                if chart: 
                    left_placeholder.altair_chart(chart, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to fetch data: {e}")

        #NEW KEYWORDS PREDICTION
        st.markdown("---")
        with st.container(border=True):
            st.write("New Keywords Prediction")
            right_placeholder = st.empty()
            col1, col2 = st.columns(2)
            with col1:
                option2 = st.selectbox(
                        "Select chart type",
                        ("Bar Chart", "Pie Chart"),
                        key="chart2_type",
                        index = 0
                    )
                chart_type2 = st.session_state.chart2_type
            with col2:
                top_n = st.slider(
                    "Select number of top keywords",
                    min_value=5,
                    max_value=20,
                    value=10,
                    step = 5,
                    key="top_n",
                )  
                selected_topn = st.session_state.top_n
            params2 = {"top_k": top_n}
            params2 = get_selected_group_ids(params2)
            with st.spinner("Fetching new keyword predictions..."):
                try:
                    df2 = api.new_keywords(params=params2)
                    chart = render_chart(df2,option2, "keyword", "score",key_prefix="chart2")
                    if chart: 
                        right_placeholder.altair_chart(chart, use_container_width=True)

                except Exception as e:
                    st.error(f"Failed to fetch data: {e}")
    else:
        st.empty()


#TAB2 - Brand Analysis
with tab2:
    set_active_tab("Brand")
    if st.session_state.active_tab == "Brand":
        st.markdown(
        "<h4 style='text-align: center;'>Brand Analysis</h4>", 
        unsafe_allow_html=True)

        brand_name = st.selectbox(
            "Select Brand",
            ("mamypoko", "huggies", "pampers","drypers","merries","offspring","rascal & friends","applecrumby","hey tiger",
            "Nino Nana"),
            key="brand_select"
        )
        st.write(f"You selected: {brand_name}")

        if "last_brand" not in st.session_state:
            st.session_state.last_brand = brand_name

        if brand_name != st.session_state.last_brand:
            st.session_state["keywords_brand"] = []
            st.session_state.last_brand = brand_name

        #KEYWORD FREQUENCY
        with st.container(border=True):
            st.write("Keyword Frequency")
            left_placeholder = st.empty() #left empty placeholder for backend to send final chart

            #selecting chart type 
            col1, col2 = st.columns(2)
            with col1:
                option = st.selectbox(
                    "Select chart type",
                    ("Bar Chart","Pie Chart"),
                    key="chart3_type"
                )
                chart_type = st.session_state.chart3_type
            with col2:
                time_range = time_range_selector("Time",key="time2")
            if time_range:
                params = {"brand_name": brand_name, **time_range}
            else:
                params = {"brand_name": brand_name}
            search_key_placeholder = st.empty()

            manage_keywords(search_key_placeholder,"keywords_brand",brand_name)
            if st.session_state.get("keywords_brand"):
                params["keywords"] = ",".join(st.session_state["keywords_brand"])
            try: 
                params = get_selected_group_ids(params)
                df = api.get_brand_keyword(params=params)
                if "error" in df.columns:
                    st.error(df["error"].iloc[0])
                elif "keyword" not in df.columns or "count" not in df.columns:
                    st.warning("No valid keyword data returned.")
                else:
                    chart = render_chart(df, chart_type, "keyword", "count", key_prefix="chart3")
                    if chart:
                        left_placeholder.altair_chart(chart, use_container_width=True)

            except Exception as e:
                st.error(f"Failed to fetch data: {e}")


        #SENTIMENT ANALYSIS
        with st.container(border=True):
            st.write("Sentiment Analysis %")
            right_placeholder = st.empty()
            time_range = time_range_selector("Time",key="time3")
            params = {"brand_name":brand_name, **time_range} if time_range else {"brand_name":brand_name}
            try:
                params = get_selected_group_ids(params)
                df = api.get_sentiment_analysis(params=params)
                if "error" in df.columns:
                    st.error(df["error"].iloc[0])
                elif "sentiment" not in df.columns or "value" not in df.columns:
                    st.warning("No valid sentiment data returned.")
                else: 
                    chart = render_chart(df, "Pie Chart", "sentiment", "value",key_prefix="chart4")
                    if chart: 
                        right_placeholder.altair_chart(chart, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to fetch data: {e}")
        
        #CONSUMER PERCEPTION
        with st.container(border = True):
            st.write("Consumer Perception Analysis")
            bottom_placeholder = st.empty()
            #selecting chart type
            col1, col2 = st.columns(2)
            with col1:
                option = st.selectbox(
                    "Select chart type",
                    ("Bar Chart","Pie Chart"),
                    key="chart5_type"
                )
                chart_type = st.session_state.chart5_type
            with col2:
                time_range = time_range_selector("Time",key="time4")

            params = {"brand_name":brand_name, **time_range}if time_range else {"brand_name":brand_name}
            try: 
                params = get_selected_group_ids(params)
                df = api.get_consumer_perception(params=params)
                if "error" in df.columns:
                    st.error(df["error"].iloc[0])
                elif "word" not in df.columns or "co_occurrence_score" not in df.columns:
                    st.warning("No valid topic data returned.")
                else:
                    chart = render_chart(df, chart_type, "word", "co_occurrence_score",key_prefix="chart5")
                    if chart:
                        bottom_placeholder.altair_chart(chart, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to fetch data: {e}")

    else:
        st.empty()
        

#TAB 3 - Time Comparison
with tab3:
    set_active_tab("Time Comparison")
    if st.session_state.active_tab == "Time Comparison":
        st.markdown(
        "<h4 style='text-align: center;'>Time Comparison</h4>", 
        unsafe_allow_html=True)
        with st.container(border=True):
            brand_name = st.selectbox(
            "Select Brand",
            ("mamypoko", "huggies", "pampers","drypers","merries","offspring","rascal & friends","applecrumby","hey tiger",
            "Nino Nana"),
            key="brand_select2"
        )
        st.write(f"You selected: {brand_name}")

        if "last_brand" not in st.session_state:
            st.session_state.last_brand = brand_name

        if brand_name != st.session_state.last_brand:
            st.session_state["keywords_brand"] = []
            st.session_state.last_brand = brand_name
            
        with st.container(border=True):
            st.write("Keyword Frequency")
            keyword_placeholder = st.empty()
            col1,col2,col3 = st.columns([1,1,1])
            with col1:
                granularity = st.selectbox(
                    "Select Comparison",
                    ("Month","Quarter","Year"),
                    key="granularity",
                    index=2
                )
            with col2:
                time1 = st.text_input("Time 1",value=2024,key="time1")
            with col3:
                time2 = st.text_input("Time 2",value=2025,key="time2")

            if not (time1.isdigit() and time2.isdigit()):
                st.warning("Please enter numeric values (e.g. 202405 for May 2025).")
                st.stop()

            params = {
                "brand_name": brand_name,
                "granularity": granularity.lower() if granularity else "year",
                "time1": int(time1) if time1 else None,
                "time2": int(time2) if time2 else None,
            }

            try:
                params = get_selected_group_ids(params)
                df_json = api.get_time_compare_frequency(params=params)
                compare = df_json.get("compare", {})
                periods = list(compare.keys())

                # --- collect all unique keywords across both time periods ---
                all_keywords = {
                    item["keyword"]
                    for data in compare.values()
                    for item in data
                    if item.get("keyword") is not None
                }

                compare_data = []
                for kw in all_keywords:
                    for period in periods:
                        count = next(
                            (i["count"] for i in compare.get(period, []) if i["keyword"] == kw),
                            0
                        )
                        compare_data.append({
                            "time_period": period,
                            "keyword": kw,
                            "count": count
                        })

                if not compare_data:
                    st.warning("No keyword frequency data returned.")
                    st.stop()

                df_plot = pd.DataFrame(compare_data)
                df_plot["count"] = pd.to_numeric(df_plot["count"], errors="coerce")

                chart = render_chart(df_plot, "Bar Chart", "keyword", "count", key_prefix="chart6")
                if chart:
                    keyword_placeholder.altair_chart(chart, use_container_width=True)

            except Exception as e:
                st.error(f"Failed to fetch data: {e}")


        with st.container(border = True):
            st.write("Sentiment Analysis %")
            sentiment_placeholder = st.empty()
            col1, col2,col3 = st.columns([1.2,1,1])
            with col1:
                granularity = st.selectbox(
                    "Select Comparison",
                    ("Month","Quarter","Year"),
                    key="granularity1",
                    index=2
                )
            with col2:
                time1 = st.text_input("Time 1",value=2024,key="time1_1")
            with col3:
                time2 = st.text_input("Time 2",value=2025,key="time2_2")

            if not (time1.isdigit() and time2.isdigit()):
                st.warning("Please enter numeric values (e.g. 202405 for May 2025).")
                st.stop()
            params = {
                "brand_name": brand_name,
                "granularity": granularity.lower(),
                "time1": int(time1),
                "time2": int(time2),
            }
            try:
                params = get_selected_group_ids(params)
                df_json= api.get_time_compare_sentiment(params=params)
                compare_data = []
                for period, data in df_json.get("compare", {}).items():
                    for item in data.get("sentiment_detail",[]):
                        compare_data.append({
                            "time_period": period,
                            "sentiment": item["sentiment"],
                            "percentage": item["percentage"],
                        })
                df_plot = pd.DataFrame(compare_data)
                if df_plot.empty:
                    st.warning("No sentiment data returned.")
                else: 
                    chart = render_chart(df_plot, "Bar Chart", "sentiment", "percentage",key_prefix="chart7")
                    if chart:
                        sentiment_placeholder.altair_chart(chart, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to fetch data: {e}")

        #share of voice
        with st.container(border=True):
            st.write("Share of Voice")
            share_placeholder = st.empty()
            category_name = st.selectbox(
                "Select Category",
                    ("formula milk", "diaper","hospital","weaning"),
                    key="category_select2"
            )
            col1, col2,col3 = st.columns([1.2,1,1])
            with col1:
                granularity = st.selectbox(
                    "Select Comparison",
                    ("Month","Quarter","Year"),
                    key="granularity2",
                    index=2
                )
            with col2:
                time1 = st.text_input("Time 1",value=2024,key="time1_3")
            with col3:
                time2 = st.text_input("Time 2",value=2025,key="time2_4")

            if not (time1.isdigit() and time2.isdigit()):
                st.warning("Please enter numeric values (e.g. 202405 for May 2025).")
                st.stop()
            params = {
                "category_name": category_name,
                "granularity": granularity.lower(),
                "time1": int(time1),
                "time2": int(time2),
            }
            try:
                params = get_selected_group_ids(params)
                df_json = api.get_time_compare_share_of_voice(params=params)
                compare_data = []
                for period, data in df_json.get("compare", {}).items():
                    for item in data.get("share",[]):
                        compare_data.append({
                            "time_period": period,
                            "brand": item["brand"],
                            "count": item["count"]
                        })
                df_plot = pd.DataFrame(compare_data)

                if df_plot.empty:
                    st.warning("No share of voice data returned.")
                else: 
                    chart = render_chart(df_plot, "Bar Chart", "brand", "count",key_prefix="chart8")
                    if chart:
                        share_placeholder.altair_chart(chart, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to fetch data: {e}")

    else:
        st.empty()

#TAB 4 -BRAND COMPARISON
with tab4: 
    set_active_tab("Brand Comparison")
    if st.session_state.active_tab == "Brand Comparison":
        st.markdown(
        "<h4 style='text-align: center;'>Brand Comparison</h4>", 
        unsafe_allow_html=True)
       
        category_name = st.selectbox(
            "Select Category",
                ("formula milk", "diaper","hospital","weaning"),
                key="category_select"
        )
        st.write(f"You selected: {category_name}")

        with st.container(border=True):
            st.write("Share of Voice")
            option = st.selectbox(
                    "Select chart type",
                    ("Bar Chart","Pie Chart"),
                    key="chart8_type"
                )
            chart_type = st.session_state.chart8_type
            params = {"category_name": category_name}
            params = get_selected_group_ids(params)
            try:
                df = api.get_share_of_voice() 
                if not df.empty and "category" in df.columns:
                    df_filtered = df[df["category"].str.lower() == category_name.lower()]
                else:
                    df_filtered = df
                if "error" in df_filtered.columns:
                    st.error(df_filtered["error"].iloc[0])
                elif "brand" not in df_filtered.columns or "percentage" not in df_filtered.columns:
                    st.warning("No valid share of voice data returned.")
                else:
                    chart = render_chart(df_filtered, chart_type, "brand", "percentage", key_prefix="chart8")
                    if chart:
                        st.altair_chart(chart, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to fetch data: {e}")

        #CONSUMER PERCEPTION
        with st.container(border=True):
            st.write("Consumer Perception Analysis")
            option = st.selectbox(
                    "Select chart type",
                    ("Bar Chart","Pie Chart"),
                    key="chart9_type"
                )
            chart_type = st.session_state.chart8_type
            params = {"category_name": category_name, "top_k": 20}
            params = get_selected_group_ids(params)
            try:
                df= api.get_category_consumer_perception(params=params)
                if "error" in df.columns:
                    st.error(df["error"].iloc[0])
                elif "brand" not in df.columns or "count" not in df.columns:
                    st.warning("No valid topic data returned.")
                else:
                    chart = render_chart(df, chart_type, "brand", "count",key_prefix="chart9")
                    if chart:
                        st.altair_chart(chart, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to fetch data: {e}")
        
    else:
        st.empty()


