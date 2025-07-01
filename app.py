import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Proximity Match Analyzer", layout="wide")

st.title("🔍 Proximity & Trio Match Analyzer")

# Upload CSV
uploaded_file = st.file_uploader("Upload your dataset CSV", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Convert columns to proper types
    df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
    df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
    df['M #'] = pd.to_numeric(df['M #'], errors='coerce')
    df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')

    # Filter for Origin range
    min_origin = st.slider("Minimum Origin", 0, 3000, 800)
    max_origin = st.slider("Maximum Origin", 0, 3000, 1300)

    st.markdown("---")

    # ------------------
    # Query 1: 0 Proximity Pair
    # ------------------
    st.header("📌 Query 1: 0.0 Proximity Match Pairs")

    zero_rows = df[(df['M #'] == 0) & (df['Day'].str.strip().str.lower() == 'today')]
    match_rows = df[df['M #'].isin([1, -1])]

    match_pairs = []

    for _, zero_row in zero_rows.iterrows():
        for _, match_row in match_rows.iterrows():
            if (
                zero_row['Output'] == match_row['Output'] and
                match_row['Arrival'] < zero_row['Arrival'] and
                (min_origin <= zero_row['Origin'] <= max_origin or min_origin <= match_row['Origin'] <= max_origin)
            ):
                match_pairs.append((zero_row, match_row))

    st.write(f"Found **{len(match_pairs)}** matched pairs")
    for z, m in match_pairs:
        st.write("---")
        st.write("🔹 Zero Row:")
        st.dataframe(pd.DataFrame([z]))
        st.write("🔸 Matched Row (±1):")
        st.dataframe(pd.DataFrame([m]))

    # ------------------
    # Query 2: Trios
    # ------------------
    st.header("🔁 Query 2: Ascending/Descending Trios")

    df_today = df[df['Day'].str.strip().str.lower() == 'today']

    # Group by Output
    output_groups = df.groupby('Output')
    trio_results = []

    for output_val, group in output_groups:
        if len(group) < 3:
            continue

        # All combinations of 3 rows with same Output
        group_sorted = group.sort_values('Arrival')
        for i in range(len(group_sorted) - 2):
            trio = group_sorted.iloc[i:i+3]
            arrival_order = list(trio['Arrival'])
            m_values = list(trio['M #'].abs())

            # Check if one row is from today
            if 'today' not in [str(x).strip().lower() for x in trio['Day']]:
                continue

            # Check Origin filter
            if not any((min_origin <= x <= max_origin) for x in trio['Origin']):
                continue

            # Ascending or Descending check
            m_sorted = sorted(m_values)
            if m_values == m_sorted:
                trio_type = 'Ascending Trio'
            elif m_values == m_sorted[::-1]:
                trio_type = 'Descending Trio'
            else:
                continue

            # Special if middle is negative
            middle_val = trio.iloc[1]['M #']
            special = 'Special ' if middle_val < 0 else ''

            trio_results.append((special + trio_type, trio))

    st.write(f"Found **{len(trio_results)}** matched trios")
    for trio_type, trio_df in trio_results:
        st.write(f"### {trio_type}")
        st.dataframe(trio_df)
        st.write("---")
