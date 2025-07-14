import streamlit as st
import pandas as pd
from datetime import datetime
from collections import defaultdict

# 🤖 Detection logic 

def feed_icon(feed):
    return "👶" if "sm" in feed.lower() else "🧔"

def find_flexible_descents(df_subset):
    rows = df_subset[df_subset["Output"] > 0].sort_values("Arrival").reset_index(drop=True)
    raw_sequences = []

    for i in range(len(rows)):
        path = []
        seen = set()
        last_abs = float("inf")

        for j in range(i, len(rows)):
            m = rows.loc[j, "M #"]
            abs_m = abs(m)

            if m == 0:
                if len(path) >= 2:
                    path.append(j)
                    raw_sequences.append(rows.loc[path])
                break

            if abs_m in seen or abs_m >= last_abs:
                continue

            path.append(j)
            seen.add(abs_m)
            last_abs = abs_m

    # Filter embedded shorter sequences
    filtered = []
    all_signatures = [tuple(seq["M #"].tolist()) for seq in raw_sequences]

    for i, sig in enumerate(all_signatures):
        longer = any(set(sig).issubset(set(other)) and len(sig) < len(other) for j, other in enumerate(all_signatures) if i != j)
        if not longer:
            filtered.append(raw_sequences[i])

    return filtered

def sequence_signature(seq):
    return tuple(seq["M #"].tolist())

def classify_A_model(row_0, prior_rows):
    epic = {"trinidad", "tobago", "wasp-12b", "macedonia"}
    anchor = {"spain", "saturn", "jupiter", "kepler-62f", "kepler-442b"}

    t0 = row_0["Arrival"]
    o0 = row_0["Origin"]
    time = "open" if t0.hour == 18 and t0.minute == 0 else \
           "early" if (18 < t0.hour < 2 or (t0.hour == 1 and t0.minute < 59)) else "late"
    is_epic = o0 in epic
    is_anchor = o0 in anchor
    prior = set(prior_rows["Origin"])
    strong = bool(prior & epic) or bool(prior & anchor)

    if is_epic and time == "open": return "A01", "Open Epic 0"
    if is_anchor and time == "open": return "A02", "Open Anchor 0"
    if not is_anchor and time == "open" and strong: return "A03", "Open non-Anchor 0"
    if not is_anchor and time == "early" and strong: return "A04", "Early non-Anchor 0"
    if is_anchor and time == "late": return "A05", "Late Anchor 0"
    if not is_anchor and time == "late" and strong: return "A06", "Late non-Anchor 0"
    if not is_anchor and time == "open" and not strong: return "A07", "Open general 0"
    if not is_anchor and time == "early" and not strong: return "A08", "Early general 0"
    if not is_anchor and time == "late" and not strong: return "A09", "Late general 0"
    return None, None

def detect_A_models(df):
    report_time = df["Arrival"].max()
    model_outputs = defaultdict(list)

    # ⛓️ Track signatures of actual classified longer matches
    valid_long_matches = []

    for output in df["Output"].unique():
        subset = df[df["Output"] == output]
        sequences = find_flexible_descents(subset)

        seen_signatures = set()
        for seq in sequences:
            if seq.shape[0] < 3 or seq.iloc[-1]["M #"] != 0:
                continue
            sig = sequence_signature(seq)
            if sig in seen_signatures: continue

            prior = seq.iloc[:-1]
            last = seq.iloc[-1]
            model, label = classify_A_model(last, prior)

            if model:
                seen_signatures.add(sig)
                valid_long_matches.append(sig)  # ✅ Only storing confirmed A Models

                model_outputs[model].append({
                    "label": label,
                    "output": output,
                    "timestamp": last["Arrival"],
                    "sequence": seq,
                    "feeds": seq["Feed"].nunique()
                })

    # 🔍 Detect valid pairs, skipping those subsumed by confirmed longer matches
    for output in df["Output"].unique():
        subset = df[df["Output"] == output].sort_values("Arrival").reset_index(drop=True)
        for i in range(len(subset) - 1):
            row1 = subset.iloc[i]
            row2 = subset.iloc[i + 1]

            if row1["M #"] == 0 or row2["M #"] != 0:
                continue

            pair_sig = (row1["M #"], row2["M #"])
            sig_sorted = tuple(sorted(pair_sig) + [0])

            # ⛔️ Skip if pair is part of confirmed longer sequence
            if any(set(sig_sorted).issubset(set(l)) and len(l) > 2 for l in valid_long_matches):
                continue

            prior = pd.DataFrame([row1])
            last = row2
            model, label = classify_A_model(last, prior)

            if model:
                full_seq = pd.concat([prior, pd.DataFrame([last])])
                model_outputs[model + "pr"].append({
                    "label": label.replace(" 0", " Pair 0"),
                    "output": output,
                    "timestamp": last["Arrival"],
                    "sequence": full_seq,
                    "feeds": full_seq["Feed"].nunique()
                })

    return model_outputs, report_time



def show_a_model_results(model_outputs, report_time):
    full_labels = {
        "A01": "Open Epic 0", "A02": "Open Anchor 0", "A03": "Open non-Anchor 0",
        "A04": "Early non-Anchor 0", "A05": "Late Anchor 0", "A06": "Late non-Anchor 0",
        "A07": "Open general 0", "A08": "Early general 0", "A09": "Late general 0"
    }

    st.subheader("🔍 A Model Results")

    for base_code, label in full_labels.items():
        for suffix in ["", "pr"]:
            code = base_code + suffix
            display_label = f"{code}. {'Pair to' if suffix == 'pr' else '2+ to'} {label}"
            results = model_outputs.get(code, [])
            today = [r for r in results if "Today [0]" in r["sequence"].iloc[-1]["Day"]] if results else []
            other = [r for r in results if "Today [0]" not in r["sequence"].iloc[-1]["Day"]] if results else []

            output_count = len(set(r["output"] for r in results)) if results else 0
            header = f"{display_label} – {output_count} output{'s' if output_count != 1 else ''}"

            with st.expander(header):
                if results:
                    def render_group(title, group):
                        st.markdown(f"#### {title}")
                        groups = defaultdict(list)
                        for r in group:
                            groups[r["output"]].append(r)

                        for out_val, items in groups.items():
                            latest = max(items, key=lambda r: r["timestamp"])
                            hrs = int((report_time - latest["timestamp"]).total_seconds() / 3600)
                            ts = latest["timestamp"].strftime('%-m/%-d/%y %H:%M')
                            sub = f"🔸 Output {out_val:,.3f} – {len(items)} descending {hrs} hours at {ts}"

                            with st.expander(sub):
                                for res in items:
                                    seq = res["sequence"]
                                    m_path = " → ".join([f"|{row['M #']}|" for _, row in seq.iterrows()])
                                    icons = "".join([feed_icon(row["Feed"]) for _, row in seq.iterrows()])
                                    st.markdown(f"{m_path} Cross [{icons}]")
                                    st.table(seq.reset_index(drop=True))

                    if today: render_group("📅 Today", today)
                    if other: render_group("📦 Other Days", other)
                    if not today and not other:
                        st.markdown("No matching outputs.")
                else:
                    st.markdown("No matching outputs.")


# 🔁 Importable entry point
def run_a_model_detection(df):
    df["Arrival"] = pd.to_datetime(df["Arrival"], errors="coerce")
    required = {"Arrival", "Day", "Origin", "M #", "Feed", "Output"}
    if not required.issubset(df.columns):
        st.error("Missing columns: " + ", ".join(required - set(df.columns)))
        return

    df = df[df["Output"] > 0].copy()
    model_outputs, report_time = detect_A_models(df)
    show_a_model_results(model_outputs, report_time)

# 🧪 If run directly
if __name__ == "__main__":
    import streamlit as st
    uploaded_file = st.file_uploader("📄 Upload your traveler report CSV", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df["Arrival"] = pd.to_datetime(df["Arrival"], errors="coerce")
        required = {"Arrival", "Day", "Origin", "M #", "Feed", "Output"}
        if not required.issubset(df.columns):
            st.error("Missing columns: " + ", ".join(required - set(df.columns)))
            st.stop()

        df = df[df["Output"] > 0].copy()
        model_outputs, report_time = detect_A_models(df)
        show_a_model_results(model_outputs, report_time)
    else:
        st.info("☝️ Upload a CSV file to begin detection.")
