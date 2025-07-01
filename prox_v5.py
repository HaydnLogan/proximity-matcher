import streamlit as st
import pandas as pd
from itertools import combinations

st.set_page_config(layout="wide")
st.title("Proximity & Trio Pair Analyzer")

# Upload CSV
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if not uploaded_file:
    st.stop()

# Load and clean data
df = pd.read_csv(uploaded_file)
df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
df['Day'] = df['Day'].astype(str)
df.dropna(subset=['Arrival', 'M Name', 'Output'], inplace=True)

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
                    'Row New': idx,
                    'Row Old': m_idx,
                    'Newest Arrival': row['Arrival'],
                    'Older Arrival': match['Arrival'],
                    'M Newer': row['M Name'],
                    'M Older': match['M Name'],
                    'Origin New': row['Origin'],
                    'Origin Old': match['Origin'],
                    'Day': row['Day']
                })
    return results

def any_to_one_pairs(df, day_filter):
    results = []
    rows = df[(df['M Name'] == 1) & (df['Day'] == day_filter)]
    for idx, row in rows.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['M Name'] != row['M Name']) &
            (df['Arrival'] < row['Arrival'])
        ]
        for m_idx, match in matches.iterrows():
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append({
                    'Row New': idx,
                    'Row Old': m_idx,
                    'Newest Arrival': row['Arrival'],
                    'Older Arrival': match['Arrival'],
                    'M Newer': row['M Name'],
                    'M Older': match['M Name'],
                    'Origin New': row['Origin'],
                    'Origin Old': match['Origin'],
                    'Day': row['Day']
                })
    return results

def exclude_ids_from(df, pair_results):
    return {tuple(sorted([res['Row New'], res['Row Old']])) for res in pair_results}

def general_pairs(df, day_filter, excluded_ids):
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
            pair_id = tuple(sorted([idx, m_idx]))
            if pair_id in excluded_ids:
                continue
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append({
                    'Row New': idx,
                    'Row Old': m_idx,
                    'Newest Arrival': row['Arrival'],
                    'Older Arrival': match['Arrival'],
                    'M Newer': row['M Name'],
                    'M Older': match['M Name'],
                    'Origin New': row['Origin'],
                    'Origin Old': match['Origin'],
                    'Day': row['Day']
                })
    return results

def find_trios(df, target_day):
    trios = []
    grouped = df.groupby('Output')
    for output, group in grouped:
        group = group.sort_values('Arrival')
        if len(group) < 3:
            continue
        for combo in combinations(group.index, 3):
            trio = group.loc[list(combo)].sort_values('Arrival')
            if trio.iloc[-1]['Day'] != target_day:
                continue
            origins = trio['Origin'].tolist()
            if not any((800 <= o <= 1300) for o in origins):
                continue
            m_vals = trio['M Name'].abs().tolist()
            m_actual = trio['M Name'].tolist()
            if m_vals[0] > m_vals[1] > m_vals[2]:
                kind = "Descending Trio"
            elif m_vals[0] < m_vals[1] < m_vals[2]:
                kind = "Ascending Trio"
            else:
                continue
            trios.append({
                'Rows': trio.index.tolist(),
                'Arrival': trio['Arrival'].tolist(),
                'M Name': m_actual,
                'Origin': trio['Origin'].tolist(),
                'Output': output,
                'Type': kind
            })
    return sorted(trios, key=lambda x: x['Output'], reverse=True)

# --- Query Execution ---
query_1_1a = proximity_pairs(df, "Today [0]")
query_1_1b = proximity_pairs(df, "Yesterday [1]")

query_3_1a = any_to_one_pairs(df, "Today [0]")
query_3_1b = any_to_one_pairs(df, "Yesterday [1]")

exclude_ids = (
    exclude_ids_from(df, query_1_1a) |
    exclude_ids_from(df, query_1_1b) |
    exclude_ids_from(df, query_3_1a) |
    exclude_ids_from(df, query_3_1b)
)

query_3_2a = general_pairs(df, "Today [0]", exclude_ids)
query_3_2b = general_pairs(df, "Yesterday [1]", exclude_ids)

query_2_1a = find_trios(df, "Today [0]")
query_2_1b = find_trios(df, "Yesterday [1]")

# --- Display Utilities ---
def pluralize(word, count):
    return f"{count} {word if count == 1 else word + 's'}"

def display_pairs(title, results):
    count = len(results)
    st.subheader(f"{title} — {pluralize('pair', count)}")
    for i, res in enumerate(results):
        summary = f"At {res['Newest Arrival']} {res['M Older']:.3f} to {res['M Newer']:.3f}"
        with st.expander(summary):
            df_display = pd.DataFrame([
                {
                    "Row": res["Row Old"],
                    "Arrival": res["Older Arrival"],
                    "M Name": res["M Older"],
                    "Origin": res["Origin Old"],
                    "Day": res["Day"]
                },
                {
                    "Row": res["Row New"],
                    "Arrival": res["Newest Arrival"],
                    "M Name": res["M Newer"],
                    "Origin": res["Origin New"],
                    "Day": res["Day"]
                }
            ])
            st.write(df_display)

def display_trios(title, trios):
    count = len(trios)
    st.subheader(f"{title} — {pluralize('trio', count)}")
    for i, trio in enumerate(trios):
        latest_time = trio['Arrival'][-1].strftime('%-m/%-d/%Y %H:%M')
        mvals = trio['M Name']
        summary = f"At {latest_time} {mvals[0]:.3f} to {mvals[1]:.3f} to {mvals[2]:.3f} @ {trio['Output']:.3f} ({trio['Type']})"
        with st.expander(summary):
            df_trio = pd.DataFrame({
                "Row": trio['Rows'],
                "Arrival": trio['Arrival'],
                "M Name": trio['M Name'],
                "Origin": trio['Origin'],
                "Output": [trio['Output']] * 3,
                "Type": [trio['Type']] * 3
            }).reset_index()
            st.write(df_trio)

# --- Output Display ---
display_pairs("Query 1.1a - Today 1→0 Pairs", query_1_1a)
display_pairs("Query 1.1b - Yesterday 1→0 Pairs", query_1_1b)

display_trios("Query 2.1a - Trios (Today)", query_2_1a)
display_trios("Query 2.1b - Trios (Yesterday)", query_2_1b)

display_pairs("Query 3.1a - Today #→1 Pairs", query_3_1a)
display_pairs("Query 3.1b - Yesterday #→1 Pairs", query_3_1b)

display_pairs("Query 3.2a - Today #→# Non-query 1.1 or 3.1 Pairs", query_3_2a)
display_pairs("Query 3.2b - Yesterday #→# Non-query 1.1 or 3.1 Pairs", query_3_2b)
