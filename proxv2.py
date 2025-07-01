import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Proximity & Trio Match Analyzer")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if not uploaded_file:
    st.stop()

df = pd.read_csv(uploaded_file)

# Safe conversion of Arrival and Departure to datetime
for col in ['Arrival', 'Departure']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    else:
        st.error(f"Missing expected column: {col}")
        st.stop()

# Convert Output to numeric (in case it's read as string)
df['Output'] = pd.to_numeric(df['Output'], errors='coerce')

# Drop rows with missing Arrival or Output
initial_len = len(df)
df = df.dropna(subset=['Arrival', 'Output'])
filtered_len = len(df)

# Optional: notify user of dropped rows
removed_rows = initial_len - filtered_len
if removed_rows > 0:
    st.warning(f"{removed_rows} rows were removed due to invalid Arrival or Output values.")

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

exclude_3a_ids = get_excluded_pairs(df, "Today [0]")
exclude_3b_ids = get_excluded_pairs(df, "Yesterday [1]")

query_3_1a = general_proximity_pairs(df, "Today [0]", exclude_3a_ids)
query_3_1b = general_proximity_pairs(df, "Yesterday [1]", exclude_3b_ids)

query_2_1a = trio_matches(df)

# --- Display Section ---
def display_matches(title, results):
    st.subheader(f"{title} — {len(results)} matches")
    for i, match in enumerate(sorted(results, key=lambda x: x['Output'], reverse=True), 1):
        with st.expander(f"{match['Summary']}"):
            st.write(pd.DataFrame([match]).T)
    if results:
        df_export = pd.DataFrame(results)
        st.download_button(f"Download {title} as CSV", df_export.to_csv(index=False), file_name=f"{title.replace(' ', '_')}.csv", mime="text/csv")

# --- Outputs ---
display_matches("Query 1.1a - Today 1→0 Matches", query_1_1a)
display_matches("Query 1.1b - Yesterday 1→0 Matches", query_1_1b)
display_matches("Query 2.1a - Trios (Today)", query_2_1a)
display_matches("Query 3.1a - Today 0→0 Non-1 Matches", query_3_1a)
display_matches("Query 3.1b - Yesterday 0→0 Non-1 Matches", query_3_1b)
