import streamlit as st
import pandas as pd
from datetime import datetime

st.title("🅰️ Position A Models – M # 0 Confluence Scanner")

uploaded_file = st.file_uploader("📤 Upload your report CSV. cP v04b", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df["Arrival"] = pd.to_datetime(df["Arrival"], errors="coerce")

    required = {"Arrival", "Day", "Origin", "M #", "Feed", "Output"}
    if not required.issubset(df.columns):
        st.error("Missing required columns: " + ", ".join(required))
        st.stop()

    report_time = df["Arrival"].max()
    st.success(f"Detected Report Time: {report_time.strftime('%Y-%m-%d %H:%M')}")

    def feed_icon(feed): return "👶" if "sm" in feed else "🧔"

    def merge_sequence(seq):
        merged, seen = [], {}
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
                seen[key] = len(merged) - 1  # fix here: point to newly added row
        return pd.DataFrame(merged)

    def classify_A_model(row_0, prior_rows):
        epic = {"Trinidad", "Tobago", "WASP-12b", "Macedonia"}
        anchor = {"Saturn", "Jupiter", "Kepler-62f", "Kepler-442b"}
        t0 = row_0["Arrival"]
        o0 = row_0["Origin"]

        time = "open" if t0.hour == 18 and t0.minute == 0 else \
               "early" if (18 < t0.hour < 2 or (t0.hour == 1 and t0.minute < 59)) else "late"
        is_epic = o0 in epic
        is_anchor = o0 in anchor
        prior = set(prior_rows["Origin"])
        prior_has_strong = bool(prior & epic) or bool(prior & anchor)

        if is_epic and time == "open": return "A01", "Open Epic 0"
        if is_anchor and time == "open": return "A02", "Open Anchor 0"
        if not is_anchor and time == "open" and prior_has_strong: return "A03", "Open non-Anchor 0"
        if not is_anchor and time == "early" and prior_has_strong: return "A04", "Early non-Anchor 0"
        if is_anchor and time == "late": return "A05", "Late Anchor 0"
        if not is_anchor and time == "late" and prior_has_strong: return "A06", "Late non-Anchor 0"
        if not is_anchor and time == "open" and not prior_has_strong: return "A07", "Open general 0"
        if not is_anchor and time == "early" and not prior_has_strong: return "A08", "Early general 0"
        if not is_anchor and time == "late" and not prior_has_strong: return "A09", "Late general 0"
        return None, None


def detect_A_models(df):
    results = []

    for output in df["Output"].unique():
        subset = df[df["Output"] == output]
        sequences = find_strict_descending_to_zero(subset)

        for seq in sequences:
            if seq.shape[0] < 3: continue
            if seq.iloc[-1]["M #"] != 0: continue

            prior = seq.iloc[:-1]
            last = seq.iloc[-1]
            model, label = classify_A_model(last, prior)

            if model:
                results.append({
                    "model": model,
                    "label": label,
                    "output": output,
                    "timestamp": last["Arrival"],
                    "sequence": seq,
                    "feeds": seq["Feed"].nunique()
                })

    return results


def find_strict_descending_to_zero(df_subset):
    sequences = []
    rows = df_subset.sort_values("Arrival")
    ms_list = rows["M #"].tolist()

    for i in range(len(ms_list) - 2):
        path = []
        seen = set()

        for j in range(i, len(ms_list)):
            m = ms_list[j]
            abs_m = abs(m)

            if m == 0:
                if len(path) >= 2:
                    seq_rows = rows.iloc[i:j+1]
                    sequences.append(seq_rows)
                break

            if abs_m in seen:
                break
            if path and abs_m >= abs(path[-1]):
                break

            path.append(m)
            seen.add(abs_m)

    return sequences


    # 🔍 Run detection
    a_results = detect_A_models(df)

    # 🔎 Display grouped by A model
    for model_code in [f"A0{i}" for i in range(1, 10)]:
        matches = [r for r in a_results if r["model"] == model_code]
        if matches:
            label = matches[0]["label"]
            st.markdown(f"### {model_code}. 2+ to {label} – {len(matches)} result{'s' if len(matches) != 1 else ''}")
            for res in matches:
                t = res["timestamp"]
                hrs = "-" if pd.isnull(t) else int((report_time - t).total_seconds() / 3600)
                time_str = "Unknown" if pd.isnull(t) else t.strftime('%Y-%m-%d %H:%M')
                m_path = " → ".join([f"|{row['M #']}|" for _, row in res["sequence"].iterrows()])
                icons = "".join([feed_icon(row["Feed"]) for _, row in res["sequence"].iterrows()])
                summary = f"{hrs} hours ago, at {time_str}, at {res['output']}, {m_path} Cross [{icons}]"

                with st.expander(summary):
                    st.table(merge_sequence(res["sequence"]))
else:
    st.info("☝️ Upload a CSV file to activate A Model scanning.")
