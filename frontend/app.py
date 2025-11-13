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
import re
import altair as alt


st.set_page_config(page_title="Data Visualization Dashboard", layout="wide")

st.markdown('<div class="main-title">📁 Data Visualization Dashboard </div>', unsafe_allow_html=True)

apply_custom_style()

# Track which tab is active
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "General"

tab_labels = ["📊 Brand", "🕓 Time Comparison", "📋 Brand Comparison","📈 General","Consumer Perception"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

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
    selected_group = st.session_state.get("selected_groups", None)
    if selected_group and len(selected_group) > 0:
        params["group_id"] = selected_group

    return params

#render chart
def render_chart(df, chart_type, x_field, y_field, color="#A7C7E7",key_prefix=""):
    import altair as alt
    if df.empty:
        st.warning("No keyword data returned.")
        return None
    
    df = df.sort_values(by=y_field, ascending=False).copy()
    if chart_type == "Bar Chart" and "time_period" in df.columns and x_field != "time_period":
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
                .mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-2,
                    color="white"
                )
                .encode(
                    x=alt.X(f"{x_field}:N", axis=alt.Axis(labelAngle=-35), sort="-y"),
                    xOffset="time_period:N",
                    y=alt.Y(f"{y_field}:Q"),
                    text=alt.Text(f"{y_field}:Q")
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
        df = df.dropna(subset=[x_field, y_field]).copy()
        df = df[df[y_field] > 0]  
        df["percent"] = (df[y_field] / df[y_field].sum() * 100).round(1)
        df["label"] = df[x_field] + " (" + df["percent"].astype(str) + "%)"

        # --- color mapping ---
        if set(df[x_field].str.lower()) >= {"positive", "neutral", "negative"}:
            color_scale = alt.Scale(
                domain=["positive", "neutral", "negative"],
                range=[sentiment_colors["positive"], sentiment_colors["neutral"], sentiment_colors["negative"]],
            )
        else:
            color_scale = alt.Scale(range=custom_colors)

        # --- base pie ---
        pie = (
            alt.Chart(df)
            .mark_arc(outerRadius=160, innerRadius=0)
            .encode(
                theta=alt.Theta(field=y_field, type="quantitative"),
                color=alt.Color(field=x_field, type="nominal", scale=color_scale, title=x_field.capitalize()),
                tooltip=[
                    alt.Tooltip(x_field, title=x_field.capitalize()),
                    alt.Tooltip(y_field, title="Value"),
                    alt.Tooltip("percent:Q", title="Percentage", format=".1f"),
                ],
            )
        )

        # --- center-aligned inside labels ---
        inside_labels = (
            alt.Chart(df)
            .mark_text(radius=100, size=13, color="white", fontWeight="bold", angle=0)
            .encode(
                text="label:N",
                theta=alt.Theta(field=y_field, type="quantitative", stack=True),
            )
            .transform_filter("datum.percent >= 8")  # show inside if ≥8%
        )

        # --- outside labels for smaller slices ---
        outside_labels = (
            alt.Chart(df)
            .mark_text(radius=185, size=13, color="white", align="center", fontWeight="bold")
            .encode(
                text="label:N",
                theta=alt.Theta(field=y_field, type="quantitative", stack=True),
            )
            .transform_filter("datum.percent < 8")
        )
        

        return (pie + inside_labels + outside_labels).properties(height=420)



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
        quarter_map = {1:1, 2:1, 3:2, 4:2, 5:2, 6:2, 7:3, 8:3, 9:3, 10:4, 11:4, 12:4}
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
                api.add_keyword(params={"brand_name": brand_name, "keyword": search_keyword})
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
                            api.remove_keyword(params={"brand_name": brand_name, "keyword": kw})
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



#TAB1 - Brand Analysis
with tab1:
    set_active_tab("Brand")
    if st.session_state.active_tab == "Brand":
        st.markdown(
        "<h4 style='text-align: center;'>Brand Analysis</h4>", 
        unsafe_allow_html=True)

        brand_name = st.selectbox(
            "Select Brand",
            ('mamypoko','huggies','pampers','drypers','merries','offspring','rascal & friends','applecrumby','hey tiger','nino nana',
    'homie','nan','lactogen','friso','enfamil','aptamil','s26','dumex dugro','bellamy organic','karihome','mount alvernia',
    'thomson medical centre','mount elizabeth','gleneagles','raffles hospital','national university hospital',
    'kkh','parkway east hospital','singapore general hospital','sengkang general hospital','changi general hospital',
    'gerber','little blossom','rafferty garden','heinz baby','ella kitchen','holle','only organic','happy baby organics'),
            key="brand_select")
        st.write(f"You selected: {brand_name}")

        if "last_brand_tab1" not in st.session_state:
            st.session_state.last_brand_tab1 = brand_name

        if brand_name != st.session_state.last_brand_tab1:
            st.session_state["keywords_brand_tab1"] = []
            st.session_state.last_brand_tab1 = brand_name

        #KEYWORD FREQUENCY
        with st.container(border=True):
            st.write("Keyword Frequency")
            left_placeholder = st.empty() #left empty placeholder for backend to send final chart

            #selecting chart type 
            col1, col2 = st.columns(2)
            with col1:
                chart_type = st.selectbox(
                    "Select chart type",
                    ("Bar Chart","Pie Chart"),
                    key="chart3_type_tab1"
                )
            with col2:
                #IDC, I GENU
                time_range = time_range_selector("Time",key="time2")
            if time_range:
                params = {"brand_name": brand_name, **time_range}
            else:
                params = {"brand_name": brand_name}
            search_key_placeholder = st.empty()

            manage_keywords(search_key_placeholder,"keywords_brand_tab1",brand_name)
            if st.session_state.get("keywords_brand_tab1"):
                params["keywords"] = ",".join(st.session_state["keywords_brand_tab1"])
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

            # --- Time Selector ---
            time_range = time_range_selector("Time", key="time3")

            params = {"brand_name": brand_name}
            if time_range:
                params.update(time_range)

            params = get_selected_group_ids(params)

            try:
                data = api.get_sentiment_analysis(params=params)

                # If no mentions
                if data.get("total_mentions", 0) == 0:
                    st.warning("No sentiment data available for this brand in the selected period.")
                    st.stop()

                # --- Build DataFrame ---
                sentiment_list = data.get("sentiment_percent", [])
                df = pd.DataFrame(sentiment_list)

                # Normalize
                if not df.empty:
                    df["sentiment"] = df["sentiment"].str.lower()

                if df.empty:
                    st.warning("No sentiment data returned.")
                    st.stop()

                # --- PIE CHART ---
                chart = render_chart(df, "Pie Chart", "sentiment", "value", key_prefix="chart4")
                if chart:
                    right_placeholder.altair_chart(chart, use_container_width=True)

                # --- Examples & Word Breakdown ---
                st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

                show = st.toggle("📄 View Top 5 Messages")
                if show:
                    examples = data.get("examples", [])

                    if not examples:
                        st.info("No sample messages detected.")
                    else:
                        for i, ex in enumerate(examples[:5]):
                            with st.container(border=True):
                                st.markdown(f"#### ✉️ Message {i+1}")

                                # Show the actual text
                                st.markdown(f"**Text:** {ex['text']}")

                                # Sentiment info
                                st.markdown(
                                    f"**Sentiment:** `{ex['sentiment']}`  | "
                                    f"**Score:** `{ex['sentiment_score']}`  | "
                                )

            except Exception as e:
                st.error(f"Failed to fetch data: {e}")


        
        #CONSUMER PERCEPTIOn
        with st.container(border=True):
            st.write("Consumer Perception Analysis")
            bottom_placeholder = st.empty()

            col1, col2 = st.columns(2)
            with col1:
                chart_type = st.selectbox(
                    "Select chart type",
                    ("Bar Chart","Pie Chart"),
                    key="chart5_type_tab1"
                )
            with col2:
                time_range = time_range_selector("Time", key="time4")

                if time_range and "month" in time_range and isinstance(time_range["month"], list):
                    time_range = {"year": time_range.get("year")}

                params = {"brand_name": brand_name, **time_range} if time_range else {"brand_name": brand_name}


            key_name = f"removed_words_{brand_name}_tab1"
            if key_name not in st.session_state:
                st.session_state[key_name] = []

            try:
                params = get_selected_group_ids(params)
                df = api.get_consumer_perception(params=params)

                if "error" in df.columns:
                    st.error(df["error"].iloc[0])
                elif "word" not in df.columns or "count" not in df.columns:
                    st.warning("No valid topic data returned.")
                else:
                    st.write("✂️ Remove Words from Chart")

                    # --- Create a form for word removal ---
                    with st.form(key=f"{brand_name}_remove_form", clear_on_submit=True):
                        new_words_input = st.text_input(
                            "Enter word(s) to remove (comma or space separated):",
                            key=f"{brand_name}_remove_input_tab1",
                            placeholder="e.g. fit, baby, leak"
                        )
                        submit_button = st.form_submit_button("Remove Words")

                    # --- Handle form submission ---
                    if submit_button and new_words_input:
                        # Split by comma or whitespace and clean up
                        words_to_add = [
                            w.strip().lower() 
                            for w in re.split(r"[,\s]+", new_words_input.strip()) 
                            if w.strip()
                        ]
                        
                        added_count = 0
                        for word in words_to_add:
                            if word and word not in st.session_state[key_name]:
                                st.session_state[key_name].append(word)
                                added_count += 1
                        
                        if added_count > 0:
                            st.success(f"✅ Removed {added_count} word(s) from chart")
                            st.rerun()
                        else:
                            st.info("All entered words were already in the remove list")

                    # --- Display removable chips ---
                    if st.session_state[key_name]:
                        st.markdown("**Currently removed words:**")
                        
                        # Create dynamic columns based on number of words
                        num_words = len(st.session_state[key_name])
                        cols_per_row = 5
                        
                        for i in range(0, num_words, cols_per_row):
                            cols = st.columns(min(cols_per_row, num_words - i))
                            for j, col in enumerate(cols):
                                if i + j < num_words:
                                    word = st.session_state[key_name][i + j]
                                    with col:
                                        if st.button(f"✕ {word}", key=f"undo_{brand_name}_tab1_{word}_{i}_{j}"):
                                            st.session_state[key_name].remove(word)
                                            st.success(f"✅ Added '{word}' back to chart")
                                            st.rerun()

                    # --- Apply filters ---
                    if st.session_state[key_name]:
                        pattern = "|".join([re.escape(w) for w in st.session_state[key_name]])
                        df = df[~df["word"].str.contains(pattern, case=False, na=False)]

                    # --- Render chart ---
                    if df.empty:
                        st.warning("All words removed — nothing to display.")
                    else:
                        chart = render_chart(df, chart_type, "word", "count", key_prefix="chart5_tab1")
                        if chart:
                            bottom_placeholder.altair_chart(chart, use_container_width=True)

            except Exception as e:
                st.error(f"Failed to fetch data: {e}")



    else:
        st.empty()
        

#TAB 2 - Time Comparison
with tab2:
    set_active_tab("Time Comparison")
    if st.session_state.active_tab == "Time Comparison":
        st.markdown(
        "<h4 style='text-align: center;'>Time Comparison</h4>", 
        unsafe_allow_html=True)
        with st.container(border=True):
            brand_name = st.selectbox(
            "Select Brand",
            ('mamypoko','huggies','pampers','drypers','merries','offspring','rascal & friends','applecrumby','hey tiger','nino nana',
    'homie','nan','lactogen','friso','enfamil','aptamil','s26','dumex dugro','bellamy organic','karihome','mount alvernia',
    'thomson medical centre','mount elizabeth','gleneagles','raffles hospital','national university hospital',
    'kkh','parkway east hospital','singapore general hospital','sengkang general hospital','changi general hospital',
    'gerber','little blossom','rafferty garden','heinz baby','ella kitchen','holle','only organic','happy baby organics'),
            key="brand_select2"
        )
        st.write(f"You selected: {brand_name}")

        if "last_brand_tab2" not in st.session_state:
            st.session_state.last_brand_tab2 = brand_name

        if brand_name != st.session_state.last_brand_tab2:
            st.session_state["keywords_brand_tab2"] = []
            st.session_state.last_brand_tab2 = brand_name
            
        #Keyword Frequency over time
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

            if not (time1 and time1.isdigit() and time2 and time2.isdigit()):
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
                all_keywords = set()
                for data in compare.values():
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "keyword" in item:
                                all_keywords.add(item["keyword"])

                compare_data = []
                for kw in all_keywords:
                    for period in periods:
                        items = compare.get(period, [])
                        if not isinstance(items, list):
                            continue  
                        count = next(
                            (i["count"] for i in items if i.get("keyword") == kw),
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

        # SENTIMENT ANALYSIS over time
        with st.container(border=True):
            st.write("Sentiment Analysis %")
            sentiment_placeholder = st.empty()

            col1, col2, col3 = st.columns([1.2,1,1])
            with col1:
                granularity = st.selectbox(
                    "Select Comparison",
                    ("Month","Quarter","Year"),
                    key="granularity_sentiment_tab2",
                    index=2
                )

            with col2:
                time1 = st.text_input("Time 1", value="2024", key="sentiment_time1")
            with col3:
                time2 = st.text_input("Time 2", value="2025", key="sentiment_time2")


            def validate_period(val: str, gran: str):
                gran = gran.lower()
                # YEAR → YYYY
                if gran == "year":
                    if not val.isdigit() or len(val) != 4:
                        return None, "Enter YYYY for Year (e.g., 2024)."
                    return int(val), None

                # MONTH → YYYYMM
                elif gran == "month":
                    if not val.isdigit() or len(val) != 6:
                        return None, "Enter YYYYMM for Month (e.g., 202405)."
                    return int(val), None

                # QUARTER → YYYYQ  (Q = 1,2,3,4)
                elif gran == "quarter":
                    if not val.isdigit() or len(val) != 5:
                        return None, "Enter YYYYQ for Quarter (e.g., 20251 for Q1)."
                    year = val[:4]
                    q = val[4]
                    if q not in ("1","2","3","4"):
                        return None, "Quarter must be 1, 2, 3, or 4 → e.g., 20251"
                    return int(val), None

            t1, err1 = validate_period(time1, granularity)
            t2, err2 = validate_period(time2, granularity)

            if err1:
                st.warning(f"Time 1 Error: {err1}")
                st.stop()
            if err2:
                st.warning(f"Time 2 Error: {err2}")
                st.stop()

            params = {
                "brand_name": brand_name,
                "granularity": granularity.lower(),
                "time1": t1,
                "time2": t2
            }
            params = get_selected_group_ids(params)

            try:
                data = api.get_time_compare_sentiment(params=params)

                compare = data.get("compare", {})
                rows = []

                # Extract sentiment% for each time period
                for period, content in compare.items():
                    sentiment_list = content.get("sentiment_percent", [])
                    for item in sentiment_list:
                        rows.append({
                            "time_period": period,
                            "sentiment": item["sentiment"],
                            "percentage": item["value"]
                        })

                df_plot = pd.DataFrame(rows)

                if df_plot.empty:
                    st.warning("No sentiment data for selected periods.")
                else:
                    chart = render_chart(df_plot, "Bar Chart", "sentiment", "percentage", key_prefix="chart_sent_tab2")
                    if chart:
                        sentiment_placeholder.altair_chart(chart, use_container_width=True)

                st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

                show_msg = st.toggle("📝 Top 5 Messages Comparison"):
                if show_msg:
                    compare = data.get("compare", {})

                    for period, content in compare.items():
                        examples = content.get("examples", [])

                        st.write(f"📅 Period: **{period}**")

                        if not examples:
                            st.info(f"No sample messages available for {period}.")
                            continue

                        for i, ex in enumerate(examples[:5]):
                            with st.container(border=True):
                                st.markdown(f"#### ✉️ Message {i+1}")

                                # Main text
                                st.markdown(f"**Text:** {ex.get('text', 'N/A')}")

                                # Sentiment metadata
                                st.markdown(
                                    f"**Sentiment:** `{ex.get('sentiment')}`  | "
                                    f"**Score:** `{ex.get('sentiment_score')}`  | "
                                )

            except Exception as e:
                st.error(f"Failed to fetch data: {e}")


       #share of voice
        with st.container(border=True):
            st.write("Share of Voice")
            share_placeholder = st.empty()
            category_name = st.selectbox(
                "Select Category",
                ("formula milk", "diaper", "hospital", "weaning"),
                key="category_select2"
            )

            col1, col2, col3 = st.columns([1.2, 1, 1])
            with col1:
                granularity = st.selectbox(
                    "Select Comparison",
                    ("Month", "Quarter", "Year"),
                    key="granularity2",
                    index=2
                )
            with col2:
                time1 = st.text_input("Time 1", value="2025", key="time1_3")
            with col3:
                time2 = st.text_input("Time 2", value="2024", key="time2_4")

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
                compare_dict = df_json.get("compare", {})

                for period, content in compare_dict.items():
                    share_items = []
                    if isinstance(content, dict):
                        share_items = content.get("share_of_voice", [])
                    if share_items:
                        for item in share_items:
                            compare_data.append({
                                "time_period": period,
                                "brand": item.get("brand", "Unknown"),
                                "percent": item.get("percent", 0)
                            })

                df_plot = pd.DataFrame(compare_data)

                if df_plot.empty:
                    st.warning(f"No share of voice data returned for {category_name}. Both periods may have zero mentions.")
                else:
                    df_plot["brand"].fillna("Unknown", inplace=True)
                    chart = render_chart(df_plot, "Bar Chart", "brand", "percent", key_prefix="chart8")
                    if chart:
                        share_placeholder.altair_chart(chart, use_container_width=True)

            except Exception as e:
                st.error(f"Failed to fetch data: {e}")

    else:
        st.empty()

#TAB 3 - BRAND COMPARISON
with tab3: 
    set_active_tab("Brand Comparison")
    if st.session_state.active_tab == "Brand Comparison":
        st.markdown(
            "<h4 style='text-align: center;'>Brand Comparison</h4>", 
            unsafe_allow_html=True
        )
       
        category_name = st.selectbox(
            "Select Category",
            ("formula milk", "diaper", "hospital", "weaning"),
            key="category_select"
        )
        st.write(f"You selected: {category_name}")
        
        # SHARE OF VOICE
        with st.container(border=True):
            st.write("Share of Voice")
            chart_type = st.selectbox(
                "Select chart type",
                ("Bar Chart","Pie Chart"),
                key="chart9_type_tab3"
            )
            
            params = {"category_name": category_name}
            params = get_selected_group_ids(params)
            
            try:
                df = api.get_share_of_voice(params=params)
                
                if df.empty:
                    st.warning(f"No share of voice data returned for '{category_name}'. This category may have no brand mentions in the selected data.")
                elif "error" in df.columns:
                    st.error(df["error"].iloc[0])
                elif "brand" not in df.columns or "percentage" not in df.columns:
                    st.error(f"Invalid data structure returned. Expected columns: 'brand', 'percentage'. Got: {df.columns.tolist()}")
                else:
                    # Filter out zero values for better visualization
                    df_filtered = df[df["percentage"] > 0]
                    
                    if df_filtered.empty:
                        st.warning("All brands have 0% share. No data to display.")
                    else:
                        chart = render_chart(df_filtered, chart_type, "brand", "percentage", key_prefix="chart9_tab3")
                        if chart:
                            st.altair_chart(chart, use_container_width=True)
                            
                            # Show summary stats
                            st.caption(f"Total brands: {len(df_filtered)} | Top brand: {df_filtered.iloc[0]['brand']} ({df_filtered.iloc[0]['percentage']:.1f}%)")
                            
            except Exception as e:
                st.error(f"Failed to fetch share of voice data: {e}")


#THIS IS TAB 4 - General Analysis
with tab4:
    set_active_tab("General")
    if st.session_state.active_tab == "General":
        st.markdown(
        "<h4 style='text-align: center;'>Whole Chat Analysis</h4>", 
        unsafe_allow_html=True)

        #KEYWORD FREQUENCY
        with st.container(border=True):
            st.write("Keyword Frequency")
            left_placeholder = st.empty() 

            chart_type = st.selectbox(
                "Select chart type",
                ("Bar Chart","Pie Chart"),
                key="chart1_type_tab4"
            )

            
            # Stage and Time Range
            stage = st.selectbox(
                "Select Stage",
                ("None", "Pregnant (0 to 9 months)", "Weaning (4 to 16 months)",
                "Infant (1 to 18 months)", "Preschool (18 months to 5yo)",
                "Enrichment (3 to 6yo)", "Current Month"),
                key="stage_select_tab4",
                index=0
            )

            time_range = time_range_selector("Time", key="time_selector_tab4")

            params = {}

            if time_range:
                params.update(time_range)

            if stage != "None":
                params["stage"] = stage

            try:
                params = get_selected_group_ids(params)
                df = api.get_keyword_frequency(params=params)
                chart = render_chart(df, chart_type, "keyword", "count",key_prefix="chart1_type_tab4")
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
                chart_type2 = st.selectbox(
                    "Select chart type",
                    ("Bar Chart","Pie Chart"),
                    key="chart2_type_tab4"
                )

            with col2:
                top_n = st.slider(
                    "Select number of top keywords",
                    min_value=5,
                    max_value=20,
                    value=10,
                    step = 5,
                    key="top_n",
                )  
            params2 = {"top_k": top_n}
            params2 = get_selected_group_ids(params2)
            with st.spinner("Fetching new keyword predictions..."):
                try:
                    df2 = api.new_keywords(params=params2)
                    chart = render_chart(df2, chart_type2, "keyword", "score", key_prefix="chart2_type_tab4")
                    if chart: 
                        right_placeholder.altair_chart(chart, use_container_width=True)

                except Exception as e:
                    st.error(f"Failed to fetch data: {e}")
    else:
        st.empty()


with tab5:
    set_active_tab("Consumer Perception")
    if st.session_state.active_tab== "Consumer Perception":
        st.markdown(
        "<h4 style='text-align: center;'>Whole Chat Analysis</h4>", 
        unsafe_allow_html=True)

        category_name = st.selectbox(
            "Select Category",
            ("formula milk", "diaper", "hospital", "weaning"),
            key="category_select_3"
        )
        st.write(f"You selected: {category_name}")
        
         # CONSUMER PERCEPTION
        with st.container(border=True):
            st.write("Consumer Perception Analysis")
            chart_type = st.selectbox(
                "Select chart type",
                ("Bar Chart", "Pie Chart"),
                key="chart10_type_tab3"
            )

            params = {"category_name": category_name, "top_k": 20}

            params = get_selected_group_ids(params)

            key_name = f"removed_words_{category_name}_tab3"
            if key_name not in st.session_state:
                st.session_state[key_name] = []

            try:
                df = api.get_category_consumer_perception(params=params)

                if df.empty:
                    st.warning(f"No consumer perception data returned for '{category_name}'. This category may have no brand mentions in the selected data.")
                elif "error" in df.columns:
                    st.error(df["error"].iloc[0])
                elif "word" not in df.columns or "count" not in df.columns:
                    st.error(f"Invalid data structure returned. Expected columns: 'word', 'count'. Got: {df.columns.tolist()}")
                else:
                    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
                    # --- Remove Words UI ---
                    st.write("✂️ Remove Words from Chart")

                    with st.form(key=f"{category_name}_remove_form_tab3", clear_on_submit=True):
                        new_words_input = st.text_input(
                            "Enter word(s) to remove (comma or space separated):",
                            key=f"{category_name}_remove_input_tab3",
                            placeholder="e.g. baby, fit, care"
                        )
                        submit_button = st.form_submit_button("Remove Words")

                    if submit_button and new_words_input:
                        words_to_add = [
                            w.strip().lower()
                            for w in re.split(r"[,\s]+", new_words_input.strip())
                            if w.strip()
                        ]
                        added_count = 0
                        for word in words_to_add:
                            if word not in st.session_state[key_name]:
                                st.session_state[key_name].append(word)
                                added_count += 1

                        if added_count > 0:
                            st.success(f"✅ Removed {added_count} word(s) from chart")
                            st.rerun()
                        else:
                            st.info("All entered words were already in the remove list")

                    if st.session_state[key_name]:
                        st.markdown("**Currently removed words:**")
                        num_words = len(st.session_state[key_name])
                        cols_per_row = 5
                        for i in range(0, num_words, cols_per_row):
                            cols = st.columns(min(cols_per_row, num_words - i))
                            for j, col in enumerate(cols):
                                if i + j < num_words:
                                    word = st.session_state[key_name][i + j]
                                    with col:
                                        if st.button(f"✕ {word}", key=f"undo_{category_name}_tab3_{word}_{i}_{j}"):
                                            st.session_state[key_name].remove(word)
                                            st.success(f"✅ Added '{word}' back to chart")
                                            st.rerun()

                    # --- Filter Data ---
                    if st.session_state[key_name]:
                        pattern = "|".join([re.escape(w) for w in st.session_state[key_name]])
                        df = df[~df["word"].str.contains(pattern, case=False, na=False)]

                    if df.empty:
                        st.warning("All words removed — nothing to display.")
                    else:
                        chart = render_chart(df, chart_type, "word", "count", key_prefix="chart10_tab3")
                        if chart:
                            st.altair_chart(chart, use_container_width=True)
                            st.caption(f"Total keywords: {len(df)} | Top keyword: '{df.iloc[0]['word']}' ({df.iloc[0]['count']} mentions)")

            except Exception as e:
                st.error(f"Failed to fetch consumer perception data: {e}")