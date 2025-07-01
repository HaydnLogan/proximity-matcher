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

# Convert columns
for col in ['Arrival', 'Departure']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
df['Day'] = df['Day'].astype(str)

# Drop invalid rows
initial_len = len(df)
df = df.dropna(subset=['Arrival', 'Output'])
df = df[df['Output'] > 0]  # Remove rows with Output <= 0

# Remove rows with unique Outputs (not matching prev or next)
df = df.sort_values('Arrival')
df['Output_prev'] = df['Output'].shift(1)
df['Output_next'] = df['Output'].shift(-1)
df = df[(df['Output'] == df['Output_prev']) | (df['Output'] == df['Output_next'])]
df = df.drop(columns=['Output_prev', 'Output_next'])
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

def query_3x(df, target_day, mname_condition, target_m, label):
    results = []
    df_day = df[df['Day'] == target_day]
    df_sorted = df_day.sort_values('Arrival')

    for idx1, row1 in df_sorted.iterrows():
        for idx2, row2 in df_sorted.iterrows():
            if row1['Arrival'] >= row2['Arrival']:
                continue
            if not mname_condition(row1['M Name'], row2['M Name']):
                continue
            if (800 <= row1['Origin'] <= 1300) or (800 <= row2['Origin'] <= 1300):
                results.append({
                    'Row New': idx2,
                    'Row Old': idx1,
                    'Newest Arrival': row2['Arrival'],
                    'Older Arrival': row1['Arrival'],
                    'M Newer': row2['M Name'],
                    'M Older': row1['M Name'],
                    'Output': row1['Output'],
                    'Origin New': row2['Origin'],
                    'Origin Old': row1['Origin'],
                    'Day': row2['Day'],
                    'Label': label
                })
    return results

# --- Query Logic ---
query_1a = match_proximity(df, "Today [0]")
query_1b = match_proximity(df, "Yesterday [1]")
trios_today = find_trios(df, "Today [0]")
trios_yesterday = find_trios(df, "Yesterday [1]")

query_3_1a = query_3x(df, "Today [0]", lambda x, y: y in [1, -1] and x not in [1, -1], "Query 3.1a - Today #→±1")
query_3_1b = query_3x(df, "Yesterday [1]", lambda x, y: y in [1, -1] and x not in [1, -1], "Query 3.1b - Yesterday #→±1")
query_3_2a = query_3x(df, "Today [0]", lambda x, y: y not in [1, -1] and x in [1, -1], "Query 3.2a - Today #→# (≠±1)")
query_3_2b = query_3x(df, "Yesterday [1]", lambda x, y: y not in [1, -1] and x in [1, -1], "Query 3.2b - Yesterday #→# (≠±1)")

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
