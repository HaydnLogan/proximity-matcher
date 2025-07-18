import pandas as pd
import datetime as dt
from dateutil import parser

# 🔬 Feed parsing, merging, and traveler report generation 

# -------------------
# UTILITY FUNCTIONS
# -------------------
def clean_timestamp(ts):
    if isinstance(ts, str):
        dt_obj = parser.parse(ts)
        return dt_obj.replace(tzinfo=None)
    return pd.to_datetime(ts, errors="coerce")

def get_most_recent_time(df):
    return df["time"].max()

def get_input_value(df, report_time):
    match = df[df["time"] == report_time]
    return match.iloc[-1]["open"] if not match.empty and "open" in match.columns else None

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
    anchor = anchor_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    return anchor

def get_monthly_anchor(report_time, months_back, start_hour):
    year = report_time.year
    month = report_time.month - (months_back - 1)
    while month <= 0:
        month += 12
        year -= 1
    anchor = dt.datetime(year, month, 1, hour=start_hour, minute=0, second=0, microsecond=0)
    return anchor

# -------------------
# MAIN RUNNER LOGIC
# -------------------
def run_feed_processor(small_df, big_df, measurements, report_time, scope_type, scope_value, start_hour):
    results = []

    def process_feed(df, feed_type):
        df.columns = df.columns.str.strip().str.lower()
        df["time"] = df["time"].apply(clean_timestamp)
        df = df.iloc[::-1]
        origins = extract_origins(df.columns)

        # Trim rows by scope
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

        input_value = get_input_value(df, report_time)
        if input_value is None:
            return []

        for origin, cols in origins.items():
            relevant_rows = df[["time", "open"] + cols].dropna()
            origin_name = origin.lower()
            is_special = any(tag in origin_name for tag in ["wasp", "macedonia"])

            if is_special:
                report_row = relevant_rows[relevant_rows["time"] == report_time]
                if report_row.empty:
                    continue
                current = report_row.iloc[0]
                bracket_number = 0
                if "[" in origin_name and "]" in origin_name:
                    try:
                        bracket_number = int(origin_name.split("[")[-1].replace("]", ""))
                    except:
                        bracket_number = 0

                if "wasp" in origin_name:
                    arrival_time = get_weekly_anchor(report_time, max(1, bracket_number), start_hour)
                elif "macedonia" in origin_name:
                    arrival_time = get_monthly_anchor(report_time, max(1, bracket_number), start_hour)
                else:
                    arrival_time = report_time

                H, L, C = current[cols[0]], current[cols[1]], current[cols[2]]
                for _, row in measurements.iterrows():
                    output = calculate_pivot(H, L, C, row["m value"])
                    day = get_day_index(arrival_time, report_time, start_hour)
                    results.append({
                        "Feed": feed_type,
                        "Arrival": arrival_time,
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
                continue

            for i in range(len(relevant_rows) - 1):
                current = relevant_rows.iloc[i]
                above = relevant_rows.iloc[i + 1]
                changed = any(current[col] != above[col] for col in cols)
                if not changed:
                    continue

                arrival_time = current["time"]
                H, L, C = current[cols[0]], current[cols[1]], current[cols[2]]
                for _, row in measurements.iterrows():
                    output = calculate_pivot(H, L, C, row["m value"])
                    day = get_day_index(arrival_time, report_time, start_hour)
                    results.append({
                        "Feed": feed_type,
                        "Arrival": arrival_time,
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

    process_feed(small_df, "Sm")
    process_feed(big_df, "Bg")

    final_df = pd.DataFrame(results)
    final_df.sort_values(by=["Output", "Arrival"], ascending=[False, True], inplace=True)
    final_df["Arrival"] = pd.to_datetime(final_df["Arrival"]).dt.strftime("%#d-%b-%y %H:%M")
    return final_df

