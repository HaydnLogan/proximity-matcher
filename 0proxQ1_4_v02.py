import streamlit as st
import pandas as pd
from itertools import combinations

st.set_page_config(layout="wide")
st.title("Pair & Trio Match o.o prox Analyzer v6c q1→4 cross feed ID")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if not uploaded_file:
    st.stop()

df = pd.read_csv(uploaded_file)

# --- Data Preprocessing ---
for col in ['Arrival', 'Departure']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

df['M Name'] = pd.to_numeric(df['M Name'], errors='coerce')
df['Output'] = pd.to_numeric(df['Output'], errors='coerce')
df['Origin'] = pd.to_numeric(df['Origin'], errors='coerce')
df['Day'] = df['Day'].astype(str)

initial_len = len(df)
df = df.dropna(subset=['Arrival', 'Output'])
removed_rows = initial_len - len(df)
if removed_rows > 0:
    st.warning(f"{removed_rows:,} rows removed due to invalid Arrival or Output values.")
if df.empty:
    st.error("No valid data remains after cleaning. Please upload a valid file.")
    st.stop()

# --- Helper Functions ---
def match_proximity(df, target_day):
    results = []
    today_rows = df[(df['M Name'] == 0) & (df['Day'] == target_day)]
    for idx, row in today_rows.iterrows():
        matches = df[
            (df['Output'] == row['Output']) &
            (df['M Name'].isin([1, -1])) &
            (df['Arrival'] < row['Arrival'])
        ]
        for midx, match in matches.iterrows():
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append({
                    'Row New': idx,
                    'Row Old': midx,
                    'Newest Arrival': row['Arrival'],
                    'Older Arrival': match['Arrival'],
                    'M Newer': row['M Name'],
                    'M Older': match['M Name'],
                    'Output': row['Output'],
                    'Origin New': row['Origin'],
                    'Origin Old': match['Origin'],
                    'Day': row['Day']
                })
    return results

def find_trios(df, target_day):
    trios = []
    grouped = df.groupby('Output')
    for output, group in grouped:
        rows = group.sort_values('Arrival')
        if len(rows) < 3:
            continue
        for combo in combinations(rows.index, 3):
            trio_df = rows.loc[list(combo)].sort_values('Arrival')
            if not trio_df.iloc[-1]['Day'].startswith(target_day):
                continue
            if not trio_df['Origin'].between(800, 1300).any():
                continue
            m_vals = trio_df['M Name'].abs().tolist()
            actual_m = trio_df['M Name'].tolist()
            if m_vals[0] > m_vals[1] > m_vals[2]:
                kind = "Descending Trio"
            elif m_vals[0] < m_vals[1] < m_vals[2]:
                kind = "Ascending Trio"
            else:
                continue
            trios.append({
                'Arrival': trio_df['Arrival'].tolist(),
                'M Name': actual_m,
                'Output': output,
                'Type': kind,
                'Origins': trio_df['Origin'].tolist(),
                'Rows': trio_df.index.tolist()
            })
    return sorted(trios, key=lambda x: x['Output'], reverse=True)

def query_3_1_pairs(df, day_filter):
    results = []
    target_ones = df[(df['M Name'].isin([1.0, -1.0])) & (df['Day'] == day_filter)]
    for idx, one in target_ones.iterrows():
        matches = df[
            (df['Output'] == one['Output']) &
            (df['Arrival'] < one['Arrival']) &
            (~df['M Name'].isin([1.0, -1.0])) &
            (df.index != idx)
        ]
        for m_idx, match in matches.iterrows():
            if (800 <= match['Origin'] <= 1300) or (800 <= one['Origin'] <= 1300):
                results.append({
                    'Row New': idx,
                    'Row Old': m_idx,
                    'Newest Arrival': one['Arrival'],
                    'Older Arrival': match['Arrival'],
                    'M Newer': one['M Name'],
                    'M Older': match['M Name'],
                    'Output': one['Output'],
                    'Origin New': one['Origin'],
                    'Origin Old': match['Origin'],
                    'Day': one['Day']
                })
    return sorted(results, key=lambda r: r['Output'], reverse=True)
 

def get_used_pair_ids(*queries):
    ids = set()
    for q in queries:
        for r in q:
            ids.add(tuple(sorted([r['Row Old'], r['Row New']])))
    return ids

def query_3_2_pairs(df, day_filter, exclude_ids):
    results = []
    rows = df[df['Day'] == day_filter]
    for idx, row in rows.iterrows():
        if row['M Name'] in [1.0, -1.0]:
            continue
        matches = df[
            (df['Output'] == row['Output']) &
            (df['Arrival'] < row['Arrival']) &
            (~df['M Name'].isin([1.0, -1.0])) &
            (df.index != idx)
        ]
        for m_idx, match in matches.iterrows():
            pair_id = tuple(sorted([idx, m_idx]))
            if pair_id in exclude_ids:
                continue
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append({
                    'Row New': idx,
                    'Row Old': m_idx,
                    'Newest Arrival': row['Arrival'],
                    'Older Arrival': match['Arrival'],
                    'M Newer': row['M Name'],
                    'M Older': match['M Name'],
                    'Output': row['Output'],
                    'Origin New': row['Origin'],
                    'Origin Old': match['Origin'],
                    'Day': row['Day']
                })
    return sorted(results, key=lambda r: r['Output'], reverse=True)

def query_4_opposites(df, day_filter):
    results = []
    rows = df[df['Day'] == day_filter]
    for idx, row in rows.iterrows():
        opposite_value = -row['M Name']
        matches = df[
            (df['Output'] == row['Output']) &
            (df['M Name'] == opposite_value) &
            (df['Arrival'] < row['Arrival']) &
            (df.index != idx)
        ]
        for m_idx, match in matches.iterrows():
            if (800 <= row['Origin'] <= 1300) or (800 <= match['Origin'] <= 1300):
                results.append({
                    'Row New': idx,
                    'Row Old': m_idx,
                    'Newest Arrival': row['Arrival'],
                    'Older Arrival': match['Arrival'],
                    'M Newer': row['M Name'],
                    'M Older': match['M Name'],
                    'Output': row['Output'],
                    'Origin New': row['Origin'],
                    'Origin Old': match['Origin'],
                    'Day': row['Day']
                })
    return sorted(results, key=lambda r: r['Output'], reverse=True)

def count_trio_feed_combos(trios):
    sm, bg, cross = 0, 0, 0
    for trio in trios:
        feeds = [str(df.loc[i]['Feed']).lower() for i in trio["Rows"]]
        unique = set(feeds)
        if len(unique) == 1 and "sm" in unique:
            sm += 1
        elif len(unique) == 1 and "bg" in unique:
            bg += 1
        elif len(unique) > 1:
            cross += 1
    return sm, bg, cross


# --- Display Functions ---
def get_feed_icon(feed):
    feed = str(feed).lower()
    if "sm" in feed:
        return "👶"
    elif "bg" in feed:
        return "🧔"
    else:
        return "❓"

def classify_pair(f1, f2):
    f1 = str(f1).lower()
    f2 = str(f2).lower()
    if "sm" in f1 and "sm" in f2:
        return "sm-sm"
    elif "bg" in f1 and "bg" in f2:
        return "Bg-Bg"
    elif f1 == f2:
        return "Same Feed"
    else:
        return "Cross Feed"

def count_feed_combos(results):
    sm_sm, bg_bg, cross = 0, 0, 0
    for r in results:
        f1 = str(df.loc[r['Row Old']]['Feed']).lower()
        f2 = str(df.loc[r['Row New']]['Feed']).lower()
        if "sm" in f1 and "sm" in f2:
            sm_sm += 1
        elif "bg" in f1 and "bg" in f2:
            bg_bg += 1
        elif f1 == f2:
            pass  # already counted in sm_sm/bg_bg
        else:
            cross += 1
    return sm_sm, bg_bg, cross

def display_pairs(title, results):
    sm_sm, bg_bg, cross = count_feed_combos(results)
    label = "pair" if len(results) == 1 else "pairs"
    feed_summary = f"{sm_sm} sm-sm, {bg_bg} Bg-Bg, {cross} Cross"
    st.subheader(f"{title} — {len(results)} {label}. {feed_summary}")

    filters = st.multiselect(
        "Filter Pairs by Feed Type",
        ["Show All", "sm-sm", "Bg-Bg", "Same Feed", "Cross Feed"],
        default=["Show All"]
    )

    for i, res in enumerate(results):
        feed_old = str(df.loc[res['Row Old']]['Feed'])
        feed_new = str(df.loc[res['Row New']]['Feed'])
        icon_old = get_feed_icon(feed_old)
        icon_new = get_feed_icon(feed_new)

        category = classify_pair(feed_old, feed_new)
        if "Show All" not in filters and category not in filters:
            continue

        feed_tag = ""
        if feed_old != feed_new:
            feed_tag = " 🔀 **CROSS FEED MATCH**"

        summary = (
            f"At {res['Newest Arrival']} {res['M Older']:.3f} to {res['M Newer']:.3f} "
            f"@ {res['Output']:,.3f}{feed_tag} [{icon_old}→{icon_new}]"
        )

        with st.expander(summary):
        # 🔍 Color logic inside the loop
            try:
                input_val = df.loc[res['Row New']]['Input']
                diff = res['Output'] - input_val
                abs_diff = abs(diff)
                if abs_diff < 4:
                    color = '#d3d3d3'
                elif diff >= 4:
                    color = '#ffc1c1'
                elif diff <= -4:
                    color = '#cde2ff'
                else:
                    color = None
            except:
                color = None

          # 🎨 Show colored diff bar inside expander
            if color:
                st.markdown(
                    f"<div style='background-color:{color}; padding:6px; border-radius:4px; font-weight:bold'>"
                    f"⚠️ Output/Input Δ = {diff:+.3f}</div>",
                    unsafe_allow_html=True
                )

            df_pair = pd.DataFrame([
                [feed_old, res['Row Old'], res['Older Arrival'], res['M Older'], res['Origin Old'], res['Day']],
                [feed_new, res['Row New'], res['Newest Arrival'], res['M Newer'], res['Origin New'], res['Day']]
            ], columns=["Feed", "Row", "Arrival", "M Name", "Origin", "Day"])
            df_pair.index = ["", ""]
            st.write(df_pair)


def display_trios(title, trios):
    label = "trio" if len(trios) == 1 else "trios"
    st.subheader(f"{title} — {len(trios)} {label}")
    
    # ✅ Filter controls go here
    filters = st.multiselect(
        "Filter Trios by Feed Type",
        ["Show All", "Same sm", "Same Bg", "Cross Feed"],
        default=["Show All"]
    )
    # ✅ Trio category classifier function
    def classify_trio(feeds):
        feeds = [f.lower() for f in feeds]
        unique = set(feeds)
        if len(unique) == 1 and "sm" in unique:
            return "Same sm"
        elif len(unique) == 1 and "bg" in unique:
            return "Same Bg"
        elif len(unique) > 1:
            return "Cross Feed"
        return "Other"
    
    # ✅ Loop over and filter trios before displaying
    for trio in trios:
        feeds = [str(df.loc[i]['Feed']) for i in trio["Rows"]]
        category = classify_trio(feeds)
        if "Show All" not in filters and category not in filters:
            continue

        # Summary info
        arr_str = trio['Arrival'][-1].strftime('%Y-%m-%d %H:%M:%S')
        mvals = trio['M Name']
        icons = [get_feed_icon(f) for f in feeds]
        is_cross = len(set([f.lower() for f in feeds])) > 1
        feed_tag = " 🔀 CROSS FEED MATCH" if is_cross else ""

        summary = (
            f"At {arr_str} {mvals[0]:.3f} to {mvals[1]:.3f} to {mvals[2]:.3f} "
            f"@ {trio['Output']:,.3f} ({trio['Type']}){feed_tag} [{icons[0]}→{icons[1]}→{icons[2]}]"
        )

        with st.expander(summary):
            df_trio = pd.DataFrame({
                "Feed": feeds,
                "Row": trio["Rows"],
                "Arrival": trio["Arrival"],
                "M Name": trio["M Name"],
                "Origin": trio["Origins"],
                "Output": [trio["Output"]] * 3,
                "Type": [trio["Type"]] * 3
            })
            df_trio.index.name = ""
            st.write(df_trio)




# --- Run Queries ---
query_1a = match_proximity(df, "Today [0]")
query_1b = match_proximity(df, "Yesterday [1]")
trios_today = find_trios(df, "Today [0]")
trios_yesterday = find_trios(df, "Yesterday [1]")
query_3_1a = query_3_1_pairs(df, "Today [0]")
query_3_1b = query_3_1_pairs(df, "Yesterday [1]")
used_ids_a = get_used_pair_ids(query_1a, query_3_1a)
used_ids_b = get_used_pair_ids(query_1b, query_3_1b)
query_3_2a = query_3_2_pairs(df, "Today [0]", used_ids_a)
query_3_2b = query_3_2_pairs(df, "Yesterday [1]", used_ids_b)
query_4_1a = query_4_opposites(df, "Today [0]")
query_4_1b = query_4_opposites(df, "Yesterday [1]")


# --- Display Results ---
display_pairs("Query 1.1a - Today 1→0 Pairs", query_1a)
display_pairs("Query 1.1b - Yesterday 1→0 Pairs", query_1b)
display_trios("Query 2.1a - Trios (Today)", trios_today)
display_trios("Query 2.1b - Trios (Yesterday)", trios_yesterday)
display_pairs("Query 3.1a - Today #→±1", query_3_1a)
display_pairs("Query 3.1b - Yesterday #→±1", query_3_1b)
display_pairs("Query 3.2a - Today #→# (≠±1)", query_3_2a)
display_pairs("Query 3.2b - Yesterday #→# (≠±1)", query_3_2b)
display_pairs("Query 4.1a - Opposites (Today)", query_4_1a)
display_pairs("Query 4.1b - Opposites (Yesterday)", query_4_1b)
