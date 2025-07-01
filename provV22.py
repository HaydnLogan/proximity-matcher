import streamlit as st
import pandas as pd
from itertools import combinations
import datetime

st.title("Proximity Match & Trio Analyzer")
st.set_page_config(layout="wide")
st.title("Proximity & Trio Match Analyzer")

uploaded_file = st.file_uploader("Upload your CSV file", type="csv")
# --- File Upload ---
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if not uploaded_file:
    st.stop()

if uploaded_file:
    df = pd.read_csv(uploaded_file)
df = pd.read_csv(uploaded_file)
df['Arrival'] = pd.to_datetime(df['Arrival'])
df['Departure'] = pd.to_datetime(df['Departure'])

    # Convert columns
    df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
    df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
    df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
    df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
    df['Day'] = df['Day'].astype(str)

    st.success("CSV loaded successfully!")
# --- Query Functions ---
def proximity_pairs(df, day_filter, mname_0_target=0, mname_1_targets=[1, -1]):
    results = []
    rows = df[(df['M Name'] == mname_0_target) & (df['Day'] == day_filter)]
    for idx, row in rows.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['M Name'].isin(mname_1_targets)) &
            (df['Arrival'] < row['Arrival'])
        ]
        for m_idx, match in matches.iterrows():
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append({
                    'Summary': f"At {row['Arrival']} {match['M Name']:.3f} to {row['M Name']:.3f} @ {row['Output']:.3f}",
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
def get_excluded_pairs(df, day_filter):
    ids = set()
    rows = df[(df['M Name'] == 0) & (df['Day'] == day_filter)]
    for idx, row in rows.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['M Name'].isin([1, -1])) &
            (df['Arrival'] < row['Arrival'])
        ]
        for m_idx in matches.index:
            ids.add(tuple(sorted([idx, m_idx])))
    return ids

    def find_trios(df, target_day):
        trios = []
        grouped = df.groupby('Output')
        for output, group in grouped:
            rows = group.sort_values('Arrival')
            if len(rows) < 3:
def general_proximity_pairs(df, day_filter, exclude_ids):
    results = []
    rows = df[df['Day'] == day_filter]
    for idx, row in rows.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['M Name'] != row['M Name']) &
            (df['Arrival'] < row['Arrival']) &
            (df.index != idx)
        ]
        for m_idx, match in matches.iterrows():
            pair_ids = tuple(sorted([idx, m_idx]))
            if pair_ids in exclude_ids:
                continue
            if row['M Name'] in [1, -1] and match['M Name'] == 0:
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
            if row['M Name'] == 0 and match['M Name'] in [1, -1]:
                continue
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append({
                    'Summary': f"At {row['Arrival']} {match['M Name']:.3f} to {row['M Name']:.3f} @ {row['Output']:.3f}",
                    'Newest Arrival': row['Arrival'],
                    'Older Arrival': match['Arrival'],
                    'M Newer': row['M Name'],
                    'M Older': match['M Name'],
                    'Output': row['Output'],
                    'Origin New': row['Origin'],
                    'Origin Old': match['Origin'],
                    'Day': row['Day']
})
        return sorted(trios, key=lambda x: x['Output'], reverse=True)
    return results

def trio_matches(df):
    results = []
    grouped = df.groupby('Output')
    for output_val, group in grouped:
        if len(group) < 3:
            continue
        group_sorted = group.sort_values(by='Arrival')
        for i in range(len(group_sorted) - 2):
            trio = group_sorted.iloc[i:i+3]
            if trio.iloc[2]['Day'] != "Today [0]":
                continue
            origins = trio['Origin'].tolist()
            if not any((800 <= o <= 1300) for o in origins):
                continue
            m_vals = trio['M Name'].abs().values
            m_actual = trio['M Name'].values
            if m_vals[0] > m_vals[1] > m_vals[2]:
                direction = "Descending Trio"
            elif m_vals[0] < m_vals[1] < m_vals[2]:
                direction = "Ascending Trio"
            else:
                continue
            results.append({
                'Summary': f"At {trio.iloc[2]['Arrival']} {m_actual[0]:.3f} to {m_actual[1]:.3f} to {m_actual[2]:.3f} @ {output_val:.3f}",
                'Type': direction,
                'Oldest Arrival': trio.iloc[0]['Arrival'],
                'Middle Arrival': trio.iloc[1]['Arrival'],
                'Newest Arrival': trio.iloc[2]['Arrival'],
                'M Oldest': m_actual[0],
                'M Middle': m_actual[1],
                'M Newest': m_actual[2],
                'Output': output_val,
                'Origins': origins,
                'Days': trio['Day'].tolist()
            })
    return sorted(results, key=lambda x: x['Output'], reverse=True)

# --- Run All Queries ---
query_1_1a = proximity_pairs(df, "Today [0]")
query_1_1b = proximity_pairs(df, "Yesterday [1]")

    # Query Execution
    query_1a = match_proximity(df, "Today [0]", 0)
    query_1b = match_proximity(df, "Yesterday [1]", 0)
exclude_3a_ids = get_excluded_pairs(df, "Today [0]")
exclude_3b_ids = get_excluded_pairs(df, "Yesterday [1]")

    trios_today = find_trios(df, "Today [0]")
query_3_1a = general_proximity_pairs(df, "Today [0]", exclude_3a_ids)
query_3_1b = general_proximity_pairs(df, "Yesterday [1]", exclude_3b_ids)

    # Display
    st.header("Query 1.1a: 1→0 Matches Today")
    for i, res in enumerate(query_1a[::-1]):
        summary = f"At {res['Newest Arrival']} {res['M Older']:.3f} to {res['M Newer']:.3f} @ {res['Output']:.3f}"
        with st.expander(summary):
            st.write(pd.DataFrame([res]))
query_2_1a = trio_matches(df)

    st.header("Query 1.1b: 1→0 Matches Yesterday")
    for i, res in enumerate(query_1b[::-1]):
        summary = f"At {res['Newest Arrival']} {res['M Older']:.3f} to {res['M Newer']:.3f} @ {res['Output']:.3f}"
        with st.expander(summary):
            st.write(pd.DataFrame([res]))
# --- Display Section ---
def display_matches(title, results):
    st.subheader(f"{title} — {len(results)} matches")
    for i, match in enumerate(sorted(results, key=lambda x: x['Output'], reverse=True), 1):
        with st.expander(f"{match['Summary']}"):
            st.write(pd.DataFrame([match]).T)
    if results:
        df_export = pd.DataFrame(results)
        st.download_button(f"Download {title} as CSV", df_export.to_csv(index=False), file_name=f"{title.replace(' ', '_')}.csv", mime="text/csv")

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
# --- Outputs ---
display_matches("Query 1.1a - Today 1→0 Matches", query_1_1a)
display_matches("Query 1.1b - Yesterday 1→0 Matches", query_1_1b)
display_matches("Query 2.1a - Trios (Today)", query_2_1a)
display_matches("Query 3.1a - Today 0→0 Non-1 Matches", query_3_1a)
display_matches("Query 3.1b - Yesterday 0→0 Non-1 Matches", query_3_1b)
