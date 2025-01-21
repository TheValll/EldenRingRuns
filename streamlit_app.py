import streamlit as st
import pandas as pd
from get_data import get
from collections import OrderedDict


# Set up the Streamlit application
st.set_page_config(
    page_title="ValRuns", 
    layout="wide", 
    page_icon="logo.png",
    initial_sidebar_state="auto",
)


# Hide streamlit menu (hamburger) and footer
padding_top = 0
hide_streamlit_style = f"""
<style>
#MainMenu {{visibility: none;}}
.appview-container .main .block-container{{padding-top: {padding_top}rem;}}
footer {{visibility: none;}}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


# Function to convert time string to milliseconds
def time_to_milliseconds(time_str):
    hours, minutes, seconds = time_str.split(":")
    
    if "." in seconds:
        seconds, milliseconds = seconds.split(".")
        milliseconds = milliseconds[:3]
    else:
        milliseconds = "0"
    
    hours_ms = int(hours) * 3600 * 1000
    minutes_ms = int(minutes) * 60 * 1000
    seconds_ms = int(seconds) * 1000
    milliseconds = int(milliseconds)
    
    total_ms = hours_ms + minutes_ms + seconds_ms + milliseconds
    return total_ms


# Function to convert milliseconds to readable time format
def millisecond_to_readable(time_in_milliseconds):
    seconds = time_in_milliseconds // 1000
    minutes = seconds // 60
    hours = minutes // 60
    
    seconds = seconds % 60
    minutes = minutes % 60

    if hours == 0:
        if minutes == 0:
            return f"{seconds:02d}.{str(time_in_milliseconds)[-1:]}"

        return f"{minutes:02d}:{seconds:02d}.{str(time_in_milliseconds)[-1:]}"
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{str(time_in_milliseconds)[-1:]}"


# Function to calculate cumulative times
def get_cumulative_times(game_times):
    cumulative_times = []
    total_time = 0
    for time in game_times:
        total_time += time
        cumulative_times.append(total_time)
    return cumulative_times


# Get data
try:
    data = get()
except Exception as E:
    st.warning('No data found')
    st.error(E)
    st.stop()

GameName = data["GameName"]
CategoryName = data["CategoryName"]
AttemptCount = data["AttemptCount"]
Segments = data["Segments"]
Runs = data["Runs"]
PB_splits = data["PB_splits"]

st.title(GameName + " " + CategoryName)
st.write(f"Attempts counts: {AttemptCount}")
st.warning("Attempts 1-32 are falsy with 3min of gap cause splits bug")

runs_info = []


for run_list in Runs:
    for run in run_list:
        run_info = OrderedDict({
            "RunStart": run["RunStart"],
            "SplitsNames": [],
            "GameTimes": [] 
        })

        for segment in Segments:
            for split in segment["SegmentHistory"]:
                if run["AttemptID"] == split["AttemptID"]:
                    run_info["SplitsNames"].append(segment["Name"])
                    run_info["GameTimes"].append(split["GameTime"])

        runs_info.append(run_info)

# ----------------------------
# Personnal best splits 
# ----------------------------

PB_splits_readable = [millisecond_to_readable(time_to_milliseconds(split)) for split in PB_splits]

pb_row = {"Date": "Personal Best"}
for i, split_name in enumerate([split["Name"] for split in Segments]):
    pb_row[split_name] = PB_splits_readable[i] if i < len(PB_splits_readable) else ""

all_rows = [pb_row]

# Create final rows
all_rows_with_cumulative_times = []

for run in reversed(runs_info):
    date = run["RunStart"]
    splits_names = run["SplitsNames"]
    game_times = run["GameTimes"]
    
    if splits_names == []:
        continue
    
    game_times_ms = [time_to_milliseconds(time) for time in game_times]
    
    run_cumulative_times = get_cumulative_times(game_times_ms)

    row = {"Date": date}
    for i, split_name in enumerate(splits_names):
        row[split_name] = millisecond_to_readable(run_cumulative_times[i])
    

    all_splits = [split["Name"] for split in Segments]
    for split in all_splits:
        if split not in row:
            row[split] = ""

    all_rows_with_cumulative_times.append(row)


all_rows.extend(all_rows_with_cumulative_times)
df_all_runs_with_cumulative_times = pd.DataFrame(all_rows)


# Define html table
html_table = f"""
<div style="margin-right: 20px;">
    <style>
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center !important;
            vertical-align: middle;      
        }}
        th {{
            background-color: #f2f2f2;
            color: #333;
            white-space: nowrap;         
            height: 40px;                
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f1f1f1;
        }}
    </style>
    {df_all_runs_with_cumulative_times.to_html(index=False, escape=False)}
</div>
"""

# Display table
st.markdown(html_table, unsafe_allow_html=True)