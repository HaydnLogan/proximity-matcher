import streamlit as st
import pandas as pd
from datetime import datetime

# 🔹 Title & File Upload
st.title("🅰️ Position A1 Detector – Anchor Zone Scanner")
uploaded_file = st.file_uploader("📤 Upload your report. cp v02", type="csv")

if uploaded_file:
    # 🔹 Read and parse datetime
    df = pd.read_csv(uploaded_file)
    df["Arrival"] = pd.to_datetime(df["Arrival"], errors="coerce")

    # 🔹 Validate required columns
    required_cols = {"Arrival", "Day", "Origin", "M #", "Feed", "Output"}
    if not required_cols.issubset(df.columns):
        st.error("❌ CSV is missing required columns. Expected: " + ", ".join(required_cols))
        st.stop()

    if df["Arrival"].isnull().any():
        st.warning("⚠️ Some Arrival values couldn't be parsed as timestamps. They will be skipped.")

    # 🔹 Dynamic Report Time
    report_time = pd.to_datetime(df["Arrival"].max()).round("H")
    st.success(f"📅 Detected Report Time: {report_time.strftime('%Y-%m-%d %H:%M')}")

    # 🔹 Helper Functions
    def feed_icon(feed):
        return "👶" if "sm" in feed else "🧔"

    def interpret_score(score):
        return "high" if score >= 7 else "medium" if score >= 4 else "low"

    def find_descending_sequences(subset):
        sequences = []
        rows = subset[["Feed", "Arrival", "M #", "Origin", "Output"]].sort_values("Arrival")
        ms = rows["M #"].tolist()
        for i in range(len(ms) - 2):
            trio = ms[i:i+3]
            if all(isinstance(m, (int, float)) for m in trio):
                if abs(trio[0]) > abs(trio[1]) > abs(trio[2]):
                    sequences.append(rows.iloc[i:i+3])
        return sequences

    def merge_sequence(seq):
        merged = []
        seen = {}
        for idx, row in seq.iterrows():
            key = (row["Arrival"], row["M #"])
            if key in seen:
                merged[seen[key]]["Origin"] += f", {row['Origin']}"
            else:
                merged.append({
                    "Feed": row["Feed"],
                    "Row": idx,
                    "Arrival": row["Arrival"],
                    "M #": row["M #"],
                    "Origin": row["Origin"],
                    "Output": row["Output"],
                    "Type": f"{len(seq)} Descending"
                })
                seen[key] = len(merged) - 1
        return pd.DataFrame(merged)

    # 🔹 Position A1 Detection Logic
    def detect_A1(df, report_time):
        strength_Ms = {0, 40, -40, 54, -54}
        anchors = {"Saturn", "Jupiter", "Kepler-62f", "Kepler-442b"}
        epics = {"Trinidad", "Tobago", "WASP-12b", "Macedonia"}
        results = []

        today_start = report_time.replace(hour=18, minute=0)
        today_end = report_time.replace(hour=23, minute=59)
        df_today = df[(df["Day"] == "Today [0]") & df["Arrival"].between(today_start, today_end)]

        for output in df["Output"].unique():
            subset = df[df["Output"] == output]
            if subset.shape[0] < 3:
                continue

            today_arrivals = df_today[df_today["Output"] == output]
            if today_arrivals.empty:
                continue

            score = 0
            ms_present = [m for m in subset["M #"] if m in strength_Ms]
            score += len(ms_present)

            if any(origin in anchors for origin in today_arrivals["Origin"]):
                score += 2
            if any(origin in epics for origin in today_arrivals["Origin"]):
                score += 3
            if any(arr == today_start for arr in today_arrivals["Arrival"]):
                score += 1

            sequences = find_descending_sequences(subset)
            if sequences:
                result = {
                    "output": output,
                    "score": score,
                    "sequences": sequences,
                    "feeds": subset["Feed"].nunique(),
                    "timestamp": today_arrivals.iloc[0]["Arrival"]
                }
                results.append(result)

        return results

    # 🔹 Run Detection and Display Results
    a1_results = detect_A1(df, report_time)
    st.subheader(f"A1 – {len(a1_results)} result{'s' if len(a1_results)!=1 else ''}")

    for res in a1_results:
        hours_ago = (report_time - res["timestamp"]).total_seconds() / 3600
        score_label = interpret_score(res["score"])
        summaries = []
        for seq in res["sequences"]:
            m_path = " → ".join([f"|{row['M #']}|" for _, row in seq.iterrows()])
            icons = "".join([feed_icon(row["Feed"]) for _, row in seq.iterrows()])
            summaries.append(f"{m_path} Cross [{icons}]")

        summary_line = f"• Scores {score_label}, {int(hours_ago)} hours ago, at {res['timestamp'].strftime('%Y-%m-%d %H:%M')}, at {res['output']}, " \
                       f"{len(res['sequences'])}x {len(res['sequences'][0])} descending: " + " and ".join(summaries)

        if st.button(summary_line):
            for seq in res["sequences"]:
                st.markdown(f"#### Detail for Output {res['output']}")
                st.table(merge_sequence(seq))

else:
    st.info("☝️ Upload your CSV to begin scanning for Position A1 patterns.")
