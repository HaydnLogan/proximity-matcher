import streamlit as st
import pandas as pd
import datetime as dt

# 📁 File Uploads
st.header("🧬 Data Feed Processor v07b UTC added")
small_feed_file = st.file_uploader("Upload small feed", type="csv")
big_feed_file = st.file_uploader("Upload big feed", type="csv")
measurement_file = st.file_uploader("Upload measurement file", type=["xlsx", "xls"])

# 📅 Settings
report_mode = st.radio("Select Report Time & Date", ["Most Current", "Choose a time"])
report_time = st.datetime_input("Choose Report Time", value=dt.datetime.now()) if report_mode == "Choose a time" else None
day_start_choice = st.radio("Select Day Start Time", ["17:00", "18:00"])
day_start_hour = int(day_start_choice.split(":")[0])
scope_type = st.radio("Scope by", ["Rows", "Days"])
scope_value = st.number_input(f"Enter number of {scope_type.lower()}", min_value=1, value=10)

# 🔧 Utilities
def clean_timestamp(ts):
    if isinstance(ts, str):
        return pd.to_datetime(ts, utc=True).tz_convert(None)
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
            group_id = core + bracket
            origins.setdefault(group_id, []).append(col)
    return {origin: cols for origin, cols in origins.items() if len(cols) == 3}

def get_day_index(arrival, report, start_hour):
    if not report:
        return "[0] Today"
    days_diff = (arrival - dt.datetime.combine(report.date(), dt.time(start_hour))) // dt.timedelta(days=1)
    return f"[{int(days_diff)}]"

def calculate_pivot(H, L, C, M_value):
    return ((H + L + C) / 3) + M_value * (H - L)

def get_most_recent_time(df):
    return df["time"].max()

def get_input_value(df, report_time):
    match = df[df["time"] == report_time]
    return match.iloc[-1]["open"] if not match.empty and "open" in match.columns else None

def process_feed(df, feed_type, report_time, scope_type, scope_value, start_hour, measurements, input_value):
    df.columns = df.columns.str.strip().str.lower()
    df["time"] = df["time"].apply(clean_timestamp)
    df = df.iloc[::-1]
    origins = extract_origins(df.columns)
    new_data_rows = []

    if report_time:
        if scope_type == "Rows":
            try:
                start_index = df[df["time"] == report_time].index[0]
                df = df.iloc[start_index:start_index+scope_value]
            except:
                pass
        else:
            cutoff = report_time - pd.Timedelta(days=scope_value)
            df = df[df["time"] >= cutoff]

    for origin, cols in origins.items():
        relevant_rows = df[["time", "open"] + cols].dropna()
        for i in range(len(relevant_rows)-1):
            current = relevant_rows.iloc[i]
            above = relevant_rows.iloc[i+1]
            changed = any(current[col] != above[col] for col in cols)
            is_special = any(tag in origin for tag in ["wasp", "macedonia"])
            if is_special and current["time"] == report_time:
                H, L, C = current[cols[0]], current[cols[1]], current[cols[2]]
                for _, row in measurements.iterrows():
                    output = calculate_pivot(H, L, C, row["m value"])
                    day = get_day_index(current["time"], report_time, start_hour)
                    new_data_rows.append({
                        "Feed": feed_type,
                        "Arrival": current["time"],
                        "Origin": origin,
                        "M Name": row["m name"],
                        "M #": row["m #"],
                        "R #": row["r #"],
                        "Tag": row["tag"],
                        "Family": row["family"],
                        "Input": input_value,
                        "Output": output,
                        "Diff": output - input_value,
                        "Day": day
                    })
            elif not is_special and changed:
                H, L, C = current[cols[0]], current[cols[1]], current[cols[2]]
                for _, row in measurements.iterrows():
                    output = calculate_pivot(H, L, C, row["m value"])
                    day = get_day_index(current["time"], report_time, start_hour)
                    new_data_rows.append({
                        "Feed": feed_type,
                        "Arrival": current["time"],
                        "Origin": origin,
                        "M Name": row["m name"],
                        "M #": row["m #"],
                        "R #": row["r #"],
                        "Tag": row["tag"],
                        "Family": row["family"],
                        "Input": input_value,
                        "Output": output,
                        "Diff": output - input_value,
                        "Day": day
                    })
    return new_data_rows

# 🧬 Main Runner
if small_feed_file and big_feed_file and measurement_file:
    try:
        small_df = pd.read_csv(small_feed_file)
        big_df = pd.read_csv(big_feed_file)
        group_2a = pd.read_excel(measurement_file, sheet_name="2a")
        group_2a.columns = group_2a.columns.str.strip().str.lower()

        # Clean feeds
        small_df.columns = small_df.columns.str.strip().str.lower()
        small_df["time"] = small_df["time"].apply(clean_timestamp)
        big_df.columns = big_df.columns.str.strip().str.lower()
        big_df["time"] = big_df["time"].apply(clean_timestamp)

        # Debug feed timestamps
        st.write("🕒 Most recent time in small feed:", get_most_recent_time(small_df))
        st.write("🕒 Most recent time in big feed:", get_most_recent_time(big_df))

        # Determine report time
        if report_mode == "Most Current":
            report_time = max(get_most_recent_time(small_df), get_most_recent_time(big_df))

        input_value = get_input_value(small_df, report_time)
        if input_value is None:
            input_value = get_input_value(big_df, report_time)

        if report_time is None or input_value is None:
            st.error("⚠️ Could not determine Report Time or Input Value.")
        else:
            st.success(f"✅ Report Time: {report_time}")
            st.success(f"✅ Input value: {input_value}")

            results = []
            results += process_feed(small_df, "Sm", report_time, scope_type, scope_value, day_start_hour, group_2a, input_value)
            results += process_feed(big_df, "Bg", report_time, scope_type, scope_value, day_start_hour, group_2a, input_value)

            final_df = pd.DataFrame(results)
            final_df.sort_values(by=["Output", "Arrival"], ascending=[False, True], inplace=True)

            final_df["Arrival"] = pd.to_datetime(final_df["Arrival"]).dt.strftime("%#d-%b-%y %H:%M")
            
            st.dataframe(final_df)

            csv_bytes = final_df.to_csv(index=False).encode()
            st.download_button("📥 Download Report CSV", data=csv_bytes, file_name="origin_report.csv", mime="text/csv")
    except Exception as e:
        st.error(f"❌ Processing error: {e}")
