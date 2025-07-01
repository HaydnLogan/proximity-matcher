import streamlit as st
import pandas as pd
from itertools import combinations
import datetime

st.set_page_config(layout="wide")
st.title("Proximity Match & Trio Analyzer")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if not uploaded_file:
    st.stop()

# Read and clean the CSV
df = pd.read_csv(uploaded_file)

# Safe conversions
for col in ['Arrival', 'Departure']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    else:
        st.error(f"Missing expected column: {col}")
        st.stop()

# Convert key columns
df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
df['Day'] = df['Day'].astype(str)

# Drop rows with invalid Arrival or Output
initial_len = len(df)
df = df.dropna(subset=['Arrival', 'Output'])
removed_rows = initial_len - len(df)
if removed_rows > 0:
    st.warning(f"{removed_rows} rows removed due to invalid Arrival or Output values.")

# --- Query Functions ---

def match_1_to_0(df, target_day):
    results = []
    subset = df[(df['M Name'] == 0) & (df['Day'] == target_day)]
    for _, row in subset.iterrows():
        candidates = df[
            (df['Output'] == row['Output']) &
            (df['M Name'].isin([1, -1])) &
            (df['Arrival'] < row['Arrival'])
        ]
        for _, match in candidates.iterrows():
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
    return sorted(results, key=lambda x: x['Output'], reverse=True)

def match_zero_pairs(df, target_day, exclude_ids=set()):
    results = []
    subset = df[df['Day'] == target_day]
    zeroes = subset[subset['M Name'] == 0]

    for _, row in zeroes.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['M Name'] == 0) &
            (df['Arrival'] < row['Arrival'])
        ]
        for _, match in matches.iterrows():
            id_pair = frozenset([row['Arrival'], match['Arrival']])
            if id_pair in exclude_ids:
                continue
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
                exclude_ids.add(id_pair)
    return sorted(results, key=lambda x: x['Output'], reverse=True)

def find_trios(df, target_day):
    trios = []
    for output, group in df.groupby('Output'):
        group = group.sort_values('Arrival')
        if len(group) < 3:
            continue
        for combo in combinations(group.index, 3):
            trio_df = group.loc[list(combo)].sort_values('Arrival')
            arrival_vals = trio_df['Arrival'].tolist()
            m_vals = trio_df['M Name'].tolist()
            abs_vals = [abs(m) for m in m_vals]

            # Check valid ascending or descending
            if abs_vals[0] > abs_vals[1] > abs_vals[2]:
                kind = "Descending Trio"
            elif abs_vals[0] < abs_vals[1] < abs_vals[2]:
                kind = "Ascending Trio"
            else:
                continue

            # Day filter
            if not str(trio_df.iloc[2]['Day']).startswith(target_day):
                continue

            # Origin filter
            if not trio_df['Origin'].between(800, 1300).any():
                continue

            trios.append({
                'Arrival': arrival_vals,
                'M Name': m_vals,
                'Output': output,
                'Type': kind
            })
    return sorted(trios, key=lambda x: x['Output'], reverse=True)

# --- Run Queries ---
q_1a = match_1_to_0(df, "Today [0]")
q_1b = match_1_to_0(df, "Yesterday [1]")

exclude_1a_pairs = {frozenset([res['Newest Arrival'], res['Older Arrival']]) for res in q_1a}

q_3a = match_zero_pairs(df, "Today [0]", exclude_ids=exclude_1a_pairs)
q_3b = match_zero_pairs(df, "Yesterday [1]", exclude_ids=exclude_1a_pairs)

trios = find_trios(df, "Today [0]")

# --- Display Results ---

def show_matches(title, results):
    st.header(title)
    for res in results:
        summary = f"At {res['Newest Arrival']} {res['M Older']:.3f} to {res['M Newer']:.3f} @ {res['Output']:.3f}"
        with st.expander(summary):
            st.dataframe(pd.DataFrame([res]))

def show_trios(title, results):
    st.header(title)
    for res in results:
        arrival_str = res['Arrival'][-1].strftime('%-m/%-d/%Y %H:%M')
        mvals = res['M Name']
        summary = f"At {arrival_str} {mvals[0]:.3f} to {mvals[1]:.3f} to {mvals[2]:.3f} @ {res['Output']:.3f} ({res['Type']})"
        with st.expander(summary):
            st.dataframe(pd.DataFrame({
                "Arrival": res['Arrival'],
                "M Name": res['M Name'],
                "Output": [res['Output']] * 3,
                "Type": [res['Type']] * 3
            }))

# Query Displays
show_matches("Query 1.1a: 1→0 Matches Today", q_1a)
show_matches("Query 1.1b: 1→0 Matches Yesterday", q_1b)
show_trios("Query 2.1a: Ascending/Descending Trios Today", trios)
show_matches("Query 3.1a: 0→0 Matches Today (Excl. 1→0)", q_3a)
show_matches("Query 3.1b: 0→0 Matches Yesterday (Excl. 1→0)", q_3b)

# Optional: Export results
with st.expander("📤 Export All Matches to CSV"):
    if st.button("Download All Matches"):
        all_matches_df = pd.DataFrame(q_1a + q_1b + q_3a + q_3b)
        st.download_button("Download CSV", all_matches_df.to_csv(index=False), "proximity_matches.csv")
