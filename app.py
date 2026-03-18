"""
F1 Telemetry Dashboard - FastF1 + Streamlit
Featured Driver: Franco Colapinto (COL)
"""

import os
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import fastf1
import fastf1.plotting
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timezone

# --- Cache Setup ---
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
try:
    fastf1.enable_cache(CACHE_DIR)
except AttributeError:
    fastf1.Cache.enable_cache(CACHE_DIR)

# --- Page Config ---
st.set_page_config(
    page_title="F1 Dashboard",
    page_icon="F1",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS ---
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  section[data-testid="stSidebar"] {
    background: #0a0a0a;
    border-right: 1px solid #1e1e1e;
  }
  .main .block-container { padding-top: 0.8rem; max-width: 1700px; }
  .f1-header {
    background: linear-gradient(135deg, #0D0D0D 0%, #1a0000 60%, #0D0D0D 100%);
    border-bottom: 3px solid #E10600;
    padding: 14px 24px;
    margin-bottom: 1rem;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .col-card {
    background: linear-gradient(135deg, #080810 0%, #0c1220 100%);
    border: 1px solid #1a2a4a;
    border-left: 4px solid #00D2BE;
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 0.8rem;
  }
  .metric-tile {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 5px;
    padding: 11px 12px;
    text-align: center;
    margin-bottom: 5px;
  }
  .metric-tile .val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.25rem;
    font-weight: 600;
    color: #eee;
    line-height: 1;
  }
  .metric-tile .lbl {
    color: #444;
    font-size: 0.62rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-top: 5px;
    font-weight: 500;
  }
  /* Timing table */
  .timing-table { width:100%; border-collapse:collapse; font-size:0.78rem; }
  .timing-table th {
    background:#111; color:#444; letter-spacing:0.1em; text-transform:uppercase;
    font-size:0.62rem; font-weight:600; padding:8px 10px; text-align:left;
    border-bottom:1px solid #1e1e1e; position:sticky; top:0;
  }
  .timing-table td {
    padding:6px 10px; border-bottom:1px solid #141414;
    font-family:'JetBrains Mono',monospace; color:#aaa; font-size:0.75rem;
  }
  .timing-table tr:hover td { background:#141414; }
  .timing-table tr.featured td { background:#09121e; color:#00D2BE; }
  .timing-table tr.dnf-row td { color:#3a3a3a; }
  .sp { color:#CC44FF; font-weight:700; }
  .sg { color:#39FF14; font-weight:700; }
  .sy { color:#FFD700; }
  /* Minisector bar */
  .ms-row { display:flex; gap:1px; height:5px; border-radius:2px; overflow:hidden; width:100%; }
  .ms-p { background:#CC44FF; flex:1; }
  .ms-g { background:#39FF14; flex:1; }
  .ms-y { background:#FFD700; flex:1; }
  .ms-w { background:#333; flex:1; }
  /* Section heading */
  .sh {
    color:#444; font-size:0.65rem; letter-spacing:0.22em; font-weight:600;
    text-transform:uppercase; border-bottom:1px solid #1a1a1a;
    padding-bottom:6px; margin:0.9rem 0 0.9rem 0;
  }
  /* Info box */
  .info-box {
    background:#0c0c0c; border:1px solid #1e1e1e; border-radius:5px;
    padding:14px 18px; font-size:0.82rem; color:#666; line-height:1.7;
  }
  .info-box b { color:#aaa; }
  /* Championship table */
  .champ-table { width:100%; border-collapse:collapse; font-size:0.78rem; }
  .champ-table th {
    background:#111; color:#444; letter-spacing:0.1em; text-transform:uppercase;
    font-size:0.62rem; font-weight:600; padding:7px 10px; text-align:left;
    border-bottom:1px solid #1e1e1e;
  }
  .champ-table td { padding:6px 10px; border-bottom:1px solid #141414; color:#999; font-size:0.78rem; }
  .champ-table tr:hover td { background:#141414; }
  .champ-table tr.fc td { background:#09121e; color:#00D2BE; }
  .pts-bar-bg { background:#1a1a1a; border-radius:3px; height:5px; width:100%; min-width:60px; }
  .pts-bar-fill { border-radius:3px; height:5px; }
  /* Status badges */
  .badge { display:inline-block; padding:1px 6px; border-radius:3px;
           font-size:0.62rem; font-weight:700; letter-spacing:0.08em; margin-left:5px; }
  .b-dnf { background:#2a0a0a; color:#FF4444; }
  .b-dns { background:#2a2000; color:#FFAA00; }
  /* Track map layout */
  .map-driver-list { font-size:0.72rem; }
  .map-driver-row {
    display:flex; align-items:center; gap:6px;
    padding:4px 0; border-bottom:1px solid #141414;
    font-family:'JetBrains Mono',monospace;
  }
  .map-driver-dot { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
  /* Weather card */
  .wx-card {
    background:#0f0f0f; border:1px solid #1e1e1e; border-radius:5px;
    padding:12px 16px; font-size:0.8rem; color:#777;
  }
  /* Schedule card */
  .sched-card {
    background:#0f0f0f; border:1px solid #1e1e1e; border-radius:5px;
    padding:14px 16px; margin-bottom:10px;
  }
  .sched-round { color:#E10600; font-size:0.65rem; font-weight:700;
                 letter-spacing:0.15em; text-transform:uppercase; }
  .sched-name { color:#ddd; font-size:0.95rem; font-weight:600; margin:3px 0; }
  .sched-date { color:#555; font-size:0.75rem; }
  .sched-session { color:#888; font-size:0.72rem; padding:2px 0; }
  .countdown-box {
    background:#0f0f0f; border:1px solid #1e1e1e; border-radius:5px;
    padding:16px; text-align:center; margin-bottom:12px;
  }
  .countdown-val {
    font-family:'JetBrains Mono',monospace; font-size:2rem;
    font-weight:700; color:#E10600; line-height:1;
  }
  .countdown-lbl { color:#444; font-size:0.65rem; letter-spacing:0.15em;
                   text-transform:uppercase; margin-top:3px; }
  /* FIA messages */
  .fia-msg {
    background:#0c0c0c; border-left:3px solid #333; border-radius:0 4px 4px 0;
    padding:8px 12px; margin-bottom:6px; font-size:0.78rem; color:#777;
    line-height:1.5;
  }
  .fia-msg.safety { border-left-color:#FFD700; }
  .fia-msg.incident { border-left-color:#FF8C00; }
  .fia-msg.penalty { border-left-color:#E10600; }
  .fia-msg.info { border-left-color:#3671C6; }
  .fia-lap { color:#444; font-size:0.65rem; font-weight:600;
             text-transform:uppercase; letter-spacing:0.1em; margin-bottom:2px; }
  .fia-text { color:#999; }
  /* Telemetry legend */
  .tel-help {
    background:#0c0c0c; border:1px solid #1a1a1a; border-radius:5px;
    padding:12px 16px; font-size:0.78rem; color:#555; line-height:1.8;
    margin-bottom:0.8rem;
  }
  .tel-help b { color:#888; }
</style>
""", unsafe_allow_html=True)

# --- Constants ---------------------------------------------------------------
FEATURED_DRIVER = "COL"
FEATURED_COLOR  = "#00D2BE"

SPRINT_GPS = ["China", "Miami", "Austria", "United States", "Sao Paulo", "Qatar", "Las Vegas"]
SESSION_NORMAL = ["FP1", "FP2", "FP3", "Q", "R"]
SESSION_SPRINT = ["FP1", "SQ", "S", "Q", "R"]
SESSION_LABELS = {
    "FP1":"Free Practice 1","FP2":"Free Practice 2","FP3":"Free Practice 3",
    "Q":"Qualifying","R":"Race","SQ":"Sprint Qualifying","S":"Sprint",
}

TEAM_COLORS = {
    "Red Bull Racing":"#3671C6","Ferrari":"#E8002D","Mercedes":"#27F4D2",
    "McLaren":"#FF8000","Aston Martin":"#229971","Alpine":"#FF87BC",
    "Williams":"#64C4FF","RB":"#6692FF","Kick Sauber":"#52E252",
    "Haas F1 Team":"#B6BABD","Cadillac":"#CC0000","Andretti":"#CC0000",
}

DRIVER_NAMES = {
    "VER":"Max Verstappen","PER":"Sergio Perez","LEC":"Charles Leclerc",
    "SAI":"Carlos Sainz","HAM":"Lewis Hamilton","RUS":"George Russell",
    "NOR":"Lando Norris","PIA":"Oscar Piastri","ALO":"Fernando Alonso",
    "STR":"Lance Stroll","GAS":"Pierre Gasly","OCO":"Esteban Ocon",
    "ALB":"Alexander Albon","COL":"Franco Colapinto","SAR":"Logan Sargeant",
    "TSU":"Yuki Tsunoda","RIC":"Daniel Ricciardo","LAW":"Liam Lawson",
    "BOT":"Valtteri Bottas","ZHO":"Guanyu Zhou","HUL":"Nico Hulkenberg",
    "MAG":"Kevin Magnussen","BEA":"Oliver Bearman","ANT":"Kimi Antonelli",
    "DOO":"Jack Doohan","HAD":"Isack Hadjar","BOR":"Gabriel Bortoleto",
    "DRU":"Paul Aron","VER":"Max Verstappen",
}

# --- Helpers -----------------------------------------------------------------

def get_driver_name(code, session=None):
    if session is not None:
        try:
            info = session.get_driver(code)
            num  = str(info.get("DriverNumber", code))
            full = info.get("FullName", "")
            if full:
                return num, full
        except Exception:
            pass
    name = DRIVER_NAMES.get(code, code)
    return code, name


def fmt_lap(td):
    if td is None or (isinstance(td, float) and np.isnan(td)):
        return "--"
    try:
        t = td.total_seconds() if hasattr(td,"total_seconds") else float(td)
        m = int(t//60); s = t - m*60
        return f"{m}:{s:06.3f}"
    except Exception:
        return "--"


def fmt_sec(td):
    if td is None or (isinstance(td, float) and np.isnan(td)):
        return "--"
    try:
        s = td.total_seconds() if hasattr(td,"total_seconds") else float(td)
        return f"{s:.3f}"
    except Exception:
        return "--"


def team_color(team, session=None):
    try:
        return fastf1.plotting.get_team_color(team, session=session)
    except Exception:
        return TEAM_COLORS.get(team, "#666")


def classify_msg(text):
    t = text.upper()
    if any(w in t for w in ["SAFETY CAR","VSC","VIRTUAL"]):
        return "safety"
    if any(w in t for w in ["PENALTY","DRIVE THROUGH","STOP GO","DISQUALIF"]):
        return "penalty"
    if any(w in t for w in ["INCIDENT","NOTED","INVESTIGATION","REVIEWED"]):
        return "incident"
    return "info"

# --- Data loaders ------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_session(year, gp, stype):
    s = fastf1.get_session(year, gp, stype)
    s.load(telemetry=True, laps=True, weather=True, messages=True)
    return s


@st.cache_data(show_spinner=False)
def get_schedule(yr):
    try:
        df = fastf1.get_event_schedule(yr, include_testing=False)
        return df[df["RoundNumber"] > 0]
    except Exception:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def get_gp_names(yr):
    df = get_schedule(yr)
    if df.empty:
        return []
    return df["EventName"].tolist()


@st.cache_data(show_spinner=False)
def get_circuit_layout(_session):
    try:
        lap = _session.laps.pick_fastest()
        pos = lap.get_pos_data()[["X","Y"]].dropna()
        return pos
    except Exception:
        return pd.DataFrame(columns=["X","Y"])


@st.cache_data(show_spinner=False)
def get_driver_positions(_session):
    """Sample positions per driver per lap for the map."""
    records = []
    for drv in _session.drivers:
        laps = _session.laps.pick_drivers(drv)
        for _, lap in laps.iterrows():
            try:
                pos = lap.get_pos_data()[["X","Y","Time"]].dropna()
                if pos.empty:
                    continue
                step = max(1, len(pos)//60)
                s = pos.iloc[::step].copy()
                s["Driver"]    = drv
                s["LapNumber"] = lap["LapNumber"]
                try:
                    s["Team"] = _session.get_driver(drv)["TeamName"]
                except Exception:
                    s["Team"] = "Unknown"
                records.append(s)
            except Exception:
                continue
    if records:
        return pd.concat(records, ignore_index=True)
    return pd.DataFrame(columns=["X","Y","Time","Driver","LapNumber","Team"])


@st.cache_data(show_spinner=False)
def get_fastest_tel(_session, driver):
    try:
        drv_laps = _session.laps.pick_drivers(driver)
        if drv_laps.empty:
            return None, None
        lap = drv_laps.pick_fastest()
        if lap is None:
            return None, None
        tel = lap.get_car_data().add_distance()
        return tel, lap
    except Exception:
        return None, None


@st.cache_data(show_spinner=False)
def build_timing_df(_session):
    rows = []
    for drv in _session.drivers:
        dlaps = _session.laps.pick_drivers(drv)
        if dlaps.empty:
            continue
        try:
            info = _session.get_driver(drv)
        except Exception:
            info = {}
        try:
            fastest = dlaps.pick_fastest()
        except Exception:
            fastest = None

        status = ""
        try:
            last = dlaps.iloc[-1]
            if pd.isna(last.get("LapTime")) and len(dlaps) < 3:
                status = "DNS"
            elif pd.isna(last.get("LapTime")) and len(dlaps) >= 3:
                status = "DNF"
        except Exception:
            pass

        # Build minisector colours (split lap into 5 mini-chunks by S1/S2/S3 availability)
        ms_colors = []
        try:
            if fastest is not None:
                session_laps = _session.laps.pick_quicklaps()
                for sec in ["Sector1Time","Sector2Time","Sector3Time"]:
                    sv = fastest.get(sec)
                    if sv is None or pd.isna(sv):
                        ms_colors.extend(["w","w"])
                        continue
                    ses_best = session_laps[sec].min()
                    try:
                        drv_laps_q = dlaps.pick_quicklaps()
                        drv_best   = drv_laps_q[sec].min()
                    except Exception:
                        drv_best = sv
                    if sv == ses_best:
                        ms_colors.extend(["p","p"])
                    elif sv == drv_best:
                        ms_colors.extend(["g","g"])
                    else:
                        ms_colors.extend(["y","y"])
        except Exception:
            ms_colors = ["w"]*6

        rows.append({
            "Driver":   drv,
            "Number":   info.get("DriverNumber", drv),
            "FullName": info.get("FullName", drv),
            "Team":     info.get("TeamName", "Unknown"),
            "LapTime":  fastest["LapTime"]     if fastest is not None else None,
            "S1":       fastest["Sector1Time"] if fastest is not None else None,
            "S2":       fastest["Sector2Time"] if fastest is not None else None,
            "S3":       fastest["Sector3Time"] if fastest is not None else None,
            "Speed":    fastest["SpeedI1"]     if fastest is not None else None,
            "Status":   status,
            "MiniSecs": ms_colors,
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df.sort_values("LapTime", inplace=True, na_position="last")
    df.reset_index(drop=True, inplace=True)
    df.insert(0, "Pos", range(1, len(df)+1))

    ref = df["LapTime"].iloc[0] if not df.empty else None
    def delta(lt):
        if lt is None or ref is None: return "--"
        try:
            d = lt.total_seconds() - ref.total_seconds()
            return "LEADER" if d == 0 else f"+{d:.3f}"
        except Exception:
            return "--"
    df["Delta"] = df["LapTime"].apply(delta)

    for sec, col in [("S1","Sector1Time"),("S2","Sector2Time"),("S3","Sector3Time")]:
        valid = df[sec].dropna()
        if valid.empty:
            df[sec+"F"] = "Y"
            continue
        best = valid.min()
        df[sec+"F"] = df[sec].apply(
            lambda v: "P" if pd.notna(v) and v==best else ("G" if pd.notna(v) else "Y")
        )
    return df


@st.cache_data(show_spinner=False)
def fetch_standings(year, round_num):
    drivers, constructors = [], []
    base = "https://api.jolpi.ca/ergast/f1"
    try:
        r = requests.get(f"{base}/{year}/{round_num}/driverStandings", timeout=8)
        sl = r.json().get("MRData",{}).get("StandingsTable",{}).get("StandingsLists",[])
        if sl:
            for s in sl[0].get("DriverStandings",[]):
                drivers.append({
                    "Pos":    int(s.get("position",0)),
                    "Driver": s["Driver"].get("familyName",""),
                    "Given":  s["Driver"].get("givenName",""),
                    "Code":   s["Driver"].get("code",""),
                    "Team":   s["Constructors"][0]["name"] if s.get("Constructors") else "--",
                    "Points": float(s.get("points",0)),
                    "Wins":   int(s.get("wins",0)),
                })
    except Exception:
        pass
    try:
        r = requests.get(f"{base}/{year}/{round_num}/constructorStandings", timeout=8)
        sl = r.json().get("MRData",{}).get("StandingsTable",{}).get("StandingsLists",[])
        if sl:
            for s in sl[0].get("ConstructorStandings",[]):
                constructors.append({
                    "Pos":    int(s.get("position",0)),
                    "Name":   s["Constructor"].get("name",""),
                    "Points": float(s.get("points",0)),
                    "Wins":   int(s.get("wins",0)),
                })
    except Exception:
        pass
    return drivers, constructors


@st.cache_data(show_spinner=False)
def get_round_num(year, gp):
    try:
        df = get_schedule(year)
        m = df[df["EventName"].str.contains(gp.split()[0], case=False, na=False)]
        if not m.empty:
            return int(m.iloc[0]["RoundNumber"])
    except Exception:
        pass
    return 1

# --- Map builder -------------------------------------------------------------

def build_map_figure(circuit_xy, all_pos, session, lap_num):
    fig = go.Figure()

    # Track outline
    if not circuit_xy.empty:
        fig.add_trace(go.Scatter(
            x=circuit_xy["X"], y=circuit_xy["Y"], mode="lines",
            line=dict(color="#1e1e1e", width=12),
            hoverinfo="skip", showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=circuit_xy["X"], y=circuit_xy["Y"], mode="lines",
            line=dict(color="#333", width=7),
            hoverinfo="skip", showlegend=False
        ))

    lap_data = all_pos[all_pos["LapNumber"] == lap_num]
    latest   = lap_data.sort_values("Time").groupby("Driver").tail(1)

    driver_rows = []
    for _, row in latest.iterrows():
        drv    = row["Driver"]
        team   = row.get("Team","Unknown")
        color  = team_color(team, session)
        is_col = drv == FEATURED_DRIVER
        try:
            info = session.get_driver(drv)
            num  = str(info.get("DriverNumber", drv))
        except Exception:
            num = drv

        driver_rows.append({"drv": drv, "num": num, "color": color, "is_col": is_col})

        fig.add_trace(go.Scatter(
            x=[row["X"]], y=[row["Y"]],
            mode="markers+text",
            marker=dict(
                color=FEATURED_COLOR if is_col else color,
                size=18 if is_col else 9,
                symbol="star" if is_col else "circle",
                line=dict(color="#fff" if is_col else color, width=2 if is_col else 0),
            ),
            text=[num], textposition="top center",
            textfont=dict(color=FEATURED_COLOR if is_col else "#ccc", size=9 if is_col else 7),
            name=num, showlegend=False,
            hovertemplate=f"<b>{drv}</b> ({num})<br>{team}<extra></extra>",
        ))

    frames = []
    if not lap_data.empty:
        all_times = lap_data["Time"].sort_values().unique()
        step = max(1, len(all_times)//45)
        for t in all_times[::step]:
            fdata = [
                go.Scatter(x=circuit_xy["X"] if not circuit_xy.empty else [],
                           y=circuit_xy["Y"] if not circuit_xy.empty else [],
                           mode="lines", line=dict(color="#1e1e1e", width=12),
                           hoverinfo="skip", showlegend=False),
                go.Scatter(x=circuit_xy["X"] if not circuit_xy.empty else [],
                           y=circuit_xy["Y"] if not circuit_xy.empty else [],
                           mode="lines", line=dict(color="#333", width=7),
                           hoverinfo="skip", showlegend=False),
            ]
            for drow in driver_rows:
                drv = drow["drv"]
                dd  = lap_data[lap_data["Driver"]==drv]
                pt  = dd[dd["Time"]<=t]
                pos = pt.iloc[-1] if not pt.empty else dd.iloc[0]
                fdata.append(go.Scatter(
                    x=[pos["X"]], y=[pos["Y"]], mode="markers+text",
                    marker=dict(
                        color=FEATURED_COLOR if drow["is_col"] else drow["color"],
                        size=18 if drow["is_col"] else 9,
                        symbol="star" if drow["is_col"] else "circle",
                        line=dict(color="#fff" if drow["is_col"] else drow["color"],
                                  width=2 if drow["is_col"] else 0),
                    ),
                    text=[drow["num"]], textposition="top center",
                    textfont=dict(color=FEATURED_COLOR if drow["is_col"] else "#ccc",
                                  size=9 if drow["is_col"] else 7),
                    showlegend=False, name=drow["num"],
                    hovertemplate=f"<b>{drv}</b><extra></extra>",
                ))
            frames.append(go.Frame(data=fdata, name=str(t)))

    fig.frames = frames

    fig.update_layout(
        paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=50),
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        height=480,
        updatemenus=[dict(
            type="buttons", showactive=False,
            y=-0.1, x=0.5, xanchor="center",
            buttons=[
                dict(label="  Play  ", method="animate",
                     args=[None, {"frame":{"duration":70,"redraw":True},
                                  "fromcurrent":True,"transition":{"duration":0}}]),
                dict(label="  Pause  ", method="animate",
                     args=[[None], {"frame":{"duration":0,"redraw":False},
                                    "mode":"immediate","transition":{"duration":0}}]),
            ],
            font=dict(color="#ccc", size=11),
            bgcolor="#1a1a1a", bordercolor="#2a2a2a", pad={"t":5},
        )],
        sliders=[dict(
            active=0,
            steps=[dict(method="animate",
                        args=[[f.name], {"frame":{"duration":70,"redraw":True},
                                         "mode":"immediate","transition":{"duration":0}}],
                        label="") for f in frames],
            x=0.0, y=-0.06, len=1.0,
            currentvalue=dict(visible=False),
            bgcolor="#1a1a1a", bordercolor="#222",
        )] if frames else [],
    )
    return fig, driver_rows

# --- Telemetry comparison -----------------------------------------------------

def build_tel_fig(session, drv1, drv2):
    tel1, _ = get_fastest_tel(session, drv1)
    tel2, _ = get_fastest_tel(session, drv2)

    channels = ["Speed","Throttle","Brake","RPM","nGear"]
    ylabels  = ["Speed (km/h)","Throttle (%)","Brake","RPM","Gear"]

    try:
        c1 = team_color(session.get_driver(drv1)["TeamName"], session)
    except Exception:
        c1 = FEATURED_COLOR if drv1==FEATURED_DRIVER else "#E10600"
    try:
        c2 = team_color(session.get_driver(drv2)["TeamName"], session)
    except Exception:
        c2 = "#888"
    if drv1==FEATURED_DRIVER: c1 = FEATURED_COLOR
    if drv2==FEATURED_DRIVER: c2 = FEATURED_COLOR

    n1 = get_driver_name(drv1, session)
    n2 = get_driver_name(drv2, session)
    label1 = f"{n1[0]} - {n1[1]}"
    label2 = f"{n2[0]} - {n2[1]}"

    fig = make_subplots(rows=len(channels), cols=1, shared_xaxes=True,
                        subplot_titles=ylabels, vertical_spacing=0.035)

    has_data = False
    for i, ch in enumerate(channels, 1):
        if tel1 is not None and ch in tel1.columns:
            fig.add_trace(go.Scatter(
                x=tel1["Distance"], y=tel1[ch],
                line=dict(color=c1, width=1.8),
                name=label1, legendgroup=drv1, showlegend=(i==1),
            ), row=i, col=1)
            has_data = True
        if tel2 is not None and ch in tel2.columns:
            fig.add_trace(go.Scatter(
                x=tel2["Distance"], y=tel2[ch],
                line=dict(color=c2, width=1.8, dash="dot"),
                name=label2, legendgroup=drv2, showlegend=(i==1),
            ), row=i, col=1)
            has_data = True

    fig.update_layout(
        paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a", height=680,
        legend=dict(bgcolor="#111", bordercolor="#1e1e1e", borderwidth=1,
                    font=dict(color="#ccc", size=11), orientation="h",
                    x=0.5, xanchor="center", y=1.02),
        margin=dict(l=55, r=15, t=45, b=35),
        font=dict(color="#666", size=9),
    )
    for i in range(1, len(channels)+1):
        fig.update_xaxes(gridcolor="#141414", zeroline=False, row=i, col=1)
        fig.update_yaxes(gridcolor="#141414", zeroline=False, row=i, col=1)
    fig.update_xaxes(title_text="Distance (m)", row=len(channels), col=1)

    return fig, has_data

# --- Lap time chart ----------------------------------------------------------

def build_lap_chart(session, driver):
    try:
        laps = session.laps.pick_drivers(driver).pick_quicklaps()
    except Exception:
        return go.Figure()
    try:
        color = team_color(session.get_driver(driver)["TeamName"], session)
    except Exception:
        color = FEATURED_COLOR if driver==FEATURED_DRIVER else "#E10600"
    fig = go.Figure()
    if not laps.empty:
        ts = laps["LapTime"].dt.total_seconds()
        fig.add_trace(go.Scatter(
            x=laps["LapNumber"], y=ts, mode="lines+markers",
            line=dict(color=color, width=2), marker=dict(size=4, color=color),
            hovertemplate="Lap %{x} - %{customdata}<extra></extra>",
            customdata=[fmt_lap(t) for t in laps["LapTime"]],
        ))
        bi = ts.idxmin()
        fig.add_annotation(x=laps.loc[bi,"LapNumber"], y=ts[bi],
                           text=f"BEST {fmt_lap(laps.loc[bi,'LapTime'])}",
                           showarrow=True, arrowhead=2,
                           font=dict(color="#CC44FF", size=9), arrowcolor="#CC44FF")
    fig.update_layout(
        paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a", height=240,
        margin=dict(l=45,r=10,t=10,b=35),
        xaxis=dict(title="Lap", gridcolor="#141414", color="#444", title_font_size=10),
        yaxis=dict(title="Sec", gridcolor="#141414", color="#444", title_font_size=10),
        font=dict(color="#666"), showlegend=False,
    )
    return fig

# --- Weather -----------------------------------------------------------------

def render_weather(session):
    st.markdown("<div class='sh'>Track Weather</div>", unsafe_allow_html=True)
    try:
        wx = session.weather_data
        if wx is None or wx.empty:
            st.info("No weather data for this session.")
            return
        last = wx.iloc[-1]
        cols = st.columns(5)
        items = [
            ("Air Temp", f"{last.get('AirTemp', '--'):.1f} C"),
            ("Track Temp", f"{last.get('TrackTemp', '--'):.1f} C"),
            ("Humidity", f"{last.get('Humidity', '--'):.0f} %"),
            ("Wind Speed", f"{last.get('WindSpeed', '--'):.1f} m/s"),
            ("Rainfall", "Yes" if last.get('Rainfall', False) else "No"),
        ]
        for col, (lbl, val) in zip(cols, items):
            with col:
                st.markdown(f"""
                <div class="metric-tile">
                  <div class="val">{val}</div>
                  <div class="lbl">{lbl}</div>
                </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.info(f"Weather data unavailable: {e}")

# --- FIA Messages -------------------------------------------------------------

def render_fia_messages(session):
    st.markdown("<div class='sh'>Race Control / FIA Messages</div>", unsafe_allow_html=True)
    try:
        msgs = session.race_control_messages
        if msgs is None or msgs.empty:
            st.info("No race control messages for this session.")
            return
        # Show latest 30, newest first
        msgs_sorted = msgs.sort_values("Time", ascending=False).head(30)
        for _, row in msgs_sorted.iterrows():
            text     = str(row.get("Message", ""))
            lap      = row.get("Lap", "")
            category = row.get("Category", "")
            css_cls  = classify_msg(text + " " + str(category))
            lap_str  = f"Lap {int(lap)}" if pd.notna(lap) and lap != "" else ""
            st.markdown(f"""
            <div class="fia-msg {css_cls}">
              <div class="fia-lap">{lap_str}</div>
              <div class="fia-text">{text}</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.info(f"Race control messages unavailable: {e}")

# --- Schedule ----------------------------------------------------------------

def render_schedule():
    st.markdown("<div class='sh'>2025 Season Schedule</div>", unsafe_allow_html=True)
    try:
        df = get_schedule(2025)
        if df.empty:
            st.info("Schedule unavailable.")
            return

        now = datetime.now(timezone.utc)

        # Find next event
        next_events = []
        for _, ev in df.iterrows():
            try:
                date_col = ev.get("EventDate") or ev.get("Session5Date") or ev.get("Session1Date")
                if date_col is None:
                    continue
                if hasattr(date_col, "tzinfo") and date_col.tzinfo is None:
                    import pytz
                    date_col = pytz.utc.localize(date_col)
                if date_col > now:
                    next_events.append(ev)
            except Exception:
                continue

        if next_events:
            nev = next_events[0]
            try:
                date_col = nev.get("EventDate") or nev.get("Session5Date") or nev.get("Session1Date")
                if hasattr(date_col, "tzinfo") and date_col.tzinfo is None:
                    import pytz
                    date_col = pytz.utc.localize(date_col)
                delta = date_col - now
                days  = delta.days
                hours = (delta.seconds // 3600)
                mins  = (delta.seconds % 3600) // 60

                st.markdown(f"""
                <div style="margin-bottom:10px;">
                  <div style="color:#555; font-size:0.65rem; letter-spacing:0.15em;
                              text-transform:uppercase; margin-bottom:6px;">
                    Next event: <b style="color:#E10600">{nev.get('EventName','')}</b>
                  </div>
                  <div style="display:flex; gap:10px;">
                    <div class="countdown-box" style="flex:1">
                      <div class="countdown-val">{days}</div>
                      <div class="countdown-lbl">Days</div>
                    </div>
                    <div class="countdown-box" style="flex:1">
                      <div class="countdown-val">{hours}</div>
                      <div class="countdown-lbl">Hours</div>
                    </div>
                    <div class="countdown-box" style="flex:1">
                      <div class="countdown-val">{mins}</div>
                      <div class="countdown-lbl">Min</div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)
            except Exception:
                pass

        # Show upcoming 6 events
        shown = 0
        for _, ev in df.iterrows():
            if shown >= 8:
                break
            name  = ev.get("EventName","")
            round_n = ev.get("RoundNumber","")
            country = ev.get("Country","")

            # Build session list
            sessions_html = ""
            for i in range(1, 6):
                sname = ev.get(f"Session{i}", "")
                sdate = ev.get(f"Session{i}Date")
                if sname and sdate is not None:
                    try:
                        sdate_str = pd.Timestamp(sdate).strftime("%a %b %d")
                        sessions_html += f"<div class='sched-session'>{sdate_str} &middot; {sname}</div>"
                    except Exception:
                        sessions_html += f"<div class='sched-session'>{sname}</div>"

            try:
                ev_date = ev.get("EventDate")
                date_str = pd.Timestamp(ev_date).strftime("%B %d") if ev_date else ""
            except Exception:
                date_str = ""

            is_next = next_events and ev.get("EventName") == next_events[0].get("EventName")
            border_style = "border-left:3px solid #E10600;" if is_next else ""

            st.markdown(f"""
            <div class="sched-card" style="{border_style}">
              <div class="sched-round">Round {round_n} &middot; {country}</div>
              <div class="sched-name">{name}</div>
              <div class="sched-date">{date_str}</div>
              <div style="margin-top:6px;">{sessions_html}</div>
            </div>""", unsafe_allow_html=True)
            shown += 1

    except Exception as e:
        st.info(f"Schedule unavailable: {e}")

# --- Render: Featured Driver --------------------------------------------------

def render_featured(session):
    st.markdown("""
    <div class="col-card">
      <div style="color:#00D2BE;font-size:0.9rem;font-weight:700;
                  letter-spacing:0.2em;text-transform:uppercase;">
        Featured Driver Monitor &middot; Franco Colapinto &middot; #43
      </div>
    </div>""", unsafe_allow_html=True)

    try:
        laps = session.laps.pick_drivers(FEATURED_DRIVER)
        if laps.empty:
            st.info("Colapinto (COL) has no data in this session. Try 2024 - Italian GP - Race.")
            return
        qlaps = laps.pick_quicklaps()
        fastest = laps.pick_fastest() if not laps.empty else None
        last    = laps.iloc[-1] if not laps.empty else None

        cols = st.columns(7)
        vals = [
            ("Last Lap",  fmt_lap(last["LapTime"])    if last is not None else "--"),
            ("S1",        fmt_sec(last["Sector1Time"])if last is not None else "--"),
            ("S2",        fmt_sec(last["Sector2Time"])if last is not None else "--"),
            ("S3",        fmt_sec(last["Sector3Time"])if last is not None else "--"),
            ("Best Lap",  fmt_lap(fastest["LapTime"]) if fastest is not None else "--"),
            ("Lap #",     str(int(last["LapNumber"])) if last is not None else "--"),
            ("Compound",  str(last["Compound"])        if last is not None else "--"),
        ]
        for c, (l, v) in zip(cols, vals):
            with c:
                st.markdown(f"""
                <div class="metric-tile">
                  <div class="val">{v}</div><div class="lbl">{l}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div class='sh'>Sector Performance</div>", unsafe_allow_html=True)
        if not qlaps.empty:
            scols = st.columns(3)
            slaps = session.laps.pick_quicklaps()
            for i, (sc, sec) in enumerate(zip(scols, ["Sector1Time","Sector2Time","Sector3Time"])):
                try:
                    db = qlaps[sec].min()
                    sb = slaps[sec].min()
                    clr = "#CC44FF" if db==sb else "#39FF14"
                    badge = "SESSION BEST" if db==sb else "PERSONAL BEST"
                except Exception:
                    db = None; clr = "#FFD700"; badge = ""
                with sc:
                    st.markdown(f"""
                    <div class="metric-tile">
                      <div class="val" style="color:{clr}">{fmt_sec(db)}</div>
                      <div class="lbl">S{i+1} &middot; {badge}</div>
                    </div>""", unsafe_allow_html=True)

        if not qlaps.empty:
            st.markdown("<div class='sh'>Lap Time Chart</div>", unsafe_allow_html=True)
            st.plotly_chart(build_lap_chart(session, FEATURED_DRIVER), use_container_width=True)

        render_weather(session)

    except Exception as e:
        st.warning(f"Featured driver panel error: {e}")

# --- Render: Timing Tower -----------------------------------------------------

def render_timing(session):
    st.markdown("<div class='sh'>Timing Tower</div>", unsafe_allow_html=True)
    df = build_timing_df(session)
    if df.empty:
        st.info("No timing data.")
        return

    flag_cls = {"P":"sp","G":"sg","Y":"sy"}
    ms_cls   = {"p":"ms-p","g":"ms-g","y":"ms-y","w":"ms-w"}

    rows_html = ""
    for _, row in df.iterrows():
        is_col = row["Driver"] == FEATURED_DRIVER
        tr_cls = "featured" if is_col else ("dnf-row" if row.get("Status") in ("DNF","DNS") else "")
        s1c = flag_cls.get(row.get("S1F","Y"),"sy")
        s2c = flag_cls.get(row.get("S2F","Y"),"sy")
        s3c = flag_cls.get(row.get("S3F","Y"),"sy")
        spd = f'{row["Speed"]:.0f}' if pd.notna(row.get("Speed")) else "--"
        star = "* " if is_col else ""

        status_badge = ""
        if row.get("Status") == "DNF":
            status_badge = '<span class="badge b-dnf">DNF</span>'
        elif row.get("Status") == "DNS":
            status_badge = '<span class="badge b-dns">DNS</span>'

        # Minisector bar
        ms = row.get("MiniSecs", ["w"]*6)
        ms_divs = "".join(f'<div class="{ms_cls.get(c,"ms-w")}"></div>' for c in ms)
        ms_bar  = f'<div class="ms-row">{ms_divs}</div>'

        drv_disp = f"{row['Number']} - {row['FullName']}"

        rows_html += f"""
        <tr class="{tr_cls}">
          <td><b>{row['Pos']}</b></td>
          <td><b>{star}{drv_disp}</b>{status_badge}</td>
          <td style="color:#444;font-size:0.7rem">{row['Team'][:16]}</td>
          <td>{fmt_lap(row['LapTime'])}</td>
          <td><span class="{s1c}">{fmt_sec(row['S1'])}</span></td>
          <td><span class="{s2c}">{fmt_sec(row['S2'])}</span></td>
          <td><span class="{s3c}">{fmt_sec(row['S3'])}</span></td>
          <td>{ms_bar}</td>
          <td>{spd}</td>
          <td>{row['Delta']}</td>
        </tr>"""

    st.markdown(f"""
    <div style="overflow-x:auto;">
    <table class="timing-table">
      <thead>
        <tr>
          <th>P</th><th>Driver</th><th>Team</th><th>Best Lap</th>
          <th>S1</th><th>S2</th><th>S3</th><th>Mini</th>
          <th>Trap</th><th>Delta</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:8px;font-size:0.68rem;color:#333;">
      <span class="sp">Purple</span> = Session best &nbsp;|&nbsp;
      <span class="sg">Green</span> = Personal best &nbsp;|&nbsp;
      <span class="sy">Yellow</span> = No improvement
    </div>""", unsafe_allow_html=True)

# --- Render: Circuit Map ------------------------------------------------------

def render_map(session):
    st.markdown("<div class='sh'>GPS Circuit Map</div>", unsafe_allow_html=True)

    with st.spinner("Loading position data..."):
        circuit_xy = get_circuit_layout(session)
        all_pos    = get_driver_positions(session)

    if all_pos.empty:
        st.warning("Position data is not available for this session type. "
                   "Try Race or Qualifying sessions which have full GPS data.")
        return

    max_lap = int(all_pos["LapNumber"].max())
    min_lap = int(all_pos["LapNumber"].min())

    map_col, list_col = st.columns([3, 1])

    with map_col:
        sel_lap = st.slider("Lap", min_value=min_lap, max_value=max_lap,
                            value=min_lap, step=1, key="map_slider")
        st.markdown("""
        <div style="font-size:0.72rem;color:#444;margin-bottom:6px;">
          Press <b style="color:#888">Play</b> to animate cars through the lap.
          Teal star = Franco Colapinto.
        </div>""", unsafe_allow_html=True)
        with st.spinner("Rendering map..."):
            fig, driver_rows = build_map_figure(circuit_xy, all_pos, session, sel_lap)
        st.plotly_chart(fig, use_container_width=True)

    with list_col:
        st.markdown("<div class='sh'>Drivers</div>", unsafe_allow_html=True)
        lap_data = all_pos[all_pos["LapNumber"] == sel_lap]
        latest   = lap_data.sort_values("Time").groupby("Driver").tail(1)
        for drow in driver_rows:
            drv = drow["drv"]
            is_col = drv == FEATURED_DRIVER
            color  = FEATURED_COLOR if is_col else drow["color"]
            try:
                info = session.get_driver(drv)
                num  = str(info.get("DriverNumber", drv))
                name = info.get("Abbreviation", drv)
            except Exception:
                num = drv; name = drv
            bold = "font-weight:700;" if is_col else ""
            st.markdown(f"""
            <div class="map-driver-row">
              <div class="map-driver-dot" style="background:{color};
                {'box-shadow:0 0 5px {color};' if is_col else ''}"></div>
              <span style="color:#555;min-width:18px;">{num}</span>
              <span style="color:{'#00D2BE' if is_col else '#888'};{bold}">{name}</span>
            </div>""", unsafe_allow_html=True)

# --- Render: Telemetry --------------------------------------------------------

def render_telemetry(session):
    st.markdown("<div class='sh'>Telemetry Comparison - Fastest Laps</div>",
                unsafe_allow_html=True)

    st.markdown("""
    <div class="tel-help">
      <b>Speed</b> = how fast the car goes (km/h) &nbsp;|&nbsp;
      <b>Throttle</b> = gas pedal 0-100% &nbsp;|&nbsp;
      <b>Brake</b> = brake pedal on/off &nbsp;|&nbsp;
      <b>RPM</b> = engine revolutions per minute &nbsp;|&nbsp;
      <b>Gear</b> = current gear (1-8).<br>
      Solid line = Driver A &nbsp;&mdash;&nbsp; Dotted line = Driver B
    </div>""", unsafe_allow_html=True)

    all_drivers = list(session.drivers)
    if len(all_drivers) < 2:
        st.info("Need at least 2 drivers.")
        return

    display_names = [f"{get_driver_name(d,session)[0]} - {get_driver_name(d,session)[1]}"
                     for d in all_drivers]

    d1_default = 0
    for i, d in enumerate(all_drivers):
        if d == FEATURED_DRIVER:
            d1_default = i; break

    d2_default = (d1_default+1) % len(all_drivers)

    c1, c2 = st.columns(2)
    with c1:
        s1 = st.selectbox("Driver A", display_names, index=d1_default, key="td1")
    with c2:
        s2 = st.selectbox("Driver B", display_names, index=d2_default, key="td2")

    drv1 = all_drivers[display_names.index(s1)]
    drv2 = all_drivers[display_names.index(s2)]

    if drv1 == drv2:
        st.warning("Select two different drivers.")
        return

    with st.spinner("Loading telemetry..."):
        fig, has_data = build_tel_fig(session, drv1, drv2)

    if not has_data:
        st.warning("Telemetry data could not be loaded for one or both drivers in this session. "
                   "Telemetry is most reliable for Race and Qualifying sessions.")
        return

    tel1, lap1 = get_fastest_tel(session, drv1)
    tel2, lap2 = get_fastest_tel(session, drv2)

    try:
        tc1 = team_color(session.get_driver(drv1)["TeamName"], session)
    except Exception:
        tc1 = FEATURED_COLOR if drv1==FEATURED_DRIVER else "#E10600"
    try:
        tc2 = team_color(session.get_driver(drv2)["TeamName"], session)
    except Exception:
        tc2 = "#888"
    if drv1==FEATURED_DRIVER: tc1=FEATURED_COLOR
    if drv2==FEATURED_DRIVER: tc2=FEATURED_COLOR

    m1, m2 = st.columns(2)
    with m1:
        lt = fmt_lap(lap1["LapTime"]) if lap1 is not None else "--"
        st.markdown(f"""
        <div class="metric-tile" style="border-left:3px solid {tc1};">
          <div class="val" style="color:{tc1}">{lt}</div>
          <div class="lbl">{s1} &middot; Fastest</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        lt = fmt_lap(lap2["LapTime"]) if lap2 is not None else "--"
        st.markdown(f"""
        <div class="metric-tile" style="border-left:3px solid {tc2};">
          <div class="val" style="color:{tc2}">{lt}</div>
          <div class="lbl">{s2} &middot; Fastest</div>
        </div>""", unsafe_allow_html=True)

    st.plotly_chart(fig, use_container_width=True)

# --- Render: Championship -----------------------------------------------------

def render_championship(year, gp):
    st.markdown("<div class='sh'>Championship Standings</div>", unsafe_allow_html=True)
    rn = get_round_num(year, gp)
    with st.spinner("Fetching standings..."):
        drivers, constructors = fetch_standings(year, rn)

    if not drivers and not constructors:
        st.info("Championship data not available. This may occur for very recent events "
                "or if the Jolpica API is unreachable.")
        return

    td, tc = st.tabs(["Drivers", "Constructors"])

    with td:
        if not drivers:
            st.info("No driver standings data.")
        else:
            max_pts = max(d["Points"] for d in drivers) or 1
            rows = ""
            for d in drivers:
                is_col = d.get("Code","") == FEATURED_DRIVER
                tr_cls = "fc" if is_col else ""
                pct    = int((d["Points"]/max_pts)*100)
                bc     = FEATURED_COLOR if is_col else "#E10600"
                star   = "* " if is_col else ""
                # Safely get team name, default to empty string if missing
                team_name = d.get("Team") or ""
                rows += f"""
                <tr class="{tr_cls}">
                  <td><b>{d['Pos']}</b></td>
                  <td><b>{star}{d.get('Given','')} {d['Driver']}</b></td>
                  <td style="color:#444;font-size:0.72rem">{team_name[:22]}</td>
                  <td>
                    <div style="display:flex;align-items:center;gap:8px;">
                      <span style="font-family:'JetBrains Mono',monospace;font-weight:600;
                                   color:{'#00D2BE' if is_col else '#ddd'};min-width:34px;">
                        {int(d['Points'])}
                      </span>
                      <div class="pts-bar-bg" style="flex:1">
                        <div class="pts-bar-fill" style="width:{pct}%;background:{bc};"></div>
                      </div>
                    </div>
                  </td>
                  <td style="color:#444">{d['Wins']}</td>
                </tr>"""
            st.markdown(f"""
            <table class="champ-table">
              <thead><tr>
                <th>P</th><th>Driver</th><th>Team</th><th>Points</th><th>W</th>
              </tr></thead>
              <tbody>{rows}</tbody>
            </table>""", unsafe_allow_html=True)

    with tc:
        if not constructors:
            st.info("No constructor standings data.")
        else:
            max_pts = max(c["Points"] for c in constructors) or 1
            rows = ""
            for c in constructors:
                pct  = int((c["Points"]/max_pts)*100)
                name = c.get("Name") or ""
                bc   = TEAM_COLORS.get(name, "#E10600")
                rows += f"""
                <tr>
                  <td><b>{c['Pos']}</b></td>
                  <td><b>{name}</b></td>
                  <td>
                    <div style="display:flex;align-items:center;gap:8px;">
                      <span style="font-family:'JetBrains Mono',monospace;font-weight:600;
                                   color:#ddd;min-width:34px;">{int(c['Points'])}</span>
                      <div class="pts-bar-bg" style="flex:1">
                        <div class="pts-bar-fill" style="width:{pct}%;background:{bc};"></div>
                      </div>
                    </div>
                  </td>
                  <td style="color:#444">{c['Wins']}</td>
                </tr>"""
            st.markdown(f"""
            <table class="champ-table">
              <thead><tr>
                <th>P</th><th>Constructor</th><th>Points</th><th>W</th>
              </tr></thead>
              <tbody>{rows}</tbody>
            </table>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top:8px;font-size:0.68rem;color:#333;">
      Standings after Round {rn} &middot; {year}
    </div>""", unsafe_allow_html=True)

# --- Sidebar -----------------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center;padding:12px 0 18px;'>
          <div style='color:#E10600;font-size:1rem;font-weight:700;
                      letter-spacing:0.2em;text-transform:uppercase;'>
            F1 TELEMETRY
          </div>
          <div style='color:#2a2a2a;font-size:0.62rem;letter-spacing:0.15em;
                      font-weight:500;'>DASHBOARD</div>
        </div>""", unsafe_allow_html=True)
        st.divider()

        year    = st.selectbox("Season", list(range(2026, 2018, -1)), index=0)
        gp_list = get_gp_names(year)

        if not gp_list:
            st.error("Could not load schedule.")
            return None, None, None

        default_idx = 0
        for i, g in enumerate(gp_list):
            if "italian" in g.lower():
                default_idx = i; break

        gp = st.selectbox("Grand Prix", gp_list, index=default_idx)

        is_sprint  = any(s.lower() in gp.lower() for s in SPRINT_GPS)
        s_opts     = SESSION_SPRINT if is_sprint else SESSION_NORMAL
        s_labels   = [f"{k} - {SESSION_LABELS[k]}" for k in s_opts]
        sel        = st.selectbox("Session", s_labels)
        stype      = sel.split(" - ")[0]

        st.divider()
        st.markdown("""
        <div style='color:#2a2a2a;font-size:0.62rem;letter-spacing:0.08em;
                    line-height:2.2;font-weight:500;'>
          DATA<br><span style='color:#444;'>FastF1 + Jolpica</span><br>
          CACHE<br><span style='color:#444;'>./cache/</span>
        </div>""", unsafe_allow_html=True)

        return year, gp, stype

# --- Main ---------------------------------------------------------------------

def main():
    st.markdown("""
    <div class="f1-header">
      <div>
        <div style='color:#E10600;font-size:1.5rem;font-weight:700;letter-spacing:0.05em;'>
          FORMULA 1
        </div>
        <div style='color:#444;font-size:0.65rem;letter-spacing:0.25em;font-weight:500;'>
          TELEMETRY DASHBOARD
        </div>
      </div>
      <div style='color:#333;font-size:0.7rem;font-weight:500;letter-spacing:0.1em;'>
        FastF1 &middot; Streamlit
      </div>
    </div>""", unsafe_allow_html=True)

    year, gp, stype = render_sidebar()
    if year is None:
        return

    slabel = SESSION_LABELS.get(stype, stype)
    st.markdown(f"""
    <div style='color:#666;font-size:0.9rem;font-weight:500;margin-bottom:0.8rem;'>
      {year} &middot; {gp} &middot; {slabel}
    </div>""", unsafe_allow_html=True)

    load_btn    = st.button("Load Session Data", type="primary")
    session_key = f"{year}_{gp}_{stype}"

    if "session_loaded" not in st.session_state:
        st.session_state.session_loaded = False
        st.session_state.session_key    = None

    already = (st.session_state.session_loaded and
               st.session_state.session_key == session_key)

    if load_btn or already:
        with st.spinner(f"Loading {gp} {stype} {year}..."):
            try:
                session = load_session(year, gp, stype)
                st.session_state._session      = session
                st.session_state.session_loaded = True
                st.session_state.session_key    = session_key
            except Exception as e:
                st.error(f"Failed to load session: {e}")
                st.info("FastF1 only has data for completed sessions. "
                        "Check your internet connection.")
                return

        session = st.session_state._session

        t1,t2,t3,t4,t5,t6,t7 = st.tabs([
            "Featured Driver",
            "Timing Tower",
            "Circuit Map",
            "Telemetry",
            "Championship",
            "FIA Messages",
            "Schedule",
        ])
        with t1: render_featured(session)
        with t2: render_timing(session)
        with t3: render_map(session)
        with t4: render_telemetry(session)
        with t5: render_championship(year, gp)
        with t6: render_fia_messages(session)
        with t7: render_schedule()

    else:
        st.markdown("""
        <div class="info-box">
          <b>Welcome to the F1 Telemetry Dashboard</b><br><br>
          1. Select <b>Season</b>, <b>Grand Prix</b> and <b>Session</b> in the sidebar.<br>
          2. Click <b>Load Session Data</b>.<br>
          3. Data is cached in <code>./cache/</code> so future loads are instant.<br><br>
          <b>Recommended start:</b> 2024 &mdash; Italian Grand Prix &mdash; R (Race)<br>
          This is Franco Colapinto's F1 debut with Williams.
        </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        for col, (title, sub, desc) in zip([c1,c2,c3],[
            ("Colapinto Debut", "2024 - Italian GP - Race",     "Williams debut"),
            ("Baku 2024",       "2024 - Azerbaijan GP - Race",  "Street circuit"),
            ("Monaco 2023",     "2023 - Monaco GP - Qualifying","Qualy classic"),
        ]):
            with col:
                st.markdown(f"""
                <div class="metric-tile" style="text-align:left;padding:16px;">
                  <div style="color:#ccc;font-weight:600;margin-bottom:4px;">{title}</div>
                  <div style="color:#E10600;font-size:0.7rem;margin-bottom:6px;
                              font-family:'JetBrains Mono',monospace;">{sub}</div>
                  <div style="color:#333;font-size:0.76rem;">{desc}</div>
                </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
