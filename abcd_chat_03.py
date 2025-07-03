import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- Constants ---
ANCHOR_ORIGINS = ["Saturn", "Jupiter", "Kepler-62f", "Kepler-442b"]
EPIC_ORIGINS = ["Trinidad", "Tobago", "WASP-12b", "Macedonia"]
STRENGTH_NUMBERS = [0, 40, -40, 54, -54]

# --- Helper Functions ---
def is_strength(m): return m in STRENGTH_NUMBERS

def get_feed_icon(feed):
    if 'sm' in feed:
        return '👶'
    elif 'Bg' in feed:
        return '🧔'
    else:
        return '❓'

def label_today_rows(df, report_time):
    df = df.copy()
    df['Day_Label'] = df['Arrival'].apply(
        lambda x: 'Today' if x.date() == report_time.date() else 'Other'
    )
    return df

def sort_sequences(df):
    df_sorted = df.copy()
    df_sorted['Abs M'] = df_sorted['M #'].abs()
    return df_sorted.sort_values(by='Abs M', ascending=False)

def find_descending_sequences(df, output_col, report_time):
    sequences = []
    df_today = df[df['Arrival'] <= report_time]
    grouped = df_today.groupby(output_col)

    for output, group in grouped:
        group_sorted = group.sort_values(by='Arrival')
        group_sorted = sort_sequences(group_sorted)

        for polarity in ['positive', 'negative']:
            if polarity == 'positive':
                subset = group_sorted[group_sorted['M #'] > 0]
            else:
                subset = group_sorted[group_sorted['M #'] < 0]

            for i in range(len(subset) - 2):
                trio = subset.iloc[i:i+3]
                if len(trio) < 3:
                    continue
                arrival_set = set(trio['Arrival'].dt.date)
                if len(arrival_set & {report_time.date()}) < 2:
                    continue
                if not any(origin in ANCHOR_ORIGINS + EPIC_ORIGINS for origin in trio['Origin']):
                    continue
                feeds = trio['Feed'].unique()
                trio_sorted = sort_sequences(trio)
                sequence = {
                    'Output': output,
                    'Rows': trio_sorted,
                    'Feeds': feeds,
                    'Strengths': [m for m in trio_sorted['M #'] if is_strength(m)],
                    'Type': f"{len(trio)} Descending",
                    'Feed_Icons': [get_feed_icon(f) for f in feeds]
                }
                sequences.append(sequence)
    return sequences

def merge_duplicate_sequences(sequences):
    unique_sequences = []
    seen_keys = set()

    for seq in sequences:
        key = (
            seq['Output'],
            tuple(sorted(seq['Rows']['M #'].abs())),
            tuple(seq['Rows']['Arrival'].round('min'))
        )
        if key not in seen_keys:
            unique_sequences.append(seq)
            seen_keys.add(key)
    return unique_sequences

# --- Streamlit UI ---
st.title("🔎 Position A1 Detector")
uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=['Arrival'])

    if 'Row' not in df.columns:
        df['Row'] = df.index  # fallback

    report_time = df['Arrival'].max()
    df = label_today_rows(df, report_time)

    st.markdown(f"**Report Time:** {report_time.strftime('%Y-%m-%d %H:%M')}")
    sequences = find_descending_sequences(df, 'Output', report_time)
    sequences = merge_duplicate_sequences(sequences)

    if not sequences:
        st.info("No A1 sequences found.")
    else:
        st.markdown(f"### A1 – {len(sequences)} result{'s' if len(sequences)!=1 else ''}")
        for i, seq in enumerate(sequences):
            dt = seq['Rows']['Arrival'].max()
            hours_ago = (report_time - dt).total_seconds() / 3600
            m_list = list(seq['Rows']['M #'])
            m_str = " → ".join(f"|{m}|" for m in m_list)
            icons = "→".join(seq['Feed_Icons'])
            summary = (
                f"Scores {'high' if len(seq['Strengths']) >= 2 else 'low'}, "
                f"{int(hours_ago)} hours ago, "
                f"at {dt.strftime('%Y-%m-%d %H:%M')}, "
                f"at {seq['Output']}, "
                f"{1}x {seq['Type']}: {m_str} Cross [{icons}]"
            )

            with st.expander(summary):
                st.dataframe(
                    seq['Rows'][['Feed', 'Row', 'Arrival', 'M #', 'Origin', 'Output']].assign(
                        Type=seq['Type']
                    ),
                    hide_index=True
                )
