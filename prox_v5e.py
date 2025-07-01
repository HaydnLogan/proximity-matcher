import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Proximity & Trio Match Analyzer v4 with Q.3")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if not uploaded_file:
    st.stop()

df = pd.read_csv(uploaded_file)

# --- Data Cleaning ---
for col in ['Arrival', 'Departure']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
df['Day'] = df['Day'].astype(str)

# Remove rows with invalid Arrival or Output
df.dropna(subset=['Arrival', 'Output'], inplace=True)

# --- Query 3.1a and 3.1b ---
def query_3_1(df, day_filter):
    pairs = []
    subset = df[df['Day'] == day_filter]
    ones = subset[subset['M Name'].isin([1.0, -1.0])]
    for idx1, row1 in ones.iterrows():
        matches = subset[
            (subset['Output'] == row1['Output']) &
            (subset['Arrival'] < row1['Arrival']) &
            (subset.index != idx1)
        ]
        for idx2, row2 in matches.iterrows():
            if row2['M Name'] in [1.0, -1.0]:
                continue
            if (800 <= row1['Origin'] <= 1300) or (800 <= row2['Origin'] <= 1300):
                older_idx, newer_idx = (idx2, idx1) if row2['Arrival'] < row1['Arrival'] else (idx1, idx2)
                pairs.append((older_idx, newer_idx))
    return pairs

# --- Query 3.2a and 3.2b ---
def query_3_2(df, day_filter, exclude_pairs):
    pairs = []
    subset = df[df['Day'] == day_filter]
    for idx1, row1 in subset.iterrows():
        matches = subset[
            (subset['Output'] == row1['Output']) &
            (subset['Arrival'] < row1['Arrival']) &
            (subset.index != idx1)
        ]
        for idx2, row2 in matches.iterrows():
            # Skip if M Names are ±1.0 or already used in previous queries
            if {row1['M Name'], row2['M Name']} & {1.0, -1.0}:
                continue
            pair_ids = tuple(sorted([idx1, idx2]))
            if pair_ids in exclude_pairs:
                continue
            if (800 <= row1['Origin'] <= 1300) or (800 <= row2['Origin'] <= 1300):
                older_idx, newer_idx = (idx2, idx1) if row2['Arrival'] < row1['Arrival'] else (idx1, idx2)
                pairs.append((older_idx, newer_idx))
    return pairs

# --- Display Function ---
def display_pair_results(title, pair_list):
    st.subheader(f"{title} — {len(pair_list)} {'pair' if len(pair_list)==1 else 'pairs'}")
    for i, (older_idx, newer_idx) in enumerate(pair_list):
        older = df.loc[older_idx]
        newer = df.loc[newer_idx]
        summary = f"At {newer['Arrival']} {older['M Name']:.3f} to {newer['M Name']:.3f} @ {newer['Output']:.3f}"
        with st.expander(f"{i+1}. {summary}"):
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

# --- Run Queries ---
query_3_1a = query_3_1(df, "Today [0]")
query_3_1b = query_3_1(df, "Yesterday [1]")

# Collect used pairs to avoid reusing them in 3.2
used_pairs_a = set(tuple(sorted(p)) for p in query_3_1a)
used_pairs_b = set(tuple(sorted(p)) for p in query_3_1b)

query_3_2a = query_3_2(df, "Today [0]", used_pairs_a)
query_3_2b = query_3_2(df, "Yesterday [1]", used_pairs_b)

# --- Display Results ---
display_pair_results("Query 3.1a - Today #→±1", query_3_1a)
display_pair_results("Query 3.1b - Yesterday #→±1", query_3_1b)
display_pair_results("Query 3.2a - Today #→# (≠±1)", query_3_2a)
display_pair_results("Query 3.2b - Yesterday #→# (≠±1)", query_3_2b)
