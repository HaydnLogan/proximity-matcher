import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Proximity & Trio Match Analyzer (v4 with 3.2)")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if not uploaded_file:
    st.stop()

df = pd.read_csv(uploaded_file)

# --- Data Cleaning ---
for col in ['Arrival', 'Departure']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    else:
        st.error(f"Missing expected column: {col}")
        st.stop()

df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
df['Day'] = df['Day'].astype(str)

initial_len = len(df)
df = df.dropna(subset=['Arrival', 'Output'])
if (removed := initial_len - len(df)) > 0:
    st.warning(f"{removed} rows removed due to invalid Arrival or Output values.")

# --- Query Functions ---
def query_1_pairs(df, day_filter):
    results = []
    rows = df[(df['M Name'] == 0) & (df['Day'] == day_filter)]
    for idx, row in rows.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['M Name'].isin([1, -1])) &
            (df['Arrival'] < row['Arrival'])
        ]
        for m_idx, match in matches.iterrows():
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append((m_idx, idx))
    return results

def query_3_1_pairs(df, day_filter):
    results = []
    target_ones = df[(df['M Name'].isin([1.0, -1.0])) & (df['Day'] == day_filter)]
    for idx, one in target_ones.iterrows():
        matches = df[
            (df['Output'] == one['Output']) &
            (df['Arrival'] < one['Arrival']) &
            (~df['M Name'].isin([1.0, -1.0])) &
            (df.index != idx)
        ]
        for m_idx, match in matches.iterrows():
            if (800 <= match['Origin'] <= 1300) or (800 <= one['Origin'] <= 1300):
                results.append((m_idx, idx))
    return results

def get_used_pair_ids(*queries):
    ids = set()
    for q in queries:
        for pair in q:
            ids.add(tuple(sorted(pair)))
    return ids

def query_3_2_pairs(df, day_filter, exclude_ids):
    results = []
    rows = df[df['Day'] == day_filter]
    for idx, row in rows.iterrows():
        if row['M Name'] in [1.0, -1.0]:
            continue
        matches = df[
            (df['Output'] == row['Output']) &
            (df['Arrival'] < row['Arrival']) &
            (~df['M Name'].isin([1.0, -1.0])) &
            (df.index != idx)
        ]
        for m_idx, match in matches.iterrows():
            pair_ids = tuple(sorted([row['Arrival'], match['Arrival']]))
            if (m_idx, idx) in exclude_ids or (idx, m_idx) in exclude_ids:
                continue
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append((m_idx, idx))
    return results

# --- Execute Queries ---
query_1_1a = query_1_pairs(df, "Today [0]")
query_1_1b = query_1_pairs(df, "Yesterday [1]")

query_3_1a = query_3_1_pairs(df, "Today [0]")
query_3_1b = query_3_1_pairs(df, "Yesterday [1]")

used_ids_a = get_used_pair_ids(query_1_1a, query_3_1a)
used_ids_b = get_used_pair_ids(query_1_1b, query_3_1b)

query_3_2a = query_3_2_pairs(df, "Today [0]", used_ids_a)
query_3_2b = query_3_2_pairs(df, "Yesterday [1]", used_ids_b)

# --- Display ---
def display_pair_results(title, pair_list):
    st.subheader(f"{title} — {len(pair_list)} {'pair' if len(pair_list)==1 else 'pairs'}")
    for i, (older_idx, newer_idx) in enumerate(pair_list):
        older = df.loc[older_idx]
        newer = df.loc[newer_idx]
        with st.expander(f"{i+1}. Row {older_idx} → Row {newer_idx}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("Older Entry")
                st.write(pd.DataFrame({
                    'Row': [older_idx],
                    'Arrival': [older['Arrival']],
                    'M Name': [older['M Name']],
                    'Origin': [older['Origin']],
                    'Day': [older['Day']],
                }).T.rename(columns={0: ''}))
            with col2:
                st.write("Newer Entry")
                st.write(pd.DataFrame({
                    'Row': [newer_idx],
                    'Arrival': [newer['Arrival']],
                    'M Name': [newer['M Name']],
                    'Origin': [newer['Origin']],
                    'Day': [newer['Day']],
                }).T.rename(columns={0: ''}))

# --- Output ---
display_pair_results("Query 1.1a - Today 1→0 Pairs", query_1_1a)
display_pair_results("Query 1.1b - Yesterday 1→0 Pairs", query_1_1b)
display_pair_results("Query 3.1a - Today #→±1", query_3_1a)
display_pair_results("Query 3.1b - Yesterday #→±1", query_3_1b)
display_pair_results("Query 3.2a - Today #→# (≠±1)", query_3_2a)
display_pair_results("Query 3.2b - Yesterday #→# (≠±1)", query_3_2b)
