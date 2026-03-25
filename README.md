# F1 Telemetry Dashboard

Un dashboard interactivo para visualizar datos de telemetría de Fórmula 1 usando FastF1 y Streamlit.

## Características

- **Monitor de Piloto Destacado**: Visualiza estadísticas detalladas de un piloto seleccionado
- **Torre de Tiempos**: Tabla de posiciones con tiempos de vuelta, sectores y deltas
- **Mapa del Circuito GPS**: Visualización animada de la posición de los coches en tiempo real
- **Comparación de Telemetría**: Gráficos de velocidad, acelerador, frenos, RPM y cambios de marcha
- **Campeonato**: Clasificaciones de pilotos y constructores
- **Mensajes FIA**: Control de carrera y mensajes de la FIA
- **Calendario de la Temporada**: Próximas carreras con cuenta regresiva

## Novedades Recientes

- **Selección Dinámica de Pilotos**: El piloto destacado ahora se selecciona de la lista completa de pilotos participantes en la sesión específica, permitiendo elegir a todos los pilotos del año actual en lugar de una lista fija.

## Tecnologías

- **Streamlit**: Framework web para la interfaz
- **FastF1**: Librería para datos de F1
- **Plotly**: Gráficos interactivos
- **Pandas**: Manipulación de datos
- **Requests**: API para clasificaciones del campeonato

## Instalación

1. Clona el repositorio:
```bash
git clone <url-del-repositorio>
cd f1_dashboard
```

2. Crea un entorno virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

Ejecuta la aplicación:
```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador. Selecciona un Gran Premio y sesión para cargar los datos.

## Estructura del Proyecto

- `app.py`: Archivo principal de la aplicación
- `requirements.txt`: Dependencias de Python
- `cache/`: Directorio para cache de datos FastF1
- `README.md`: Este archivo

## Datos

Los datos se obtienen de:
- **FastF1**: Telemetría, vueltas, clima, mensajes
- **Jolpica API**: Clasificaciones del campeonato

## Contribución

Si encuentras errores o tienes sugerencias, por favor abre un issue o envía un pull request.

## Licencia

Este proyecto es de código abierto. Consulta el archivo LICENSE para más detalles.

# ============================================================
# CONSTANTS
# ============================================================
FEATURED_DRIVER = "COL"
FEATURED_COLOR  = "#00D2BE"
LIVE_REFRESH_S  = 3

SPRINT_GPS = ["China","Miami","Austria","United States","Sao Paulo","Qatar","Las Vegas"]
SESSION_NORMAL = ["FP1","FP2","FP3","Q","R"]
SESSION_SPRINT = ["FP1","SQ","S","Q","R"]
SESSION_LABELS = {
    "FP1":"Free Practice 1","FP2":"Free Practice 2","FP3":"Free Practice 3",
    "Q":"Qualifying","R":"Race","SQ":"Sprint Qualifying","S":"Sprint",
}
TEAM_COLORS = {
    "Red Bull Racing":"#3671C6","Ferrari":"#E8002D","Mercedes":"#27F4D2",
    "McLaren":"#FF8000","Aston Martin":"#229971","Alpine":"#FF87BC",
    "Williams":"#64C4FF","RB":"#6692FF","Kick Sauber":"#52E252",
    "Haas F1 Team":"#B6BABD","Cadillac":"#CC0000",
}

# ============================================================
# HELPERS
# ============================================================

def get_driver_info(drv, session):
    try:
        info = session.get_driver(drv)
        num  = str(info.get("DriverNumber", drv))
        full = str(info.get("FullName", drv))
        abbr = str(info.get("Abbreviation", drv))
        team = str(info.get("TeamName", "Unknown"))
        return num, full, abbr, team
    except Exception:
        return str(drv), str(drv), str(drv), "Unknown"


def fmt_lap(td):
    if td is None or (isinstance(td, float) and np.isnan(td)):
        return "--"
    try:
        t = td.total_seconds() if hasattr(td,"total_seconds") else float(td)
        m = int(t//60); s = t-m*60
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


def tcolor(team, session=None):
    try:
        return fastf1.plotting.get_team_color(team, session=session)
    except Exception:
        return TEAM_COLORS.get(str(team), "#555")


def classify_msg(text):
    t = text.upper()
    if any(w in t for w in ["SAFETY CAR","VSC","VIRTUAL SAFETY"]):
        return "safety"
    if any(w in t for w in ["PENALTY","DRIVE THROUGH","STOP GO","DISQUALIF"]):
        return "penalty"
    if any(w in t for w in ["INCIDENT","NOTED","INVESTIGATION","REVIEWED"]):
        return "incident"
    return "info"


def ms_html(colors):
    css = {"p":"background:#CC44FF","g":"background:#39FF14",
           "y":"background:#FFD700","w":"background:#222"}
    divs = "".join(
        f'<div style="{css.get(c,"background:#222")};flex:1;height:5px;"></div>'
        for c in colors
    )
    return (f'<div style="display:flex;gap:1px;height:5px;border-radius:2px;'
            f'overflow:hidden;width:72px;">{divs}</div>')

# ============================================================
# DATA LOADERS
# ============================================================

@st.cache_data(show_spinner=False)
def load_session_cached(year, gp, stype):
    s = fastf1.get_session(year, gp, stype)
    s.load(telemetry=True, laps=True, weather=True, messages=True)
    return s


@st.cache_data(show_spinner=False)
def get_schedule_df(yr):
    try:
        df = fastf1.get_event_schedule(yr, include_testing=False)
        return df[df["RoundNumber"] > 0].copy()
    except Exception:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def fetch_standings(year, rn):
    drivers, constructors = [], []
    base = "https://api.jolpi.ca/ergast/f1"
    try:
        r  = requests.get(f"{base}/{year}/{rn}/driverStandings", timeout=8)
        sl = r.json().get("MRData",{}).get("StandingsTable",{}).get("StandingsLists",[])
        if sl:
            for s in sl[0].get("DriverStandings",[]):
                drivers.append({
                    "Pos":    int(s.get("position",0)),
                    "Driver": str(s["Driver"].get("familyName","")),
                    "Given":  str(s["Driver"].get("givenName","")),
                    "Code":   str(s["Driver"].get("code","")),
                    "Team":   str(s["Constructors"][0]["name"]) if s.get("Constructors") else "",
                    "Points": float(s.get("points",0)),
                    "Wins":   int(s.get("wins",0)),
                })
    except Exception:
        pass
    try:
        r  = requests.get(f"{base}/{year}/{rn}/constructorStandings", timeout=8)
        sl = r.json().get("MRData",{}).get("StandingsTable",{}).get("StandingsLists",[])
        if sl:
            for s in sl[0].get("ConstructorStandings",[]):
                constructors.append({
                    "Pos":    int(s.get("position",0)),
                    "Name":   str(s["Constructor"].get("name","")),
                    "Points": float(s.get("points",0)),
                    "Wins":   int(s.get("wins",0)),
                })
    except Exception:
        pass
    return drivers, constructors

# ============================================================
# SESSION-SCOPED DATA (NOT cached - always fresh per session)
# ============================================================

def build_circuit_xy(session):
    try:
        pos = session.laps.pick_fastest().get_pos_data()[["X","Y"]].dropna()
        return pos.reset_index(drop=True)
    except Exception:
        return pd.DataFrame(columns=["X","Y"])


def build_driver_positions(session):
    records = []
    for drv in session.drivers:
        laps = session.laps.pick_drivers(drv)
        for _, lap in laps.iterrows():
            try:
                pos = lap.get_pos_data()[["X","Y","Time"]].dropna()
                if pos.empty:
                    continue
                step = max(1, len(pos)//60)
                s = pos.iloc[::step].copy()
                s["Driver"]    = str(drv)
                s["LapNumber"] = int(lap["LapNumber"])
                num, _, _, team = get_driver_info(drv, session)
                s["Num"]  = num
                s["Team"] = team
                records.append(s)
            except Exception:
                continue
    if records:
        return pd.concat(records, ignore_index=True)
    return pd.DataFrame(columns=["X","Y","Time","Driver","LapNumber","Num","Team"])


def build_timing_data(session, stype):
    rows = []
    for drv in session.drivers:
        dlaps = session.laps.pick_drivers(drv)
        if dlaps.empty:
            continue
        num, full, abbr, team = get_driver_info(drv, session)
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

        ms = []
        try:
            if fastest is not None:
                slaps = session.laps.pick_quicklaps()
                for sec in ["Sector1Time","Sector2Time","Sector3Time"]:
                    sv = fastest.get(sec)
                    if sv is None or (hasattr(sv,"total_seconds") and pd.isna(sv)):
                        ms.extend(["w","w"]); continue
                    sb = slaps[sec].min()
                    try:
                        db = dlaps.pick_quicklaps()[sec].min()
                    except Exception:
                        db = sv
                    if sv == sb:
                        ms.extend(["p","p"])
                    elif sv == db:
                        ms.extend(["g","g"])
                    else:
                        ms.extend(["y","y"])
        except Exception:
            ms = ["w"]*6

        rows.append({
            "Driver":  str(drv),
            "Number":  num,
            "Name":    full,
            "Team":    team,
            "LapTime": fastest["LapTime"]     if fastest is not None else None,
            "S1":      fastest["Sector1Time"] if fastest is not None else None,
            "S2":      fastest["Sector2Time"] if fastest is not None else None,
            "S3":      fastest["Sector3Time"] if fastest is not None else None,
            "Speed":   fastest["SpeedI1"]     if fastest is not None else None,
            "Status":  status,
            "MS":      ms,
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

    for sec in ["S1","S2","S3"]:
        valid = df[sec].dropna()
        if valid.empty:
            df[sec+"F"] = "Y"; continue
        best = valid.min()
        df[sec+"F"] = df[sec].apply(
            lambda v: "P" if pd.notna(v) and v==best else ("G" if pd.notna(v) else "Y")
        )
    return df

# ============================================================
# LIVE DETECTION
# ============================================================

def check_live_session():
    try:
        now = datetime.now(timezone.utc)
        df  = get_schedule_df(now.year)
        if df.empty:
            return None
        for _, ev in df.iterrows():
            for i in range(1,6):
                sdate = ev.get(f"Session{i}Date")
                sname = ev.get(f"Session{i}","")
                if sdate is None or not sname:
                    continue
                try:
                    ts = pd.Timestamp(sdate)
                    if ts.tzinfo is None:
                        ts = ts.tz_localize("UTC")
                    diff = (now - ts).total_seconds()/60
                    if -30 <= diff <= 180:
                        return {
                            "event":   str(ev.get("EventName","")),
                            "session": str(sname),
                            "year":    now.year,
                            "started": diff > 0,
                        }
                except Exception:
                    continue
    except Exception:
        pass
    return None

# ============================================================
# MAP FIGURE
# ============================================================

def build_map_figure(circuit_xy, all_pos, session, lap_num):
    fig = go.Figure()

    # Track
    if not circuit_xy.empty:
        fig.add_trace(go.Scatter(
            x=circuit_xy["X"], y=circuit_xy["Y"], mode="lines",
            line=dict(color="#1a1a1a", width=12),
            hoverinfo="skip", showlegend=False, name="bg"
        ))
        fig.add_trace(go.Scatter(
            x=circuit_xy["X"], y=circuit_xy["Y"], mode="lines",
            line=dict(color="#2e2e2e", width=7),
            hoverinfo="skip", showlegend=False, name="track"
        ))

    lap_data = all_pos[all_pos["LapNumber"] == lap_num].copy()
    latest   = lap_data.sort_values("Time").groupby("Driver").tail(1)

    driver_info_list = []
    for _, row in latest.iterrows():
        drv    = str(row["Driver"])
        num    = str(row.get("Num", drv))
        team   = str(row.get("Team", "Unknown"))
        color  = tcolor(team, session)
        is_col = drv == FEATURED_DRIVER

        try:
            info = session.get_driver(drv)
            abbr = str(info.get("Abbreviation", drv))
        except Exception:
            abbr = drv

        driver_info_list.append({
            "drv": drv, "num": num, "abbr": abbr,
            "color": color, "is_col": is_col,
        })

        fig.add_trace(go.Scatter(
            x=[row["X"]], y=[row["Y"]], mode="markers+text",
            marker=dict(
                color=FEATURED_COLOR if is_col else color,
                size=18 if is_col else 9,
                symbol="star" if is_col else "circle",
                line=dict(color="#fff" if is_col else color,
                          width=2 if is_col else 0),
            ),
            text=[num], textposition="top center",
            textfont=dict(color=FEATURED_COLOR if is_col else "#bbb",
                          size=9 if is_col else 7),
            showlegend=False, name=num,
            hovertemplate=f"<b>{abbr}</b> #{num}<br>{team}<extra></extra>",
        ))

    # Animation frames
    frames = []
    if not lap_data.empty:
        all_times = lap_data["Time"].sort_values().unique()
        step = max(1, len(all_times)//45)
        for t in all_times[::step]:
            fd = [
                go.Scatter(
                    x=circuit_xy["X"] if not circuit_xy.empty else [],
                    y=circuit_xy["Y"] if not circuit_xy.empty else [],
                    mode="lines", line=dict(color="#1a1a1a", width=12),
                    hoverinfo="skip", showlegend=False),
                go.Scatter(
                    x=circuit_xy["X"] if not circuit_xy.empty else [],
                    y=circuit_xy["Y"] if not circuit_xy.empty else [],
                    mode="lines", line=dict(color="#2e2e2e", width=7),
                    hoverinfo="skip", showlegend=False),
            ]
            for dr in driver_info_list:
                dd  = lap_data[lap_data["Driver"] == dr["drv"]]
                pt  = dd[dd["Time"] <= t]
                pos = pt.iloc[-1] if not pt.empty else dd.iloc[0]
                fd.append(go.Scatter(
                    x=[pos["X"]], y=[pos["Y"]], mode="markers+text",
                    marker=dict(
                        color=FEATURED_COLOR if dr["is_col"] else dr["color"],
                        size=18 if dr["is_col"] else 9,
                        symbol="star" if dr["is_col"] else "circle",
                        line=dict(color="#fff" if dr["is_col"] else dr["color"],
                                  width=2 if dr["is_col"] else 0),
                    ),
                    text=[dr["num"]], textposition="top center",
                    textfont=dict(color=FEATURED_COLOR if dr["is_col"] else "#bbb",
                                  size=9 if dr["is_col"] else 7),
                    showlegend=False, name=dr["num"],
                ))
            frames.append(go.Frame(data=fd, name=str(t)))

    fig.frames = frames
    fig.update_layout(
        paper_bgcolor="#080808", plot_bgcolor="#080808", showlegend=False,
        margin=dict(l=0,r=0,t=0,b=50),
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False), height=460,
        updatemenus=[dict(
            type="buttons", showactive=False,
            y=-0.11, x=0.5, xanchor="center",
            buttons=[
                dict(label="Play", method="animate",
                     args=[None, {"frame":{"duration":70,"redraw":True},
                                  "fromcurrent":True,"transition":{"duration":0}}]),
                dict(label="Pause", method="animate",
                     args=[[None], {"frame":{"duration":0,"redraw":False},
                                    "mode":"immediate","transition":{"duration":0}}]),
            ],
            font=dict(color="#ccc",size=11),
            bgcolor="#111",bordercolor="#222",
        )],
        sliders=[dict(
            active=0,
            steps=[dict(method="animate",
                        args=[[f.name],{"frame":{"duration":70,"redraw":True},
                                        "mode":"immediate","transition":{"duration":0}}],
                        label="") for f in frames],
            x=0.0, y=-0.07, len=1.0,
            currentvalue=dict(visible=False),
            bgcolor="#111", bordercolor="#1a1a1a",
        )] if frames else [],
    )
    return fig, driver_info_list

# ============================================================
# TELEMETRY FIGURE
# ============================================================

def build_tel_figure(session, drv1, drv2):
    def get_tel(drv):
        try:
            dlaps = session.laps.pick_drivers(drv)
            if dlaps.empty: return None, None
            lap = dlaps.pick_fastest()
            tel = lap.get_car_data().add_distance()
            return tel, lap
        except Exception:
            return None, None

    tel1, lap1 = get_tel(drv1)
    tel2, lap2 = get_tel(drv2)

    channels = ["Speed","Throttle","Brake","RPM","nGear"]
    ylabels  = ["Speed (km/h)","Throttle (%)","Brake","RPM","Gear"]

    n1, _, _, t1 = get_driver_info(drv1, session)
    n2, _, _, t2 = get_driver_info(drv2, session)
    c1 = FEATURED_COLOR if drv1==FEATURED_DRIVER else tcolor(t1, session)
    c2 = FEATURED_COLOR if drv2==FEATURED_DRIVER else tcolor(t2, session)
    lbl1 = f"{n1} - {get_driver_info(drv1,session)[1]}"
    lbl2 = f"{n2} - {get_driver_info(drv2,session)[1]}"

    fig = make_subplots(rows=len(channels), cols=1, shared_xaxes=True,
                        subplot_titles=ylabels, vertical_spacing=0.033)
    has_data = False
    for i, ch in enumerate(channels, 1):
        if tel1 is not None and ch in tel1.columns:
            fig.add_trace(go.Scatter(
                x=tel1["Distance"], y=tel1[ch],
                line=dict(color=c1, width=1.8),
                name=lbl1, legendgroup=drv1, showlegend=(i==1),
            ), row=i, col=1)
            has_data = True
        if tel2 is not None and ch in tel2.columns:
            fig.add_trace(go.Scatter(
                x=tel2["Distance"], y=tel2[ch],
                line=dict(color=c2, width=1.8, dash="dot"),
                name=lbl2, legendgroup=drv2, showlegend=(i==1),
            ), row=i, col=1)
            has_data = True

    fig.update_layout(
        paper_bgcolor="#080808", plot_bgcolor="#080808", height=680,
        legend=dict(bgcolor="#0f0f0f",bordercolor="#1a1a1a",borderwidth=1,
                    font=dict(color="#ccc",size=11),orientation="h",
                    x=0.5,xanchor="center",y=1.02),
        margin=dict(l=52,r=12,t=42,b=32),
        font=dict(color="#555",size=9),
    )
    for i in range(1, len(channels)+1):
        fig.update_xaxes(gridcolor="#111", zeroline=False, row=i, col=1)
        fig.update_yaxes(gridcolor="#111", zeroline=False, row=i, col=1)
    fig.update_xaxes(title_text="Distance (m)", row=len(channels), col=1)
    return fig, has_data, lap1, lap2, c1, c2, lbl1, lbl2


def build_lap_chart(session, driver):
    try:
        laps = session.laps.pick_drivers(driver).pick_quicklaps()
    except Exception:
        return go.Figure()
    _, _, _, team = get_driver_info(driver, session)
    color = FEATURED_COLOR if driver==FEATURED_DRIVER else tcolor(team, session)
    fig = go.Figure()
    if not laps.empty:
        ts = laps["LapTime"].dt.total_seconds()
        fig.add_trace(go.Scatter(
            x=laps["LapNumber"], y=ts, mode="lines+markers",
            line=dict(color=color,width=2), marker=dict(size=4,color=color),
            hovertemplate="Lap %{x} - %{customdata}<extra></extra>",
            customdata=[fmt_lap(t) for t in laps["LapTime"]],
        ))
        bi = ts.idxmin()
        fig.add_annotation(
            x=laps.loc[bi,"LapNumber"], y=ts[bi],
            text=f"BEST {fmt_lap(laps.loc[bi,'LapTime'])}",
            showarrow=True, arrowhead=2,
            font=dict(color="#CC44FF",size=9), arrowcolor="#CC44FF",
        )
    fig.update_layout(
        paper_bgcolor="#080808", plot_bgcolor="#080808", height=230,
        margin=dict(l=42,r=8,t=8,b=32),
        xaxis=dict(title="Lap",gridcolor="#111",color="#3a3a3a"),
        yaxis=dict(title="Sec",gridcolor="#111",color="#3a3a3a"),
        font=dict(color="#555"), showlegend=False,
    )
    return fig

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_featured(session):
    st.markdown("""
    <div class="col-card">
      <div style="color:#00D2BE;font-size:.88rem;font-weight:700;
                  letter-spacing:.2em;text-transform:uppercase;">
        Featured Driver Monitor - Franco Colapinto - #43 - Williams
      </div>
    </div>""", unsafe_allow_html=True)
    try:
        laps = session.laps.pick_drivers(FEATURED_DRIVER)
        if laps.empty:
            st.info("Colapinto (COL) has no data in this session.")
            return
        qlaps   = laps.pick_quicklaps()
        fastest = laps.pick_fastest() if not laps.empty else None
        last    = laps.iloc[-1] if not laps.empty else None

        cols = st.columns(7)
        items = [
            ("Last Lap",  fmt_lap(last["LapTime"])    if last is not None else "--"),
            ("S1",        fmt_sec(last["Sector1Time"])if last is not None else "--"),
            ("S2",        fmt_sec(last["Sector2Time"])if last is not None else "--"),
            ("S3",        fmt_sec(last["Sector3Time"])if last is not None else "--"),
            ("Best Lap",  fmt_lap(fastest["LapTime"]) if fastest is not None else "--"),
            ("Lap",       str(int(last["LapNumber"])) if last is not None else "--"),
            ("Compound",  str(last["Compound"])        if last is not None else "--"),
        ]
        for c,(l,v) in zip(cols, items):
            with c:
                st.markdown(f"""
                <div class="metric-tile">
                  <div class="val">{v}</div><div class="lbl">{l}</div>
                </div>""", unsafe_allow_html=True)

        if not qlaps.empty:
            st.markdown("<div class='sh'>Sector Performance</div>",
                        unsafe_allow_html=True)
            scols = st.columns(3)
            slaps = session.laps.pick_quicklaps()
            for i,(sc,sec) in enumerate(
                    zip(scols,["Sector1Time","Sector2Time","Sector3Time"])):
                try:
                    db  = qlaps[sec].min()
                    sb  = slaps[sec].min()
                    clr = "#CC44FF" if db==sb else "#39FF14"
                    bge = "SESSION BEST" if db==sb else "PERSONAL BEST"
                except Exception:
                    db=None; clr="#FFD700"; bge=""
                with sc:
                    st.markdown(f"""
                    <div class="metric-tile">
                      <div class="val" style="color:{clr}">{fmt_sec(db)}</div>
                      <div class="lbl">S{i+1} - {bge}</div>
                    </div>""", unsafe_allow_html=True)

        # Weather
        st.markdown("<div class='sh'>Track Weather</div>", unsafe_allow_html=True)
        try:
            wx = session.weather_data
            if wx is not None and not wx.empty:
                lw   = wx.iloc[-1]
                wcols = st.columns(5)
                for wc,(wl,wv) in zip(wcols,[
                    ("Air Temp",  f"{lw.get('AirTemp',0):.1f} C"),
                    ("Track",     f"{lw.get('TrackTemp',0):.1f} C"),
                    ("Humidity",  f"{lw.get('Humidity',0):.0f} %"),
                    ("Wind",      f"{lw.get('WindSpeed',0):.1f} m/s"),
                    ("Rain",      "Yes" if lw.get("Rainfall",False) else "No"),
                ]):
                    with wc:
                        st.markdown(f"""
                        <div class="metric-tile">
                          <div class="val">{wv}</div>
                          <div class="lbl">{wl}</div>
                        </div>""", unsafe_allow_html=True)
        except Exception:
            st.caption("Weather unavailable.")

        if not qlaps.empty:
            st.markdown("<div class='sh'>Lap Time Chart</div>",
                        unsafe_allow_html=True)
            st.plotly_chart(build_lap_chart(session, FEATURED_DRIVER),
                            use_container_width=True)
    except Exception as e:
        st.warning(f"Featured driver error: {e}")


def render_timing(session, stype):
    st.markdown("<div class='sh'>Timing Tower</div>", unsafe_allow_html=True)

    # Alerts
    try:
        msgs = session.race_control_messages
        if msgs is not None and not msgs.empty:
            for _, m in msgs.tail(5).iterrows():
                txt = str(m.get("Message","")).upper()
                if "SAFETY CAR DEPLOYED" in txt:
                    st.markdown('<div class="alert-sc">Safety Car Deployed</div>',
                                unsafe_allow_html=True); break
                elif "VIRTUAL SAFETY CAR DEPLOYED" in txt:
                    st.markdown('<div class="alert-sc">Virtual Safety Car</div>',
                                unsafe_allow_html=True); break
                elif "RED FLAG" in txt:
                    st.markdown('<div class="alert-red">Red Flag</div>',
                                unsafe_allow_html=True); break
    except Exception:
        pass

    df = build_timing_data(session, stype)
    if df.empty:
        st.info("No timing data available for this session.")
        return

    is_qual = stype in ("Q","SQ")

    # Build table using st.dataframe approach to avoid HTML rendering issues
    # We'll use a styled HTML table but wrap each row carefully
    fc_map = {"P":"#CC44FF","G":"#39FF14","Y":"#FFD700"}

    # Header
    header_cols = st.columns([0.4, 2.5, 1.5, 1.2, 0.9, 0.9, 0.9, 0.8, 0.8, 1.0])
    headers = ["P","Driver","Team","Best Lap","S1","S2","S3","Mini","Trap","Delta"]
    for hc, h in zip(header_cols, headers):
        hc.markdown(
            f'<div style="color:#333;font-size:.6rem;letter-spacing:.1em;'
            f'text-transform:uppercase;font-weight:600;padding:4px 0;'
            f'border-bottom:1px solid #1a1a1a;">{h}</div>',
            unsafe_allow_html=True
        )

    for _, row in df.iterrows():
        pos    = row["Pos"]
        is_col = row["Driver"] == FEATURED_DRIVER
        status = str(row.get("Status",""))
        is_qual_elim = is_qual and pos > 10

        bg     = "#08111c" if is_col else ("#0d0a0a" if status in ("DNF","DNS") else "transparent")
        fc     = "#00D2BE" if is_col else ("#3a3a3a" if status in ("DNF","DNS") else "#999")

        row_cols = st.columns([0.4, 2.5, 1.5, 1.2, 0.9, 0.9, 0.9, 0.8, 0.8, 1.0])

        # Badge
        badge = ""
        if status == "DNF":
            badge = ' <span style="background:#1e0808;color:#FF4444;padding:1px 5px;border-radius:3px;font-size:.6rem;font-weight:700;">DNF</span>'
        elif status == "DNS":
            badge = ' <span style="background:#1e1800;color:#FFAA00;padding:1px 5px;border-radius:3px;font-size:.6rem;font-weight:700;">DNS</span>'
        elif is_qual and pos == 11:
            badge = ' <span style="background:#1a0a0a;color:#FF6644;padding:1px 5px;border-radius:3px;font-size:.6rem;">OUT Q3</span>'
        elif is_qual and pos == 16:
            badge = ' <span style="background:#1a1200;color:#FFAA44;padding:1px 5px;border-radius:3px;font-size:.6rem;">OUT Q2</span>'

        star = "* " if is_col else ""
        drv_name = f"{row['Number']} - {row['Name']}"
        spd = f'{row["Speed"]:.0f}' if pd.notna(row.get("Speed")) else "--"

        s1c = fc_map.get(row.get("S1F","Y"), "#FFD700")
        s2c = fc_map.get(row.get("S2F","Y"), "#FFD700")
        s3c = fc_map.get(row.get("S3F","Y"), "#FFD700")

        mono = "font-family:'JetBrains Mono',monospace;font-size:.73rem;"
        cell_style = f"background:{bg};padding:5px 2px;{mono}color:{fc};"

        with row_cols[0]:
            st.markdown(
                f'<div style="{cell_style}font-weight:700;">{pos}</div>',
                unsafe_allow_html=True)
        with row_cols[1]:
            st.markdown(
                f'<div style="{cell_style}font-weight:600;">{star}{drv_name}{badge}</div>',
                unsafe_allow_html=True)
        with row_cols[2]:
            st.markdown(
                f'<div style="background:{bg};padding:5px 2px;font-size:.68rem;color:#2a2a2a;">'
                f'{row.get("Team","")[:16]}</div>',
                unsafe_allow_html=True)
        with row_cols[3]:
            st.markdown(
                f'<div style="{cell_style}">{fmt_lap(row["LapTime"])}</div>',
                unsafe_allow_html=True)
        with row_cols[4]:
            st.markdown(
                f'<div style="{cell_style}color:{s1c};font-weight:700;">{fmt_sec(row["S1"])}</div>',
                unsafe_allow_html=True)
        with row_cols[5]:
            st.markdown(
                f'<div style="{cell_style}color:{s2c};font-weight:700;">{fmt_sec(row["S2"])}</div>',
                unsafe_allow_html=True)
        with row_cols[6]:
            st.markdown(
                f'<div style="{cell_style}color:{s3c};font-weight:700;">{fmt_sec(row["S3"])}</div>',
                unsafe_allow_html=True)
        with row_cols[7]:
            st.markdown(
                f'<div style="background:{bg};padding:5px 2px;">'
                f'{ms_html(row.get("MS",["w"]*6))}</div>',
                unsafe_allow_html=True)
        with row_cols[8]:
            st.markdown(
                f'<div style="{cell_style}">{spd}</div>',
                unsafe_allow_html=True)
        with row_cols[9]:
            delta_color = "#E10600" if row["Delta"] == "LEADER" else "#999"
            st.markdown(
                f'<div style="{cell_style}color:{delta_color};">{row["Delta"]}</div>',
                unsafe_allow_html=True)

        # Q cutoff dividers
        if is_qual and pos in (10, 15):
            st.markdown(
                '<hr style="border:none;border-top:1px solid #E10600;margin:1px 0;">',
                unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:8px;font-size:.65rem;color:#2a2a2a;">
      <span style="color:#CC44FF">Purple</span> = Session best &nbsp;|&nbsp;
      <span style="color:#39FF14">Green</span> = Personal best &nbsp;|&nbsp;
      <span style="color:#FFD700">Yellow</span> = No improvement
    </div>""", unsafe_allow_html=True)


def render_map(session, session_key):
    st.markdown("<div class='sh'>GPS Circuit Map</div>", unsafe_allow_html=True)

    # Build fresh data - NOT cached, keyed to this session
    if (st.session_state.get("map_session_key") != session_key or
            "circuit_xy" not in st.session_state):
        with st.spinner("Loading position data..."):
            st.session_state["circuit_xy"]     = build_circuit_xy(session)
            st.session_state["driver_pos"]     = build_driver_positions(session)
            st.session_state["map_session_key"] = session_key

    circuit_xy = st.session_state["circuit_xy"]
    all_pos    = st.session_state["driver_pos"]

    if all_pos.empty:
        st.warning("Position data not available for this session. "
                   "GPS data is most complete in Race and Qualifying sessions.")
        return

    max_lap = int(all_pos["LapNumber"].max())
    min_lap = int(all_pos["LapNumber"].min())

    map_col, list_col = st.columns([3, 1])
    with map_col:
        sel_lap = st.slider("Lap", min_value=min_lap, max_value=max_lap,
                            value=min_lap, step=1,
                            key=f"mapslider_{session_key}")
        st.markdown(
            '<div style="font-size:.7rem;color:#333;margin-bottom:5px;">'
            'Press Play to animate. Teal star = Colapinto.</div>',
            unsafe_allow_html=True)
        with st.spinner("Rendering map..."):
            fig, driver_list = build_map_figure(circuit_xy, all_pos, session, sel_lap)
        st.plotly_chart(fig, use_container_width=True, key=f"mapfig_{session_key}_{sel_lap}")

    with list_col:
        st.markdown("<div class='sh'>Drivers</div>", unsafe_allow_html=True)
        for dr in driver_list:
            clr  = FEATURED_COLOR if dr["is_col"] else dr["color"]
            bold = "font-weight:700;" if dr["is_col"] else ""
            col_c = "#00D2BE" if dr["is_col"] else "#555"
            st.markdown(f"""
            <div class="mdr">
              <div class="mdd" style="background:{clr}"></div>
              <span style="color:#333;min-width:22px;font-family:'JetBrains Mono',monospace;
                           font-size:.72rem;">{dr['num']}</span>
              <span style="color:{col_c};{bold};font-size:.72rem;">{dr['abbr']}</span>
            </div>""", unsafe_allow_html=True)


def render_telemetry(session, session_key):
    st.markdown("<div class='sh'>Telemetry Comparison</div>",
                unsafe_allow_html=True)
    st.markdown("""
    <div class="telh">
      <b>Speed</b> = km/h &nbsp;|&nbsp; <b>Throttle</b> = gas 0-100% &nbsp;|&nbsp;
      <b>Brake</b> = on/off &nbsp;|&nbsp; <b>RPM</b> = engine revs &nbsp;|&nbsp;
      <b>Gear</b> = current gear. Solid = A, Dotted = B.
    </div>""", unsafe_allow_html=True)

    all_drivers = list(session.drivers)
    if len(all_drivers) < 2:
        st.info("Need at least 2 drivers.")
        return

    disp = []
    for d in all_drivers:
        num, full, _, _ = get_driver_info(d, session)
        disp.append(f"{num} - {full}")

    d1i = next((i for i,d in enumerate(all_drivers) if d==FEATURED_DRIVER), 0)
    d2i = (d1i+1) % len(all_drivers)

    c1, c2 = st.columns(2)
    with c1:
        s1 = st.selectbox("Driver A", disp, index=d1i, key=f"td1_{session_key}")
    with c2:
        s2 = st.selectbox("Driver B", disp, index=d2i, key=f"td2_{session_key}")

    drv1 = all_drivers[disp.index(s1)]
    drv2 = all_drivers[disp.index(s2)]
    if drv1 == drv2:
        st.warning("Select two different drivers.")
        return

    with st.spinner("Loading telemetry..."):
        fig, has_data, lap1, lap2, tc1, tc2, lbl1, lbl2 = build_tel_figure(session, drv1, drv2)

    if not has_data:
        st.warning("Telemetry not available. Try Race or Qualifying sessions.")
        return

    m1, m2 = st.columns(2)
    with m1:
        lt = fmt_lap(lap1["LapTime"]) if lap1 is not None else "--"
        st.markdown(f"""
        <div class="metric-tile" style="border-left:3px solid {tc1};">
          <div class="val" style="color:{tc1}">{lt}</div>
          <div class="lbl">{lbl1} - Fastest</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        lt = fmt_lap(lap2["LapTime"]) if lap2 is not None else "--"
        st.markdown(f"""
        <div class="metric-tile" style="border-left:3px solid {tc2};">
          <div class="val" style="color:{tc2}">{lt}</div>
          <div class="lbl">{lbl2} - Fastest</div>
        </div>""", unsafe_allow_html=True)

    st.plotly_chart(fig, use_container_width=True, key=f"telfig_{session_key}")


def render_championship(year, gp):
    st.markdown("<div class='sh'>Championship Standings</div>",
                unsafe_allow_html=True)
    try:
        df_sched = get_schedule_df(year)
        rn = 1
        if not df_sched.empty:
            m = df_sched[df_sched["EventName"].str.contains(
                gp.split()[0], case=False, na=False)]
            if not m.empty:
                rn = int(m.iloc[0]["RoundNumber"])
    except Exception:
        rn = 1

    with st.spinner("Fetching standings..."):
        drivers, constructors = fetch_standings(year, rn)

    if not drivers and not constructors:
        st.info("Championship data not available for this round.")
        return

    td, tc = st.tabs(["Drivers","Constructors"])
    with td:
        if not drivers:
            st.info("No driver standings data.")
        else:
            max_pts = max((d["Points"] for d in drivers), default=1) or 1
            for d in drivers:
                is_col  = str(d.get("Code","")) == FEATURED_DRIVER
                pct     = int((d["Points"]/max_pts)*100)
                bc      = FEATURED_COLOR if is_col else "#E10600"
                star    = "* " if is_col else ""
                name_c  = "#00D2BE" if is_col else "#ccc"
                cols    = st.columns([0.3, 2, 1.8, 2, 0.5])
                with cols[0]:
                    st.markdown(
                        f'<div style="font-size:.78rem;color:#555;padding:4px 0;">'
                        f'<b>{d["Pos"]}</b></div>',
                        unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(
                        f'<div style="font-size:.78rem;color:{name_c};padding:4px 0;font-weight:600;">'
                        f'{star}{d.get("Given","")} {d["Driver"]}</div>',
                        unsafe_allow_html=True)
                with cols[2]:
                    st.markdown(
                        f'<div style="font-size:.68rem;color:#2a2a2a;padding:4px 0;">'
                        f'{str(d.get("Team",""))[:22]}</div>',
                        unsafe_allow_html=True)
                with cols[3]:
                    bar = (f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;">'
                           f'<span style="font-family:JetBrains Mono,monospace;font-weight:600;'
                           f'color:{name_c};min-width:32px;font-size:.78rem;">{int(d["Points"])}</span>'
                           f'<div style="background:#151515;border-radius:3px;height:5px;flex:1;">'
                           f'<div style="background:{bc};border-radius:3px;height:5px;width:{pct}%;"></div>'
                           f'</div></div>')
                    st.markdown(bar, unsafe_allow_html=True)
                with cols[4]:
                    st.markdown(
                        f'<div style="font-size:.75rem;color:#2a2a2a;padding:4px 0;">'
                        f'{d["Wins"]}</div>',
                        unsafe_allow_html=True)
            st.markdown(
                f'<div style="margin-top:6px;font-size:.62rem;color:#2a2a2a;">'
                f'After Round {rn} - {year}</div>',
                unsafe_allow_html=True)

    with tc:
        if not constructors:
            st.info("No constructor standings data.")
        else:
            max_pts = max((c["Points"] for c in constructors), default=1) or 1
            for c in constructors:
                name = str(c.get("Name",""))
                pct  = int((c["Points"]/max_pts)*100)
                bc   = TEAM_COLORS.get(name, "#E10600")
                cols = st.columns([0.3, 2, 2.5, 0.5])
                with cols[0]:
                    st.markdown(
                        f'<div style="font-size:.78rem;color:#555;padding:4px 0;">'
                        f'<b>{c["Pos"]}</b></div>',
                        unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(
                        f'<div style="font-size:.78rem;color:#ccc;padding:4px 0;font-weight:600;">'
                        f'{name}</div>',
                        unsafe_allow_html=True)
                with cols[2]:
                    bar = (f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;">'
                           f'<span style="font-family:JetBrains Mono,monospace;font-weight:600;'
                           f'color:#ccc;min-width:32px;font-size:.78rem;">{int(c["Points"])}</span>'
                           f'<div style="background:#151515;border-radius:3px;height:5px;flex:1;">'
                           f'<div style="background:{bc};border-radius:3px;height:5px;width:{pct}%;"></div>'
                           f'</div></div>')
                    st.markdown(bar, unsafe_allow_html=True)
                with cols[3]:
                    st.markdown(
                        f'<div style="font-size:.75rem;color:#2a2a2a;padding:4px 0;">'
                        f'{c["Wins"]}</div>',
                        unsafe_allow_html=True)


def render_fia(session):
    st.markdown("<div class='sh'>Race Control / FIA Messages</div>",
                unsafe_allow_html=True)
    try:
        msgs = session.race_control_messages
        if msgs is None or msgs.empty:
            st.info("No race control messages for this session.")
            return
        for _, row in msgs.sort_values("Time", ascending=False).head(40).iterrows():
            text = str(row.get("Message",""))
            lap  = row.get("Lap","")
            cls  = classify_msg(text)
            lap_str = f"Lap {int(lap)}" if pd.notna(lap) and str(lap) != "" else ""
            st.markdown(f"""
            <div class="fiam {cls}">
              <div class="fialap">{lap_str}</div>
              <div style="color:#888">{text}</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.info(f"Race control messages unavailable: {e}")


def render_schedule(year):
    st.markdown(f"<div class='sh'>{year} Season Schedule</div>",
                unsafe_allow_html=True)
    try:
        now = datetime.now(timezone.utc)
        df  = get_schedule_df(year)
        if df.empty:
            st.info("Schedule unavailable.")
            return

        # Countdown
        next_ev = None
        for _, ev in df.iterrows():
            try:
                d = ev.get("EventDate") or ev.get("Session5Date")
                if d is None: continue
                ts = pd.Timestamp(d)
                if ts.tzinfo is None:
                    ts = ts.tz_localize("UTC")
                if ts > now:
                    next_ev = (ev, ts); break
            except Exception:
                continue

        if next_ev:
            ev, ts = next_ev
            delta = ts - now
            days  = delta.days
            hours = delta.seconds//3600
            mins  = (delta.seconds%3600)//60
            st.markdown(f"""
            <div style="margin-bottom:10px;">
              <div style="color:#2a2a2a;font-size:.62rem;letter-spacing:.15em;
                          text-transform:uppercase;margin-bottom:6px;">
                Next: <b style="color:#E10600">{ev.get('EventName','')}</b>
              </div>
              <div style="display:flex;gap:8px;">
                <div class="cdbox" style="flex:1">
                  <div class="cdval">{days}</div><div class="cdlbl">Days</div>
                </div>
                <div class="cdbox" style="flex:1">
                  <div class="cdval">{hours}</div><div class="cdlbl">Hours</div>
                </div>
                <div class="cdbox" style="flex:1">
                  <div class="cdval">{mins}</div><div class="cdlbl">Min</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        for _, ev in df.iterrows():
            name  = ev.get("EventName","")
            rnd   = ev.get("RoundNumber","")
            cntry = ev.get("Country","")
            try:
                date_str = pd.Timestamp(ev.get("EventDate")).strftime("%B %d")
            except Exception:
                date_str = ""
            is_next = next_ev and ev.get("EventName")==next_ev[0].get("EventName")
            border  = "border-left:3px solid #E10600;" if is_next else ""
            sess_html = ""
            for i in range(1,6):
                sn = ev.get(f"Session{i}","")
                sd = ev.get(f"Session{i}Date")
                if sn and sd is not None:
                    try:
                        sd_str = pd.Timestamp(sd).strftime("%a %b %d")
                        sess_html += f"<div class='sc-sess'>{sd_str} - {sn}</div>"
                    except Exception:
                        sess_html += f"<div class='sc-sess'>{sn}</div>"
            st.markdown(f"""
            <div class="sc-card" style="{border}">
              <div class="sc-round">Round {rnd} - {cntry}</div>
              <div class="sc-name">{name}</div>
              <div style="color:#333;font-size:.72rem;">{date_str}</div>
              <div style="margin-top:5px;">{sess_html}</div>
            </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.info(f"Schedule unavailable: {e}")

# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center;padding:10px 0 16px;'>
          <div style='color:#E10600;font-size:.95rem;font-weight:700;
                      letter-spacing:.2em;text-transform:uppercase;'>
            F1 TELEMETRY
          </div>
          <div style='color:#1e1e1e;font-size:.6rem;letter-spacing:.15em;'>
            DASHBOARD
          </div>
        </div>""", unsafe_allow_html=True)
        st.divider()

        # Only current year
        year    = CURRENT_YEAR
        df_sched = get_schedule_df(year)

        if df_sched.empty:
            st.error("Could not load schedule.")
            return None, None, None

        # Only show rounds that have already happened
        now = datetime.now(timezone.utc)
        past_events = []
        for _, ev in df_sched.iterrows():
            try:
                d = ev.get("Session5Date") or ev.get("EventDate")
                if d is None: continue
                ts = pd.Timestamp(d)
                if ts.tzinfo is None:
                    ts = ts.tz_localize("UTC")
                if ts < now:
                    past_events.append(ev.get("EventName",""))
            except Exception:
                continue

        if not past_events:
            st.info(f"No completed races in {year} yet. Season may not have started.")
            return None, None, None

        st.markdown(
            f'<div style="color:#333;font-size:.6rem;letter-spacing:.1em;'
            f'margin-bottom:4px;">{year} SEASON</div>',
            unsafe_allow_html=True)

        gp = st.selectbox("Grand Prix", past_events, index=len(past_events)-1)

        is_sp  = any(s.lower() in gp.lower() for s in SPRINT_GPS)
        s_opts = SESSION_SPRINT if is_sp else SESSION_NORMAL
        s_lbls = [f"{k} - {SESSION_LABELS[k]}" for k in s_opts]
        sel    = st.selectbox("Session", s_lbls)
        stype  = sel.split(" - ")[0]

        st.divider()
        st.markdown("""
        <div style='color:#1e1e1e;font-size:.6rem;letter-spacing:.08em;
                    line-height:2.2;font-weight:500;'>
          DATA<br><span style='color:#2a2a2a;'>FastF1 + Jolpica</span><br>
          CACHE<br><span style='color:#2a2a2a;'>./cache/</span>
        </div>""", unsafe_allow_html=True)

        return year, gp, stype

# ============================================================
# MAIN
# ============================================================

def main():
    # Live detection
    live_info = check_live_session()
    is_live   = live_info is not None

    mode_badge = (
        '<span class="live-badge">LIVE</span>'
        if is_live else
        '<span class="hist-badge">HISTORICAL</span>'
    )

    st.markdown(f"""
    <div class="f1h">
      <div>
        <div style='color:#E10600;font-size:1.4rem;font-weight:700;letter-spacing:.05em;'>
          FORMULA 1
        </div>
        <div style='color:#2a2a2a;font-size:.62rem;letter-spacing:.25em;font-weight:500;'>
          TELEMETRY DASHBOARD &middot; {CURRENT_YEAR} SEASON
        </div>
      </div>
      <div style='display:flex;align-items:center;gap:10px;'>
        {mode_badge}
        <span style='color:#1e1e1e;font-size:.65rem;'>FastF1</span>
      </div>
    </div>""", unsafe_allow_html=True)

    year, gp, stype = render_sidebar()
    if year is None:
        st.markdown("""
        <div class="ib">
          <b>No completed sessions available yet for this season.</b><br>
          The dashboard will show races and sessions as they are completed.
        </div>""", unsafe_allow_html=True)
        render_schedule(CURRENT_YEAR)
        return

    # -- LIVE MODE ------------------------------------------
    if is_live:
        lev   = live_info["event"]
        lsess = live_info["session"]
        lyear = live_info["year"]

        started = live_info.get("started", False)
        status_txt = "LIVE NOW" if started else "STARTING SOON"
        border_c   = "#E10600" if started else "#FFD700"

        st.markdown(f"""
        <div style="background:#0d0000;border:1px solid {border_c};border-radius:5px;
                    padding:12px 18px;margin-bottom:12px;display:flex;
                    align-items:center;gap:14px;">
          <div class="live-badge">{status_txt}</div>
          <div>
            <div style="color:{border_c};font-weight:700;font-size:.9rem;">{lev}</div>
            <div style="color:#555;font-size:.72rem;letter-spacing:.1em;
                        text-transform:uppercase;">{lsess}</div>
          </div>
          <div style="margin-left:auto;color:#222;font-size:.65rem;">
            Auto-refresh every {LIVE_REFRESH_S}s
          </div>
        </div>""", unsafe_allow_html=True)

        live_key = f"live_{lyear}_{lev}_{lsess}"
        try:
            with st.spinner("Loading live session..."):
                live_session = load_session_cached(lyear, lev, lsess)
        except Exception as e:
            st.error(f"Could not load live session: {e}")
            is_live = False

        if is_live:
            t1,t2,t3,t4,t5,t6,t7 = st.tabs([
                "Live Timing","Live Map","Featured Driver",
                "FIA Messages","Telemetry","Championship","Schedule",
            ])
            with t1: render_timing(live_session, lsess)
            with t2: render_map(live_session, live_key)
            with t3: render_featured(live_session)
            with t4: render_fia(live_session)
            with t5: render_telemetry(live_session, live_key)
            with t6: render_championship(lyear, lev)
            with t7: render_schedule(lyear)
            time.sleep(LIVE_REFRESH_S)
            st.rerun()
            return

    # -- HISTORICAL MODE ------------------------------------
    slabel = SESSION_LABELS.get(stype, stype)
    st.markdown(
        f'<div style="color:#444;font-size:.85rem;font-weight:500;margin-bottom:.6rem;">'
        f'{year} &middot; {gp} &middot; {slabel}</div>',
        unsafe_allow_html=True)

    load_btn    = st.button("Load Session Data", type="primary")
    session_key = f"{year}_{gp}_{stype}"

    # Reset state when selection changes
    if st.session_state.get("sess_key") != session_key:
        for key in ["sess_loaded","_session","circuit_xy","driver_pos","map_session_key"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["sess_key"] = session_key

    already = st.session_state.get("sess_loaded", False)

    if load_btn or already:
        if not already:
            with st.spinner(f"Loading {gp} {stype} {year}..."):
                try:
                    session = load_session_cached(year, gp, stype)
                    st.session_state["_session"]   = session
                    st.session_state["sess_loaded"] = True
                    st.session_state["sess_key"]    = session_key
                    # Clear map cache so it rebuilds for new session
                    for k in ["circuit_xy","driver_pos","map_session_key"]:
                        if k in st.session_state:
                            del st.session_state[k]
                except Exception as e:
                    st.error(f"Failed to load session: {e}")
                    st.info("FastF1 only has data for completed sessions.")
                    return

        session = st.session_state["_session"]

        t1,t2,t3,t4,t5,t6,t7 = st.tabs([
            "Featured Driver","Timing Tower","Circuit Map",
            "Telemetry","Championship","FIA Messages","Schedule",
        ])
        with t1: render_featured(session)
        with t2: render_timing(session, stype)
        with t3: render_map(session, session_key)
        with t4: render_telemetry(session, session_key)
        with t5: render_championship(year, gp)
        with t6: render_fia(session)
        with t7: render_schedule(year)
    else:
        st.markdown("""
        <div class="ib">
          <b>Welcome to the F1 Telemetry Dashboard</b><br><br>
          Select a <b>Grand Prix</b> and <b>Session</b> from the sidebar,
          then click <b>Load Session Data</b>.<br><br>
          The app shows only completed sessions from the current season.<br>
          During a live F1 session it switches to
          <b style="color:#E10600">LIVE MODE</b> automatically.
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        render_schedule(CURRENT_YEAR)


if __name__ == "__main__":
    main()