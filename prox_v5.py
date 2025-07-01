import streamlit as st
import pandas as pd
from itertools import combinations

st.set_page_config(layout="wide")
st.title("Proximity & Trio Pair Analyzer")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if not uploaded_file:
    st.stop()

df_raw = pd.read_csv(uploaded_file)

# --- Safe Conversion ---
df = df_raw.copy()
df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
df['Day'] = df['Day'].astype(str)

# --- Row Filtering & Reporting ---
initial_count = len(df)
df.dropna(subset=['Arrival', 'M Name', 'Output'], inplace=True)
cleaned_count = len(df)
removed_count = initial_count - cleaned_count

if removed_count > 0:
    st.info(f"{removed_count:,} rows removed due to invalid Arrival, M Name, or Output values.")

# --- Query Functions ---
def format_output(val):
    return f"{val:,.3f}"

def pair_1_to_0(df, day_filter):
    results = []
    target_rows = df[(df['M Name'] == 0) & (df['Day'] == day_filter)]
    for idx, row in target_rows.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['M Name'].isin([1, -1])) &
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
                    'Output': row['Output'],
                    'Origin New': row['Origin'],
                    'Origin Old': match['Origin'],
                    'Day': row['Day']
                })
    return results

def pair_any_to_1(df, day_filter):
    results = []
    target_rows = df[(df['M Name'] == 1) & (df['Day'] == day_filter)]
    for idx, row in target_rows.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['M Name'] != 1) &
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
                    'Output': row['Output'],
                    'Origin New': row['Origin'],
                    'Origin Old': match['Origin'],
                    'Day': row['Day']
                })
    return results

def pair_remaining(df, day_filter, exclude_ids):
    results = []
    rows = df[df['Day'] == day_filter]
    for idx, row in rows.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['Arrival'] < row['Arrival']) &
            (df.index != idx)
        ]
        for m_idx, match in matches.iterrows():
            pair_id = tuple(sorted([idx, m_idx]))
            if pair_id in exclude_ids:
                continue
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append({
                    'Row New': idx,
                    'Row Old': m_idx,
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

def get_exclusion_ids(results):
    return set(tuple(sorted([r['Row New'], r['Row Old']])) for r in results)

def find_trios(df, day_filter):
    trios = []
    grouped = df[df['Day'] == day_filter].groupby('Output')
    for output, group in grouped:
        sorted_rows = group.sort_values('Arrival')
        if len(sorted_rows) < 3:
            continue
        for combo in combinations(sorted_rows.index, 3):
            trio_df = sorted_rows.loc[list(combo)].sort_values('Arrival')
            m_vals_abs = trio_df['M Name'].abs().tolist()
            m_vals_actual = trio_df['M Name'].tolist()
            if m_vals_abs[0] > m_vals_abs[1] > m_vals_abs[2]:
                kind = "Descending Trio"
            elif m_vals_abs[0] < m_vals_abs[1] < m_vals_abs[2]:
                kind = "Ascending Trio"
            else:
                continue
            if not trio_df['Origin'].between(800, 1300).any():
                continue
            trios.append({
                'Summary': f"At {trio_df.iloc[-1]['Arrival'].strftime('%-m/%-d/%Y %H:%M')} "
                           f"{m_vals_actual[0]:.3f} to {m_vals_actual[1]:.3f} to {m_vals_actual[2]:.3f} "
                           f"@ {format_output(output)} ({kind})",
                'Type': kind,
                'Output': output,
                'Rows': trio_df.index.tolist(),
                'Arrivals': trio_df['Arrival'].tolist(),
                'M Names': m_vals_actual,
                'Origins': trio_df['Origin'].tolist()
            })
    return sorted(trios, key=lambda x: x['Output'], reverse=True)

