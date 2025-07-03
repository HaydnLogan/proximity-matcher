import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("Position A Model - A1 Detector")

# Load the data
uploaded_file = st.file_uploader("Upload your CSV", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
    df['Departure'] = pd.to_datetime(df['Departure'], errors='coerce')
    
    # Proceed with detection logic here
    a1_raw = detect_descending_sequences(df)
    a1_deduped = deduplicate(a1_raw)
    generate_summary(a1_deduped, label="A1")
else:
    st.warning("Please upload a CSV file to begin.")

# Constants
REPORT_TIME = df['Arrival'].max()
ANCHOR_ORIGINS = {"Saturn", "Jupiter", "Kepler-62f", "Kepler-442b"}
EPIC_TODAY = {"Trinidad", "Tobago"}
EPIC_WEEK = {"WASP-12b"}
EPIC_MONTH = {"Macedonia"}
STRENGTH_TRAVELERS = {0, 40, -40, 54, -54}

# Helpers
def get_feed_icon(feed): return "👶" if "sm" in str(feed) else "🧔"
def hours_ago(arr): return round((REPORT_TIME - arr).total_seconds() / 3600, 1)
def is_anchor(origin): return origin in ANCHOR_ORIGINS
def is_epic(origin):
    if origin in EPIC_TODAY: return "today"
    elif origin in EPIC_WEEK: return "week"
    elif origin in EPIC_MONTH: return "month"
    return None

# Detect descending sequences for a given Output
def detect_descending_sequences(df):
    outputs = df['Output'].unique()
    results = []

    for output in outputs:
        sub = df[df['Output'] == output].sort_values('Arrival')
        for i in range(len(sub) - 2):
            trio = sub.iloc[i:i+3]
            m_nums = trio['M #'].tolist()
            if sorted([abs(x) for x in m_nums], reverse=True) == [abs(x) for x in m_nums]:
                polarity = all(x >= 0 for x in m_nums) or all(x <= 0 for x in m_nums)
                if polarity:
                    arrival = trio.iloc[-1]['Arrival']
                    results.append((output, trio.copy(), arrival))
    return results

# Merge duplicate paths
def deduplicate(trios):
    unique = []
    seen = set()

    for output, trio, arr_time in trios:
        m_key = tuple(trio['M #'].tolist())
        arr_key = tuple(trio['Arrival'].tolist())
        key = (output, m_key, arr_key)
        if key in seen:
            continue
        seen.add(key)

        # Check for same M# and Arrival, merge Origins
        for idx in range(len(trio)):
            same_time = (trio['M #'] == trio.iloc[idx]['M #']) & (trio['Arrival'] == trio.iloc[idx]['Arrival'])
            origins = df[same_time & (df['Output'] == output)]['Origin'].unique()
            trio.at[trio.index[idx], 'Origin'] = ", ".join(sorted(set(origins)))
        unique.append((output, trio, arr_time))
    return unique

# Score summary line
def generate_summary(trios, label="A1"):
    st.subheader(f"{label} – {len(trios)} result{'s' if len(trios) != 1 else ''}")
    for idx, (output, trio, arrival) in enumerate(trios):
        icons = [get_feed_icon(row['Feed']) for _, row in trio.iterrows()]
        m_path = " → ".join([f"|{int(row['M #'])}|" for _, row in trio.iterrows()])
        icon_path = "→".join(icons)
        type_desc = f"{len(trio)} descending"

        # Score logic
        strength_score = sum(1 for x in trio['M #'] if int(x) in STRENGTH_TRAVELERS)
        anchor_score = any(is_anchor(row['Origin']) for _, row in trio.iterrows())
        time_score = (arrival.time().hour == 18)

        if strength_score >= 2 and anchor_score and time_score:
            score = "Scores high"
        elif strength_score >= 1 or anchor_score:
            score = "Scores mid"
        else:
            score = "Scores low"

        summary = (
            f"{score}, {hours_ago(arrival)} hours ago, at {arrival.strftime('%Y-%m-%d %H:%M')}, "
            f"at {output}, 1x {type_desc}: {m_path} Cross [{icon_path}]"
        )

        with st.expander(summary):
            st.dataframe(trio.reset_index(drop=True)[['Feed', 'Row', 'Arrival', 'M #', 'Origin', 'Output']].assign(Type=type_desc))

# Streamlit UI
st.title("Output Position Analysis")

a1_raw = detect_descending_sequences(df)
a1_deduped = deduplicate(a1_raw)
generate_summary(a1_deduped, label="A1")

# (You’ll add B1, B2, and C1 detection here similarly)

st.info("B1, B2, and C1 logic can be added below this line.")
