import streamlit as st
import pandas as pd
from itertools import combinations

st.set_page_config(layout="wide")
st.title("Proximity & Trio Match Analyzer v4. q1→3")

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

def query_3_1_pairs(df, day_filter):
    results = []
    target_ones = df[(df['M Name'] == 1.0) & (df['Day'] == day_filter)]
    for idx, one in target_ones.iterrows():
        matches = df[
            (df['Output'] == one['Output']) &
            (df['Arrival'] < one['Arrival']) &
            (df.index != idx)
        ]
        for m_idx, match in matches.iterrows():
            if match['M Name'] in [1.0]:
                continue
            if (800 <= match['Origin'] <= 1300) or (800 <= one['Origin'] <= 1300):
                results.append({
                    'Summary': f"At {one['Arrival']} {match['M Name']:.3f} to {one['M Name']:.3f} @ {one['Output']:.3f}",
                    'Newest Arrival': one['Arrival'],
                    'Older Arrival': match['Arrival'],
                    'M Newer': one['M Name'],
                    'M Older': match['M Name'],
                    'Output': one['Output'],
                    'Origin New': one['Origin'],
                    'Origin Old': match['Origin'],
                    'Day': one['Day']
                })
    return results

def get_used_pair_ids(*queries):
    ids = set()
    for q in queries:
        for res in q:
            newer = res['Newest Arrival']
            older = res['Older Arrival']
            ids.add(tuple(sorted([newer, older])))
    return ids

def query_3_2_pairs(df, day_filter, exclude_ids):
    results = []
    rows = df[df['Day'] == day_filter]
    for idx, row in rows.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['Arrival'] < row['Arrival']) &
            (df.index != idx)
        ]
        for m_idx, match in matches.iterrows():
            pair_ids = tuple(sorted([row['Arrival'], match['Arrival']]))
            if pair_ids in exclude_ids:
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

def query_trios(df, day_filter):
    results = []
    grouped = df.groupby('Output')
    for output_val, group in grouped:
        if len(group) < 3:
            continue
        group_sorted = group.sort_values('Arrival')
        for i in range(len(group_sorted) - 2):
            trio = group_sorted.iloc[i:i+3]
            if trio.iloc[2]['Day'] != day_filter:
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
                'Summary': f"At {trio.iloc[2]['Arrival']} {m_actual[0]:.3f} to {m_actual[1]:.3f} to {m_actual[2]:.3f} @ {output_val:.3f} ({direction})",
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

# --- Execute Queries ---
query_1_1a = query_1_pairs(df, "Today [0]")
query_1_1b = query_1_pairs(df, "Yesterday [1]")

query_3_1a = query_3_1_pairs(df, "Today [0]")
query_3_1b = query_3_1_pairs(df, "Yesterday [1]")

used_ids_a = get_used_pair_ids(query_1_1a, query_3_1a)
used_ids_b = get_used_pair_ids(query_1_1b, query_3_1b)

query_3_2a = query_3_2_pairs(df, "Today [0]", used_ids_a)
query_3_2b = query_3_2_pairs(df, "Yesterday [1]", used_ids_b)

query_2_1a = query_trios(df, "Today [0]")
query_2_1b = query_trios(df, "Yesterday [1]")

# --- Display ---
def display_results(title, results):
    st.subheader(f"{title} — {len(results)} pairs" if 'Trio' not in title else f"{title} — {len(results)} trios")
    for i, r in enumerate(results):
        with st.expander(r['Summary']):
            st.write(pd.DataFrame([r]).T)
    if results:
        df_export = pd.DataFrame(results)
        st.download_button(f"Download {title} as CSV", df_export.to_csv(index=False), file_name=f"{title.replace(' ', '_')}.csv", mime="text/csv")

# --- Output ---
display_results("Query 1.1a - Today 1→0 Pairs", query_1_1a)
display_results("Query 1.1b - Yesterday 1→0 Pairs", query_1_1b)
display_results("Query 2.1a - Trios (Today)", query_2_1a)
display_results("Query 2.1b - Trios (Yesterday)", query_2_1b)
display_results("Query 3.1a - Today #→1 Pairs", query_3_1a)
display_results("Query 3.1b - Yesterday #→1 Pairs", query_3_1b)
display_results("Query 3.2a - Today #→# Non-query 1.1 or 3.1 Pairs", query_3_2a)
display_results("Query 3.2b - Yesterday #→# Non-query 1.1 or 3.1 Pairs", query_3_2b)
