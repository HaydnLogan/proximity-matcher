import streamlit as st
import pandas as pd
from itertools import combinations

st.set_page_config(layout="wide")
st.title("Proximity & Trio Match Analyzer")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if not uploaded_file:
    st.stop()

df = pd.read_csv(uploaded_file)

# --- Data Cleanup ---
for col in ['Arrival', 'Departure']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
df['Day'] = df['Day'].astype(str)

initial_len = len(df)
df = df.dropna(subset=['Arrival', 'Output'])
df = df[df['Output'] > 0]

# Remove rows where Output is not equal to neighbor row Outputs
df = df.sort_values(by='Arrival').reset_index(drop=True)
mask = (df['Output'].shift(1) == df['Output']) | (df['Output'].shift(-1) == df['Output'])
df = df[mask].copy()
filtered_len = len(df)
removed_rows = initial_len - filtered_len

if removed_rows > 0:
    st.warning(f"{removed_rows:,} rows removed due to invalid or isolated Output values.")
if df.empty:
    st.error("No valid data remains after cleaning. Please upload a valid file.")
    st.stop()

# --- Helper Functions ---
def match_proximity(df, target_day):
    results = []
    today_rows = df[(df['M Name'] == 0) & (df['Day'] == target_day)]
    for idx, row in today_rows.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['M Name'].isin([1, -1])) &
            (df['Arrival'] < row['Arrival'])
        ]
        for midx, match in matches.iterrows():
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append({
                    'Row New': idx,
                    'Row Old': midx,
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
            if not trio_df.iloc[-1]['Day'].startswith(target_day):
                continue
            if not trio_df['Origin'].between(800, 1300).any():
                continue
            m_vals = trio_df['M Name'].abs().tolist()
            actual_m = trio_df['M Name'].tolist()
            if m_vals[0] > m_vals[1] > m_vals[2]:
                kind = "Descending Trio"
            elif m_vals[0] < m_vals[1] < m_vals[2]:
                kind = "Ascending Trio"
            else:
                continue
            trios.append({
                'Arrival': trio_df['Arrival'].tolist(),
                'M Name': actual_m,
                'Output': output,
                'Type': kind,
                'Origins': trio_df['Origin'].tolist(),
                'Rows': trio_df.index.tolist()
            })
    return sorted(trios, key=lambda x: x['Output'], reverse=True)

def series_3_matches(df, target_day, pair_type):
    results = []
    is_today = df['Day'] == target_day
    df_filtered = df[is_today]
    for idx_a, row_a in df_filtered.iterrows():
        for idx_b, row_b in df.iterrows():
            if idx_a == idx_b or row_a['Output'] != row_b['Output']:
                continue
            if pair_type == "3.1":
                cond_mname = (row_a['M Name'] in [1.0, -1.0]) != (row_b['M Name'] in [1.0, -1.0])
            else:  # pair_type == "3.2"
                cond_mname = (row_a['M Name'] not in [1.0, -1.0]) and (row_b['M Name'] not in [1.0, -1.0])
            if not cond_mname:
                continue
            if row_a['Arrival'] < row_b['Arrival']:
                newer, older = row_b, row_a
                idx_new, idx_old = idx_b, idx_a
            else:
                newer, older = row_a, row_b
                idx_new, idx_old = idx_a, idx_b
            if not (800 <= newer['Origin'] <= 1300 or 800 <= older['Origin'] <= 1300):
                continue
            results.append({
                'Row New': idx_new,
                'Row Old': idx_old,
                'Newest Arrival': newer['Arrival'],
                'Older Arrival': older['Arrival'],
                'M Newer': newer['M Name'],
                'M Older': older['M Name'],
                'Output': newer['Output'],
                'Origin New': newer['Origin'],
                'Origin Old': older['Origin'],
                'Day': newer['Day']
            })
    return results

# --- Run Queries ---
query_1a = match_proximity(df, "Today [0]")
query_1b = match_proximity(df, "Yesterday [1]")
trios_today = find_trios(df, "Today [0]")
trios_yesterday = find_trios(df, "Yesterday [1]")
query_3_1a = series_3_matches(df, "Today [0]", "3.1")
query_3_1b = series_3_matches(df, "Yesterday [1]", "3.1")
query_3_2a = series_3_matches(df, "Today [0]", "3.2")
query_3_2b = series_3_matches(df, "Yesterday [1]", "3.2")

# --- Display Functions ---
def display_pairs(title, results):
    label = "pair" if len(results) == 1 else "pairs"
    st.subheader(f"{title} — {len(results)} {label}")
    for i, res in enumerate(results[::-1]):
        summary = f"At {res['Newest Arrival']} {res['M Older']:.3f} to {res['M Newer']:.3f} @ {res['Output']:,.3f}"
        with st.expander(summary):
            df_pair = pd.DataFrame([
                [res['Row Old'], res['Older Arrival'], res['M Older'], res['Origin Old'], res['Day']],
                [res['Row New'], res['Newest Arrival'], res['M Newer'], res['Origin New'], res['Day']]
            ], columns=["Row", "Arrival", "M Name", "Origin", "Day"])
            df_pair.index = ["", ""]
            st.write(df_pair)

def display_trios(title, trios):
    label = "trio" if len(trios) == 1 else "trios"
    st.subheader(f"{title} — {len(trios)} {label}")
    for i, trio in enumerate(trios):
        arr_str = trio['Arrival'][-1].strftime('%Y-%m-%d %H:%M:%S')
        mvals = trio['M Name']
        summary = f"At {arr_str} {mvals[0]:.3f} to {mvals[1]:.3f} to {mvals[2]:.3f} @ {trio['Output']:,.3f} ({trio['Type']})"
        with st.expander(summary):
            df_trio = pd.DataFrame({
                "Row": trio["Rows"],
                "Arrival": trio["Arrival"],
                "M Name": trio["M Name"],
                "Origin": trio["Origins"],
                "Output": [trio["Output"]] * 3,
                "Type": [trio["Type"]] * 3
            })
            df_trio.index.name = ""
            st.write(df_trio)

# --- Display Results ---
display_pairs("Query 1.1a - Today 1→0 Pairs", query_1a)
display_pairs("Query 1.1b - Yesterday 1→0 Pairs", query_1b)
display_trios("Query 2.1a - Trios (Today)", trios_today)
display_trios("Query 2.1b - Trios (Yesterday)", trios_yesterday)
display_pairs("Query 3.1a - Today #→±1", query_3_1a)
display_pairs("Query 3.1b - Yesterday #→±1", query_3_1b)
display_pairs("Query 3.2a - Today #→# (≠±1)", query_3_2a)
display_pairs("Query 3.2b - Yesterday #→# (≠±1)", query_3_2b)
