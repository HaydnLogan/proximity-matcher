import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Proximity Match Analyzer - Query 3.1 Only")

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

df = df.dropna(subset=['Arrival', 'Output'])

# --- Query 3.1a/b: #→±1 where one has Origin 800–1300 and newest row is Today or Yesterday ---
def query_3_1_pairs(df, day_filter):
    results = []
    targets = df[(df['M Name'].isin([1.0, -1.0])) & (df['Day'] == day_filter)]
    for idx, target in targets.iterrows():
        potential_matches = df[
            (df['Output'] == target['Output']) &
            (df['Arrival'] < target['Arrival']) &
            (df.index != idx)
        ]
        for m_idx, match in potential_matches.iterrows():
            if match['M Name'] in [1.0, -1.0]:
                continue
            if (800 <= match['Origin'] <= 1300) or (800 <= target['Origin'] <= 1300):
                results.append({
                    'Newest Arrival': target['Arrival'],
                    'Older Arrival': match['Arrival'],
                    'M Newer': target['M Name'],
                    'M Older': match['M Name'],
                    'Output': target['Output'],
                    'Origin New': target['Origin'],
                    'Origin Old': match['Origin'],
                    'Day New': target['Day'],
                    'Day Old': match['Day'],
                    'Row New': idx,
                    'Row Old': m_idx,
                    'Summary': f"At {target['Arrival']} {match['M Name']:.3f} → {target['M Name']:.3f} @ {target['Output']:.3f}"
                })
    return results

def display_pairs(title, results):
    st.subheader(f"{title} — {len(results)} pair{'s' if len(results) != 1 else ''}")
    for i, r in enumerate(results):
        with st.expander(f"{i+1}. {r['Summary']}"):
            detail_df = pd.DataFrame([
                {
                    "Row": r['Row Old'],
                    "Arrival": r['Older Arrival'],
                    "M Name": r['M Older'],
                    "Origin": r['Origin Old'],
                    "Day": r['Day Old']
                },
                {
                    "Row": r['Row New'],
                    "Arrival": r['Newest Arrival'],
                    "M Name": r['M Newer'],
                    "Origin": r['Origin New'],
                    "Day": r['Day New']
                }
            ])[["Row", "Arrival", "M Name", "Origin", "Day"]]  # enforce column order
            st.dataframe(detail_df, use_container_width=True)

# --- Run and Display ---
query_3_1a = query_3_1_pairs(df, "Today [0]")
query_3_1b = query_3_1_pairs(df, "Yesterday [1]")

display_pairs("Query 3.1a - Today #→±1", query_3_1a)
display_pairs("Query 3.1b - Yesterday #→±1", query_3_1b)
