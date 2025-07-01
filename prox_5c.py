import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Query 3.1 Checker - #→±1")

# Upload CSV
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
if not uploaded_file:
    st.stop()

# Load data
df = pd.read_csv(uploaded_file)

# Parse dates
for col in ['Arrival', 'Departure']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
df['Day'] = df['Day'].astype(str)

# Filter invalid Output
df = df[df['Output'] > 0]

# Remove rows where Output appears only once
df = df.sort_values(by='Output')
df['Prev'] = df['Output'].shift(1)
df['Next'] = df['Output'].shift(-1)
df = df[(df['Output'] == df['Prev']) | (df['Output'] == df['Next'])]
df.drop(columns=['Prev', 'Next'], inplace=True)

# Drop rows with missing Arrival or Output
df.dropna(subset=['Arrival', 'Output'], inplace=True)

# --- Query 3.1 Logic ---
def run_query_3_1(df, day_filter, title):
    results = []
    df_today = df[df['Day'] == day_filter]
    for i, newer in df_today.iterrows():
        for j, older in df[(df['Arrival'] < newer['Arrival']) & (df['Output'] == newer['Output'])].iterrows():
            # one must be ±1.0, one must not
            m1, m2 = newer['M Name'], older['M Name']
            if ({abs(m1), abs(m2)} == {1, abs(m2)} or {abs(m1), abs(m2)} == {abs(m1), 1}) and (m1 != m2):
                if (800 <= newer['Origin'] <= 1300) or (800 <= older['Origin'] <= 1300):
                    results.append({
                        'Row New': i,
                        'Row Old': j,
                        'Arrival New': newer['Arrival'],
                        'Arrival Old': older['Arrival'],
                        'M Newer': m1,
                        'M Older': m2,
                        'Origin New': newer['Origin'],
                        'Origin Old': older['Origin'],
                        'Output': newer['Output'],
                        'Day New': newer['Day'],
                        'Day Old': older['Day']
                    })
    return results

# Run Query 3.1a and 3.1b
results_3_1a = run_query_3_1(df, "Today [0]", "Query 3.1a - Today #→±1")
results_3_1b = run_query_3_1(df, "Yesterday [1]", "Query 3.1b - Yesterday #→±1")

# Display results
def display_pairs(title, results):
    label = "pair" if len(results) == 1 else "pairs"
    st.subheader(f"{title} — {len(results)} {label}")
    for res in results[::-1]:
        summary = f"{res['M Older']:.3f} to {res['M Newer']:.3f} @ {res['Output']:,.3f} — {res['Arrival New']}"
        with st.expander(summary):
            st.write(pd.DataFrame([
                [res['Row Old'], res['Arrival Old'], res['M Older'], res['Origin Old'], res['Day Old']],
                [res['Row New'], res['Arrival New'], res['M Newer'], res['Origin New'], res['Day New']],
            ], columns=["Row", "Arrival", "M Name", "Origin", "Day"]))

display_pairs("Query 3.1a - Today #→±1", results_3_1a)
display_pairs("Query 3.1b - Yesterday #→±1", results_3_1b)
