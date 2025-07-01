import streamlit as st
import pandas as pd
from itertools import combinations
import datetime

st.title("Proximity Match & Trio Analyzer")

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Convert columns
    df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
    df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
    df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
    df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
    df['Day'] = df['Day'].astype(str)

    st.success("CSV loaded successfully!")

    # Helper function
    def match_proximity(df, target_day, target_val):
        results = []
        today_rows = df[(df['M Name'] == 0) & (df['Day'] == target_day)]
        for idx, row in today_rows.iterrows():
            matches = df[
                (df['Output'] == row['Output']) &
                (df['M Name'].isin([1, -1])) &
                (df['Arrival'] < row['Arrival'])
            ]
            for _, match in matches.iterrows():
                if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                    results.append({
                        'Newest Arrival': row['Arrival'],
                        'Older Arrival': match['Arrival'],
                        'M Newer': row['M Name'],
                        'M Older': match['M Name'],
                        'Output': row['Output'],
                        'Origin New': row['Origin'],
                        'Origin Old': match['Origin'],
                        'Day': row['Day']
                    })
        return results

    def find_trios(df, target_day):
        trios = []
        grouped = df.groupby('Output')
        for output, group in grouped:
            rows = group.sort_values('Arrival')
            if len(rows) < 3:
                continue
            for combo in combinations(rows.index, 3):
                trio_df = rows.loc[list(combo)].sort_values('Arrival')
                m_vals = trio_df['M Name'].abs().tolist()
                if m_vals[0] > m_vals[1] > m_vals[2]:
                    kind = "Descending Trio"
                elif m_vals[0] < m_vals[1] < m_vals[2]:
                    kind = "Ascending Trio"
                else:
                    continue
                if not trio_df.iloc[-1]['Day'].startswith(target_day):
                    continue
                if not trio_df['Origin'].between(800, 1300).any():
                    continue
                trios.append({
                    'Arrival': trio_df['Arrival'].tolist(),
                    'M Name': trio_df['M Name'].tolist(),
                    'Output': output,
                    'Type': kind
                })
        return sorted(trios, key=lambda x: x['Output'], reverse=True)

    # Query Execution
    query_1a = match_proximity(df, "Today [0]", 0)
    query_1b = match_proximity(df, "Yesterday [1]", 0)

    trios_today = find_trios(df, "Today [0]")

    # Display
    st.header("Query 1.1a: 1→0 Matches Today")
    for i, res in enumerate(query_1a[::-1]):
        summary = f"At {res['Newest Arrival']} {res['M Older']:.3f} to {res['M Newer']:.3f} @ {res['Output']:.3f}"
        with st.expander(summary):
            st.write(pd.DataFrame([res]))

    st.header("Query 1.1b: 1→0 Matches Yesterday")
    for i, res in enumerate(query_1b[::-1]):
        summary = f"At {res['Newest Arrival']} {res['M Older']:.3f} to {res['M Newer']:.3f} @ {res['Output']:.3f}"
        with st.expander(summary):
            st.write(pd.DataFrame([res]))

    st.header("Query 2.1a: Ascending/Descending Trios Today")
    for i, trio in enumerate(trios_today):
        arrival_str = trio['Arrival'][-1].strftime('%-m/%-d/%Y %H:%M')
        mvals = trio['M Name']
        summary = f"At {arrival_str} {mvals[0]:.3f} to {mvals[1]:.3f} to {mvals[2]:.3f} @ {trio['Output']:.3f} ({trio['Type']})"
        with st.expander(summary):
            st.write(pd.DataFrame({
                "Arrival": trio['Arrival'],
                "M Name": trio['M Name'],
                "Output": [trio['Output']] * 3,
                "Type": [trio['Type']] * 3
            }))
