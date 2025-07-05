import streamlit as st
import pandas as pd
from datetime import datetime

# 🔹 Title & File Upload
st.title("🅰️ Position A Models – M # 0 Confluence Tracker")
uploaded_file = st.file_uploader("📤 Upload report CSV. cP v04", type="csv")

if uploaded_file:
    # ✅ Load and parse datetime safely
    df = pd.read_csv(uploaded_file)
    df["Arrival"] = pd.to_datetime(df["Arrival"], errors="coerce")

    required = {"Arrival", "Day", "Origin", "M #", "Feed", "Output"}
    if not required.issubset(df.columns):
        st.error("Missing required columns: " + ", ".join(required))
        st.stop()

    report_time = df["Arrival"].max().round("H")
    st.success(f"Detected Report Time: {report_time.strftime('%Y-%m-%d %H:%M')}")

    # 🔹 Feed Icon
    def feed_icon(feed):
        return "👶" if "sm" in feed else "🧔"

    # 🔹 Merge Origin rows at same timestamp
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

    # 🔹 A-model classification
    def classify_A_model(row_0, prior_rows):
        epic = {"Trinidad", "Tobago", "WASP-12b", "Macedonia"}
        anchor = {"Saturn", "Jupiter", "Kepler-62f", "Kepler-442b"}
        o0 = row_0["Origin"]
        t0 = row_0["Arrival"]

        # Time Tag
        if t0.hour == 18 and t0.minute == 0:
            time = "open"
        elif 18 < t0.hour < 2 or (t0.hour == 1 and t0.minute < 59):
            time = "early"
        else:
            time = "late"

        is_epic = o0 in epic
        is_anchor = o0 in anchor
        prior = set(prior_rows["Origin"])
        has_strong = bool(prior & epic) or bool(prior & anchor)

        if is_epic and time == "open": return "A01", "Open Epic 0"
        if is_anchor and time == "open": return "A02", "Open Anchor 0"
        if not is_anchor and time == "open" and has_strong: return "A03", "Open non-Anchor 0"
        if not is_anchor and time == "early" and has_strong: return "A04", "Early non-Anchor 0"
        if is_anchor and time == "late": return "A05", "Late Anchor 0"
        if not is_anchor and time == "late" and has_strong: return "A06", "Late non-Anchor 0"
        if not is_anchor and time == "open" and not has_strong: return "A07", "Open general 0"
        if not is_anchor and time == "early" and not has_strong: return "A08", "Early general 0"
        if not is_anchor and time == "late" and not has_strong: return "A09", "Late general 0"
        return None, None

    # 🔹 A-model detection logic
    def detect_A_models(df):
        results = []
        for output in df["Output"].unique():
            subset = df[df["Output"] == output].sort_values("Arrival")
            if subset.shape[0] < 3:
                continue
            last = subset.iloc[-1]
            if last["M #"] != 0:
                continue
            prior = subset.iloc[:-1]
            if prior.shape[0] < 2:
                continue

            model, label = classify_A_model(last, prior)
            if model:
                result = {
                    "model": model,
                    "label": label,
                    "output": output,
                    "timestamp": last["Arrival"],
                    "sequence": subset,
                    "feeds": subset["Feed"].nunique()
                }
                results.append(result)
        return results

    # 🔹 Run detection and display results
    a_model_results = detect_A_models(df)
    st.subheader("🔍 A Model Results")

    for res in a_model_results:
        hrs = (report_time - res["timestamp"]).total_seconds() / 3600
        m_path = " → ".join([f"|{row['M #']}|" for _, row in res["sequence"].iterrows()])
        icons = "".join([feed_icon(row["Feed"]) for _, row in res["sequence"].iterrows()])

        header = f"{res['model']}. 2+ to {res['label']} – 1 result"
        summary = f"{int(hrs)} hours ago, at {res['timestamp'].strftime('%Y-%m-%d %H:%M')}, " \
                  f"at {res['output']}, {m_path} Cross [{icons}]"

        with st.expander(header + "\n" + summary):
            st.table(merge_sequence(res["sequence"]))

else:
    st.info("Upload a CSV to begin scanning A Models.")
