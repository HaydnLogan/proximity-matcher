import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="A1 Position Detector v3b", layout="wide")

# -------------------- FUNCTIONS --------------------

def label_today_rows(df, report_time):
    df = df.copy()

    def label_fn(x):
        try:
            x_parsed = pd.to_datetime(x)
            if x_parsed.date() == report_time.date():
                return 'Today'
            else:
                return 'Other'
        except Exception:
            return 'Other'

    df['Day_Label'] = df['Arrival'].apply(label_fn)
    return df

def is_descending(m_numbers):
    return all(abs(m_numbers[i]) > abs(m_numbers[i + 1]) for i in range(len(m_numbers) - 1))

def score_a1_group(group_df, report_time):
    # Basic scoring logic — placeholder: can be made more advanced later
    hours_ago = (report_time - group_df['Arrival'].max()).total_seconds() / 3600
    if hours_ago < 6:
        return 'Scores high'
    elif hours_ago < 12:
        return 'Scores medium'
    else:
        return 'Scores low'

def find_a1_positions(df, report_time):
    results = []
    grouped = df[df['Day_Label'] == 'Today'].groupby('Output')

    for output, group in grouped:
        output_df = df[df['Output'] == output].sort_values(by='Arrival')
        candidates = []

        for i in range(len(output_df) - 2):
            trio = output_df.iloc[i:i+3]
            m_numbers = trio['M #'].tolist()
            arrival_times = trio['Arrival'].tolist()
            day_labels = trio['Day_Label'].tolist()

            if is_descending(m_numbers):
                feed_set = [f for f in trio['Feed']]
                icon_seq = ''.join(['👶' if 'sm' in f else '🧔' for f in feed_set])

                row_key = tuple((round(a.timestamp()), m) for a, m in zip(arrival_times, m_numbers))

                candidates.append({
                    "Output": output,
                    "Trio": trio.copy(),
                    "Type": f"{len(trio)} Descending",
                    "Icon_Seq": icon_seq,
                    "Key": row_key
                })

        # Deduplicate based on M # sequence and arrival
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c["Key"] not in seen:
                seen.add(c["Key"])
                unique_candidates.append(c)

        if unique_candidates:
            score = score_a1_group(group, report_time)
            result = {
                "Output": output,
                "Trio_List": unique_candidates,
                "Score": score,
                "Time": output_df['Arrival'].max(),
            }
            results.append(result)

    return results

def merge_same_arrival_origins(trio_df):
    trio_df = trio_df.copy()
    merged_rows = []
    seen = {}

    for _, row in trio_df.iterrows():
        key = (row['Arrival'], row['M #'])
        if key not in seen:
            seen[key] = row.copy()
        else:
            seen[key]['Origin'] += f", {row['Origin']}"

    return pd.DataFrame(seen.values())

# -------------------- STREAMLIT UI --------------------

st.title("🧭 A1 Position Detector")
st.markdown("Upload a CSV and detect Position A1 patterns across Outputs.")

uploaded_file = st.file_uploader("Upload your CSV. cG v03b", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # Ensure correct dtypes
    df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')

    st.success("CSV loaded successfully!")

    # Automatically extract report time from file name or user input
    default_report_time = datetime.now()
    report_time = st.date_input("Report date", default_report_time.date())
    report_hour = st.time_input("Report hour", default_report_time.time())
    report_time = datetime.combine(report_time, report_hour)

    df = label_today_rows(df, report_time)

    st.markdown("### 🔍 Detecting A1 Patterns...")

    a1_results = find_a1_positions(df, report_time)

    st.markdown(f"### 🅰️ A1 – {len(a1_results)} result{'s' if len(a1_results) != 1 else ''}")

    for i, result in enumerate(a1_results):
        output = result['Output']
        score = result['Score']
        time_str = result['Time'].strftime("%Y-%m-%d %H:%M")
        hours_ago = int((report_time - result['Time']).total_seconds() / 3600)
        feed_count = len(set(row['Feed'] for trio in result['Trio_List'] for _, row in trio['Trio'].iterrows()))

        seq_descriptions = []
        for trio_data in result['Trio_List']:
            m_numbers = trio_data['Trio']['M #'].tolist()
            icon_seq = trio_data['Icon_Seq']
            seq_desc = " → ".join(f"|{int(m)}|" for m in m_numbers)
            seq_descriptions.append(f"{seq_desc} Cross [{icon_seq}]")

        all_sequences = " and ".join(seq_descriptions)
        summary = f"{score}, {hours_ago} hours ago, at {time_str}, at {output}, {len(result['Trio_List'])}x {trio_data['Type']}: {all_sequences}"

        with st.expander(summary):
            for trio_data in result['Trio_List']:
                cleaned = merge_same_arrival_origins(trio_data['Trio'])
                cleaned = cleaned[['Feed', 'Row', 'Arrival', 'M #', 'Origin', 'Output']].copy()
                cleaned['Type'] = trio_data['Type']
                st.dataframe(cleaned, use_container_width=True)

