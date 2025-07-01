import streamlit as st
import pandas as pd
from itertools import combinations

st.set_page_config(layout="wide")
st.title("Proximity & Trio Match Analyzer")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if not uploaded_file:
    st.stop()

df = pd.read_csv(uploaded_file)

# Convert types safely
df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
df['Day'] = df['Day'].astype(str)

# Drop invalid rows
initial_len = len(df)
df = df.dropna(subset=['Arrival', 'Output'])
removed_rows = initial_len - len(df)
if removed_rows > 0:
    st.warning(f"{removed_rows} rows removed due to invalid Arrival or Output values.")

# ---------- Query Functions ----------
def proximity_pairs(df, day_filter):
    results = []
    for idx, row in df[(df['M Name'] == 0) & (df['Day'] == day_filter)].iterrows():
        candidates = df[(df['Output'] == row['Output']) & (df['M Name'].isin([1, -1])) & (df['Arrival'] < row['Arrival'])]
        for c_idx, match in candidates.iterrows():
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append({
                    'Summary': f"At {row['Arrival']} {match['M Name']:.3f} to {row['M Name']:.3f} @ {row['Output']:,.3f}",
                    'Row New': idx,
                    'Row Old': c_idx,
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

def query_3_1_pairs(df, day_filter):
    results = []
    df_day = df[df['Day'] == day_filter]
    ones = df_day[df_day['M Name'] == 1.0]
    for idx, one_row in ones.iterrows():
        pre_arrivals = df_day[(df_day['Arrival'] < one_row['Arrival']) & (df_day.index != idx)]
        for other_idx, other in pre_arrivals.iterrows():
            if (800 <= one_row['Origin'] <= 1300) or (800 <= other['Origin'] <= 1300):
                results.append({
                    'Summary': f"At {one_row['Arrival']} {other['M Name']:.3f} to {one_row['M Name']:.3f} @ {one_row['Output']:,.3f}",
                    'Row New': idx,
                    'Row Old': other_idx,
                    'Newest Arrival': one_row['Arrival'],
                    'Older Arrival': other['Arrival'],
                    'M Newer': one_row['M Name'],
                    'M Older': other['M Name'],
                    'Output': one_row['Output'],
                    'Origin New': one_row['Origin'],
                    'Origin Old': other['Origin'],
                    'Day': one_row['Day']
                })
    return results

def query_3_2_pairs(df, day_filter, exclude_ids):
    results = []
    df_day = df[df['Day'] == day_filter]
    for idx, row in df_day.iterrows():
        for c_idx, candidate in df_day.iterrows():
            if idx == c_idx or (candidate['Arrival'] >= row['Arrival']):
                continue
            if (row['Output'] != candidate['Output']) or ((idx, c_idx) in exclude_ids) or ((c_idx, idx) in exclude_ids):
                continue
            if {row['M Name'], candidate['M Name']} == {0.0, 1.0}:
                continue
            if row['M Name'] == 1.0 or candidate['M Name'] == 1.0:
                continue
            if (800 <= row['Origin'] <= 1300) or (800 <= candidate['Origin'] <= 1300):
                results.append({
                    'Summary': f"At {row['Arrival']} {candidate['M Name']:.3f} to {row['M Name']:.3f} @ {row['Output']:,.3f}",
                    'Row New': idx,
                    'Row Old': c_idx,
                    'Newest Arrival': row['Arrival'],
                    'Older Arrival': candidate['Arrival'],
                    'M Newer': row['M Name'],
                    'M Older': candidate['M Name'],
                    'Output': row['Output'],
                    'Origin New': row['Origin'],
                    'Origin Old': candidate['Origin'],
                    'Day': row['Day']
                })
    return results

def trio_matches(df, day_filter):
    results = []
    df_day = df[df['Day'] == day_filter]
    for output, group in df_day.groupby('Output'):
        group = group.sort_values('Arrival')
        if len(group) < 3:
            continue
        for i in range(len(group) - 2):
            trio = group.iloc[i:i+3]
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
                'Summary': f"At {trio.iloc[2]['Arrival']} {m_actual[0]:.3f} to {m_actual[1]:.3f} to {m_actual[2]:.3f} @ {output:,.3f} ({direction})",
                'Type': direction,
                'Rows': trio.index.tolist(),
                'Arrivals': trio['Arrival'].tolist(),
                'M Names': trio['M Name'].tolist(),
                'Origins': origins,
                'Output': output
            })
    return results

# ---------- Query Execution ----------
query_1_1a = proximity_pairs(df, "Today [0]")
query_1_1b = proximity_pairs(df, "Yesterday [1]")

query_3_1a = query_3_1_pairs(df, "Today [0]")
query_3_1b = query_3_1_pairs(df, "Yesterday [1]")

# Build set of existing pair IDs for 3.2 exclusion
excl_ids = set()
for q in (query_1_1a + query_1_1b + query_3_1a + query_3_1b):
    excl_ids.add((q['Row New'], q['Row Old']))
    excl_ids.add((q['Row Old'], q['Row New']))

query_3_2a = query_3_2_pairs(df, "Today [0]", excl_ids)
query_3_2b = query_3_2_pairs(df, "Yesterday [1]", excl_ids)

query_2_1a = trio_matches(df, "Today [0]")
query_2_1b = trio_matches(df, "Yesterday [1]")

# ---------- Display ----------
def display_pairs(title, results):
    count = len(results)
    st.subheader(f"{title} — {count} {'pair' if count == 1 else 'pairs'}")
    for i, match in enumerate(results):
        with st.expander(match['Summary']):
            df_disp = pd.DataFrame([
                {
                    'Row': match['Row Old'],
                    'Arrival': match['Older Arrival'],
                    'M Name': match['M Older'],
                    'Origin': match['Origin Old'],
                    'Day': match['Day']
                },
                {
                    'Row': match['Row New'],
                    'Arrival': match['Newest Arrival'],
                    'M Name': match['M Newer'],
                    'Origin': match['Origin New'],
                    'Day': match['Day']
                }
            ]).reset_index(drop=True)
            st.dataframe(df_disp)

def display_trios(title, trios):
    count = len(trios)
    st.subheader(f"{title} — {count} {'trio' if count == 1 else 'trios'}")
    for trio in trios:
        with st.expander(trio['Summary']):
            df_trio = pd.DataFrame({
                'Row': trio['Rows'],
                'Arrival': trio['Arrivals'],
                'M Name': trio['M Names'],
                'Origin': trio['Origins'],
                'Output': [trio['Output']] * 3,
                'Type': [trio['Type']] * 3
            })
            df_trio.index.name = ''
            st.dataframe(df_trio)

# ---------- Output Display ----------
display_pairs("Query 1.1a - Today 1→0 Pairs", query_1_1a)
display_pairs("Query 1.1b - Yesterday 1→0 Pairs", query_1_1b)

display_trios("Query 2.1a - Trios (Today)", query_2_1a)
display_trios("Query 2.1b - Trios (Yesterday)", query_2_1b)

display_pairs("Query 3.1a - Today #→1 Pairs", query_3_1a)
display_pairs("Query 3.1b - Yesterday #→1 Pairs", query_3_1b)

display_pairs("Query 3.2a - Today #→# Non-query 1.1 or 3.1 Pairs", query_3_2a)
display_pairs("Query 3.2b - Yesterday #→# Non-query 1.1 or 3.1 Pairs", query_3_2b)
