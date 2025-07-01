import streamlit as st
import pandas as pd
from datetime import datetime
from itertools import combinations

st.set_page_config(page_title="Proximity Match Finder", layout="wide")
st.title("🔍 Proximity Match Finder (Pairs & Trios)")

uploaded_file = st.file_uploader("📁 Upload your CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    # Parse relevant columns
    df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
    df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
    df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
    df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
    df['Day'] = df['Day'].astype(str).str.strip().str.lower()

    # Filter options
    origin_min, origin_max = 800, 1300
    filter_origin = st.checkbox("✅ Require at least one Origin between 800 and 1300", value=True)
    run_pairs = st.checkbox("🔗 Run Pair Match Query", value=True)
    run_trios = st.checkbox("🔺 Run Trio Match Query", value=True)

    origin_check = lambda *rows: any(origin_min <= row['Origin'] <= origin_max for row in rows) if filter_origin else True

    if run_pairs:
        st.subheader("🔗 0.0 Proximity Matched Pairs")

        is_today = df['Day'].str.contains(r'\[0\]')
        zero_rows = df[(df['M Name'] == 0) & is_today]
        match_rows = df[df['M Name'].isin([1, -1])]

        match_pairs = []
        for _, zrow in zero_rows.iterrows():
            for _, mrow in match_rows.iterrows():
                if (
                    zrow['Output'] == mrow['Output'] and
                    mrow['Arrival'] < zrow['Arrival'] and
                    origin_check(zrow, mrow)
                ):
                    match_pairs.append((zrow, mrow))

        st.success(f"Found {len(match_pairs)} matched pair(s).")
        for idx, (r1, r2) in enumerate(match_pairs):
            with st.expander(f"Match {idx+1}"):
                st.write("🔹 **Row 1 (M Name = 0)**")
                st.write(r1)
                st.write("🔹 **Row 2 (M Name = ±1)**")
                st.write(r2)

    if run_trios:
        st.subheader("🔺 Matched Trios")

        def is_valid_trio(trio):
            mnames = [abs(r['M Name']) for r in trio]
            arrivals = [r['Arrival'] for r in trio]
            if len(set(r['Output'] for r in trio)) > 1:
                return False

            m_order = sorted(zip(mnames, arrivals), key=lambda x: x[0])
            sorted_arrivals = [a for _, a in m_order]

            is_ascending = sorted_arrivals == sorted(sorted_arrivals)
            is_descending = sorted_arrivals == sorted(sorted_arrivals, reverse=True)
            newest_row = max(trio, key=lambda r: r['Arrival'])
            is_today = '[0]' in newest_row['Day']
            return (is_ascending or is_descending) and is_today and origin_check(*trio)

        trios_found = []
        for _, group in df.groupby('Output'):
            if len(group) >= 3:
                for trio in combinations(group.to_dict('records'), 3):
                    if is_valid_trio(trio):
                        trios_found.append(trio)

        st.success(f"Found {len(trios_found)} matched trio(s).")
        for idx, trio in enumerate(trios_found):
            with st.expander(f"Trio {idx+1}"):
                for i, row in enumerate(sorted(trio, key=lambda r: r['Arrival'])):
                    st.write(f"🔸 Row {i+1}")
                    st.write(row)
