import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Position A Model - A1 Detector")

uploaded_file = st.file_uploader("Upload your CSV", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')
    df['Departure'] = pd.to_datetime(df['Departure'], errors='coerce')
    df = df[df['Arrival'].notna() & df['Departure'].notna()]

    REPORT_TIME = df['Arrival'].max()

    def is_strength(m):
        return abs(m) in [0, 40, 54]

    def detect_descending_sequences(df):
        grouped = df.groupby("Output")
        results = []

        for output, group in grouped:
            group = group.sort_values("Arrival")
            travelers = group[["Feed", "Arrival", "M #", "Origin", "Output", "Row"]].copy()
            travelers["abs_m"] = travelers["M #"].abs()
            travelers["polarity"] = travelers["M #"].apply(lambda x: "pos" if x > 0 else "neg" if x < 0 else "zero")

            for i in range(len(travelers) - 2):
                seq = travelers.iloc[i:i+3]
                if seq["M #"].is_unique and all(seq["polarity"] == seq.iloc[0]["polarity"]):
                    descending = all(seq["abs_m"].values[j] > seq["abs_m"].values[j+1] for j in range(2))
                    if descending:
                        strength_present = seq["M #"].apply(is_strength).any()
                        recent_today = seq["Arrival"].apply(lambda x: (REPORT_TIME - x).total_seconds() / 3600 < 24).sum() >= 2
                        anchor_present = seq["Origin"].isin(["Saturn", "Jupiter", "Kepler-62f", "Kepler-442b"]).any()
                        if strength_present and recent_today and anchor_present:
                            results.append(seq.assign(Type="3 Descending"))
        return results

    def deduplicate(sequences):
        # Merge by identical M #s and Arrival, combine Origins
        merged = []
        seen = set()
        for seq in sequences:
            key = tuple(zip(seq["M #"], seq["Arrival"]))
            if key in seen:
                continue
            seen.add(key)
            merged.append(seq)
        return merged

    def summarize(seq_group):
        first_row = seq_group.iloc[-1]
        output = first_row["Output"]
        hours_ago = round((REPORT_TIME - first_row["Arrival"]).total_seconds() / 3600)
        datetime_str = first_row["Arrival"].strftime("%Y-%m-%d %H:%M")
        path = " → ".join(f"|{int(m)}|" for m in seq_group["M #"])
        feeds = seq_group["Feed"].apply(lambda x: "👶" if "sm" in x else "🧔")
        feed_str = "→".join(feeds)
        score = "Scores low"  # Future scoring logic can improve this
        return f"{score}, {hours_ago} hours ago, at {datetime_str}, at {output}, 1x 3 descending: {path} Cross [{feed_str}]"

    raw_results = detect_descending_sequences(df)
    deduped_results = deduplicate(raw_results)

    st.header(f"A1 – {len(deduped_results)} result{'s' if len(deduped_results) != 1 else ''}")
    for i, seq in enumerate(deduped_results):
        summary = summarize(seq)
        with st.expander(summary):
            display_df = seq[["Feed", "Row", "Arrival", "M #", "Origin", "Output", "Type"]].copy()
            display_df["Arrival"] = display_df["Arrival"].dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(display_df, use_container_width=True)
else:
    st.warning("Please upload a CSV file to begin.")
