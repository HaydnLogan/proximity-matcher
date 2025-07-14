import streamlit as st
import pandas as pd
import datetime as dt
from dateutil import parser
from collections import defaultdict

# --------------------------------------------
# 🔧 Utilities
# --------------------------------------------
def clean_timestamp(ts):
    if isinstance(ts, str):
        dt_obj = parser.parse(ts)
        return dt_obj.replace(tzinfo=None)
    return pd.to_datetime(ts, errors="coerce")

def extract_origins(columns):
    origins = {}
    for col in columns:
        col = col.strip().lower()
        if col in ["time", "open"]:
            continue
        if any(suffix in col for suffix in [" h", " l", " c"]):
            bracket = ""
            if "[" in col and "]" in col:
                bracket = col[col.find("["):col.find("]")+1]
            core = col.replace(" h", "").replace(" l", "").replace(" c", "")
            if bracket and not core.endswith(bracket):
                core += bracket
            group_id = core
            origins.setdefault(group_id, []).append(col)
    return {origin: cols for origin, cols in origins.items() if len(cols) == 3}

def get_weekly_anchor(report_time, weeks_back, start_hour):
    days_since_sunday = (report_time.weekday() + 1) % 7
    anchor_date = (report_time - dt.timedelta(days=days_since_sunday + 7 * (weeks_back - 1)))
    return anchor_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)

def get_monthly_anchor(report_time, months_back, start_hour):
    year = report_time.year
    month = report_time.month - (months_back - 1)
    while month <= 0:
        month += 12
        year -= 1
    return dt.datetime(year, month, 1, hour=start_hour, minute=0, second=0, microsecond=0)

def get_day_index(arrival, report_time, start_hour):
    if not report_time:
        return "[0] Today"
    report_day_start = report_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    if report_time.hour < start_hour:
        report_day_start -= dt.timedelta(days=1)
    days_diff = (arrival - report_day_start) // dt.timedelta(days=1)
    return f"[{int(days_diff)}]"

def calculate_pivot(H, L, C, M_value):
    return ((H + L + C) / 3) + M_value * (H - L)

def get_most_recent_time(df):
    return df["time"].max()

def get_input_value(df, report_time):
    match = df[df["time"] == report_time]
    return match.iloc[-1]["open"] if not match.empty and "open" in match.columns else None

# --------------------------------------------
# 🚦 Streamlit UI + Report Builder
# --------------------------------------------
st.set_page_config(layout="wide")
st.title("🧬 Unified Traveler Feed Processor + A-Model Analyzer")

# Upload section
small_feed_file = st.file_uploader("Upload small feed", type="csv")
big_feed_file = st.file_uploader("Upload big feed", type="csv")
measurement_file = st.file_uploader("Upload measurement file", type=["xlsx", "xls"])

report_mode = st.radio("Select Report Time & Date", ["Most Current", "Choose a time"], key="report_mode_radio")
if report_mode == "Choose a time":
    selected_date = st.date_input("Select Report Date", value=dt.date.today(), key="report_date_picker")
    selected_time = st.time_input("Select Report Time", value=dt.time(18, 0), key="report_time_picker")
    report_time = dt.datetime.combine(selected_date, selected_time)
else:
    report_time = None

# Additional Settings
day_start_choice = st.radio("Select Day Start Time", ["17:00", "18:00"])
day_start_hour = int(day_start_choice.split(":")[0])
scope_type = st.radio("Scope by", ["Rows", "Days"])
scope_value = st.number_input(f"Enter number of {scope_type.lower()}", min_value=1, value=10)

# Once everything is uploaded...
if small_feed_file and big_feed_file and measurement_file:
    small_df = pd.read_csv(small_feed_file)
    big_df = pd.read_csv(big_feed_file)

    small_df.columns = small_df.columns.str.strip().str.lower()
    big_df.columns = big_df.columns.str.strip().str.lower()

    small_df["time"] = small_df["time"].apply(clean_timestamp)
    big_df["time"] = big_df["time"].apply(clean_timestamp)

    xls = pd.ExcelFile(measurement_file)
    available_sheets = xls.sheet_names
    sheet_choice = st.selectbox("Select measurement tab", available_sheets)
    measurements = pd.read_excel(measurement_file, sheet_name=sheet_choice)
    measurements.columns = measurements.columns.str.strip().str.lower()

    if report_mode == "Most Current":
        report_time = max(get_most_recent_time(small_df), get_most_recent_time(big_df))

    input_value = get_input_value(small_df, report_time) or get_input_value(big_df, report_time)

    if not report_time or input_value is None:
        st.error("⚠️ Could not determine Report Time or Input Value.")
    else:
        from processor import process_feed  # You'd move your process_feed() function into a file called processor.py
        results = process_feed(small_df, "Sm", report_time, scope_type, scope_value, day_start_hour, measurements, input_value)
        results += process_feed(big_df, "Bg", report_time, scope_type, scope_value, day_start_hour, measurements, input_value)

        final_df = pd.DataFrame(results)
        final_df.sort_values(by=["Output", "Arrival"], ascending=[False, True], inplace=True)
        final_df["Arrival"] = pd.to_datetime(final_df["Arrival"]).dt.strftime("%#d-%b-%y %H:%M")

        st.success(f"✅ Report Time: {report_time.strftime('%d-%b-%y %H:%M')}")
        st.success(f"✅ Input value: {input_value}")

        st.dataframe(final_df)
        csv_bytes = final_df.to_csv(index=False).encode()
        st.download_button("📥 Download Traveler Report CSV", data=csv_bytes, file_name=f"origin_report_{report_time.strftime('%y-%m-%d_%H-%M')}.csv")

        # 🔍 Now run A Model logic
        st.markdown("---")
        st.header("🅰️ Position A Models – Output-Centric Scanner")

        # ✅ Inline A-Model Logic
        def feed_icon(feed): return "👶" if "sm" in feed else "🧔"

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
            filtered = []
            all_signatures = [tuple(seq["M #"].tolist()) for seq in raw_sequences]
            for i, sig in enumerate(all_signatures):
                longer = any(set(sig).issubset(set(other)) and len(sig) < len(other) for j, other in enumerate(all_signatures) if i != j)
                if not longer:
                    filtered.append(raw_sequences[i])
            return filtered

        def classify_A_model(row_0, prior_rows):
            epic = {"Trinidad", "Tobago", "WASP-12b", "Macedonia"}
            anchor = {"Saturn", "Jupiter", "Kepler-62f", "Kepler-442b"}
            t0 = row_0["Arrival"]
            o0 = row_0["Origin"]
            time = "open" if t0.hour == 18 and t0.minute == 0 else "early" if (18 < t0.hour < 2 or (t0.hour == 1 and t0.minute < 59)) else "late"
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
            df["Arrival"] = pd.to_datetime(df["Arrival"], errors="coerce")
            report_time = df["Arrival"].max()
            model_outputs = defaultdict(list)
            for output in df["Output"].unique():
                subset = df[df["Output"] == output]
                sequences = find_flexible_descents(subset)
                seen_signatures = set()
                for seq in sequences:
                    if seq.shape[0] < 3 or seq.iloc[-1]["M #"] != 0:
                        continue
                    sig = tuple(seq["M #"].tolist())
                    if sig in seen_signatures:
                        continue
                    seen_signatures.add(sig)
                    prior = seq.iloc[:-1]
                    last = seq.iloc[-1]
                    model, label = classify_A_model(last, prior)
                    if model:
                        model_outputs[model].append({
                            "label": label,
                            "output": output,
                            "timestamp": last["Arrival"],
                            "sequence": seq,
                            "feeds": seq["Feed"].nunique()
                        })
            return model_outputs, report_time

        def show_a_model_results(model_outputs, report_time):
            labels = {
                "A01": "Open Epic 0", "A02": "Open Anchor 0", "A03": "Open non-Anchor 0",
                "A04": "Early non-Anchor 0", "A05": "Late Anchor 0", "A06": "Late non-Anchor 0",
                "A07": "Open general 0", "A08": "Early general 0", "A09": "Late general 0"
            }
            for code, label in labels.items():
                results = model_outputs.get(code, [])
                if not results:
                    continue
                with st.expander(f"{code}. {label} ({len(results)} sequences)"):
                    for r in results:
                        seq = r["sequence"]
                        m_path = " → ".join([f"|{row['M #']}|" for _, row in seq.iterrows()])
                        icons = "".join([feed_icon(row["Feed"]) for _, row in seq.iterrows()])
                        summary = f"{m_path} Cross [{icons}]"
                        st.markdown(summary)
                        st.table(seq.reset_index(drop=True))

        # 🔍 Detect and Show
        model_outputs, report_time = detect_A_models(final_df.copy())
        show_a_model_results(model_outputs, report_time)
