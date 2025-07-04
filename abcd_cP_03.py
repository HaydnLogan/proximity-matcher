import streamlit as st
import pandas as pd
from datetime import datetime

# 🔹 Title & File Upload
st.title("🅰️ Position A1 Detector – Anchor Zone Scanner")
uploaded_file = st.file_uploader("📤 Upload your report. cP v03", type="csv")

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

    # 🔹 Allow all Today arrivals, but highlight if within 18:00–24:00
    df_today = df[df["Day"] == "Today [0]"]
    for output in df["Output"].unique():
        subset = df[df["Output"] == output]
        if subset.shape[0] < 3:
            continue

        today_arrivals = df_today[df_today["Output"] == output]
        if today_arrivals.empty:
            continue

        # 🔍 Diagnostic info to trace activity
        st.write(f"🧪 Checking Output: {output}")
        st.write(f"Total Travelers: {subset.shape[0]}, Today Travelers: {today_arrivals.shape[0]}")

        score = 0

        # 🔹 Strength Traveler Presence
        ms_present = [m for m in subset["M #"] if m in strength_Ms]
        st.write(f"Strength Travelers Found: {ms_present}")
        score += len(ms_present)

        # 🔹 Anchor & EPIC Origin Boosts
        origins_today = set(today_arrivals["Origin"])
        if origins_today & anchors:
            score += 2
            st.write(f"Anchor Origins Present: {origins_today & anchors}")
        if origins_today & epics:
            score += 3
            st.write(f"EPIC Origins Present: {origins_today & epics}")

        # 🔹 Precise Time Anchor
        if any(arr.hour == 18 for arr in today_arrivals["Arrival"]):
            score += 1
            st.write("💫 Arrival at start of Traveler Day (18:00) detected.")

        # 🔹 Sequence Search
        sequences = find_descending_sequences(subset)
        if sequences:
            st.write(f"✅ {len(sequences)} Descending Sequence(s) Found")
            result = {
                "output": output,
                "score": score,
                "sequences": sequences,
                "feeds": subset["Feed"].nunique(),
                "timestamp": today_arrivals.iloc[0]["Arrival"]
            }
            results.append(result)
        else:
            st.write("🔸 No qualifying descending sequences at this output.")

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
