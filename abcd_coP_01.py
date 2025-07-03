import streamlit as st
import pandas as pd
from datetime import datetime

# 🔹 Load your CSV
uploaded_file = st.file_uploader("Drop a CSV file here", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["Arrival"])
    # Continue with the detection/report logic...
else:
    st.warning("Please upload a CSV file to begin.")


report_time = pd.to_datetime(df["Arrival"].max())

# 🔹 Feed Icon Conversion
def feed_icon(feed):
    return "👶" if "sm" in feed else "🧔"

# 🔹 Score Interpretation
def interpret_score(score):
    return "high" if score >= 7 else "medium" if score >= 4 else "low"

# 🔹 Detect descending sequences at output
def find_descending_sequences(subset):
    sequences = []
    rows = subset[["Feed", "Arrival", "M #", "Origin", "Output"]].sort_values("Arrival")
    ms = rows["M #"].tolist()
    for i in range(len(ms) - 2):
        triplet = ms[i:i+3]
        if all(isinstance(m, (int, float)) for m in triplet):
            if abs(triplet[0]) > abs(triplet[1]) > abs(triplet[2]):
                sequences.append(rows.iloc[i:i+3])
    return sequences

# 🔹 A1 Detection Logic
def detect_A1(df):
    results = []
    strength_Ms = {0, 40, -40, 54, -54}
    anchors = {"Saturn", "Jupiter", "Kepler-62f", "Kepler-442b"}
    epics = {"Trinidad", "Tobago", "WASP-12b", "Macedonia"}
    today_mask = df["Day"] == "Today [0]"
    df_today = df[today_mask & df["Arrival"].between("2025-06-25 18:00", "2025-06-25 23:59")]

    for output in df["Output"].unique():
        subset = df[df["Output"] == output]
        if subset.shape[0] < 3:
            continue

        today_arrivals = df_today[df_today["Output"] == output]
        if today_arrivals.empty:
            continue

        score = 0
        present_strength = [m for m in subset["M #"] if m in strength_Ms]
        score += len(present_strength)

        if any(o in anchors for o in today_arrivals["Origin"]):
            score += 2
        if any(o in epics for o in today_arrivals["Origin"]):
            score += 3
        if any(t == datetime(2025, 6, 25, 18, 0) for t in today_arrivals["Arrival"]):
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

# 🔹 Merge Rows for Display
def merge_sequence(seq):
    merged = []
    seen_times = {}
    for idx, row in seq.iterrows():
        key = (row["Arrival"], row["M #"])
        if key in seen_times:
            merged[seen_times[key]]["Origin"] += f", {row['Origin']}"
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
            seen_times[key] = len(merged) - 1
    return pd.DataFrame(merged)

# 🔹 Display Logic
st.title("Position A1 – Possible Anchor Zones")

a1_results = detect_A1(df)
st.subheader(f"A1 – {len(a1_results)} results")

for res in a1_results:
    hours_ago = (report_time - res["timestamp"]).total_seconds() / 3600
    score_label = interpret_score(res["score"])
    summaries = []
    for seq in res["sequences"]:
        m_path = " → ".join([f"|{row['M #']}|" for _, row in seq.iterrows()])
        icons = "".join([feed_icon(row["Feed"]) for _, row in seq.iterrows()])
        summaries.append(f"{m_path} Cross [{icons}]")

    summary_line = f"• Scores {score_label}, {int(hours_ago)} hours ago, at {res['timestamp'].date()}, at {res['output']}, " \
                   f"{len(res['sequences'])}x {len(res['sequences'][0])} descending: " + " and ".join(summaries)

    if st.button(summary_line):
        for seq in res["sequences"]:
            st.write(f"Detail for Output {res['output']}:")
            st.table(merge_sequence(seq))

