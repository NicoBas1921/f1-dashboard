# 🏎️ F1 Telemetry Dashboard

A Streamlit interactive dashboard powered by **FastF1**, featuring real-time and
historical F1 telemetry, GPS circuit maps, lap-time analysis, and a dedicated
tracker for **Franco Colapinto (COL)**.

---

## 📁 Project Structure

```
f1_dashboard/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── .streamlit/
│   └── config.toml         # Dark F1 theme configuration
└── cache/                  # FastF1 auto-managed local cache (auto-created)
```

---

## ⚙️ Setup & Installation

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** FastF1 requires Python 3.8+. All heavy dependencies (NumPy, Pandas,
> Plotly) are pinned for compatibility.

### 3. Run the app

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501** automatically.

---

## 🚀 First Use

1. On first launch you'll see the **Welcome screen**.
2. Select a **Season → Grand Prix → Session** in the left sidebar.
3. Click **Load Session Data**.  
   FastF1 will download the session data from the F1 API and cache it in
   `./cache/` — this takes ~30–60 s the first time, then **loads instantly**.

### ⭐ Colapinto's debut

To see Franco's F1 debut data immediately:

| Field   | Value                  |
|---------|------------------------|
| Season  | 2024                   |
| GP      | Italian Grand Prix     |
| Session | R – Race               |

---

## 🗂️ Dashboard Tabs

| Tab | Contents |
|-----|----------|
| **⭐ Featured Driver** | Colapinto-specific metrics, sector analysis, lap progression |
| **📊 Timing Tower** | Full grid timing table with purple/green/yellow sector colours |
| **🗺️ Circuit Map** | GPS map with lap-replay slider; COL marked with a star |
| **📈 Telemetry** | Speed / Throttle / Brake / RPM / Gear comparison for any two drivers |

---

## 🏁 Sprint Weekend Support

The sidebar automatically switches session types based on the selected GP:

- **Normal weekend:** FP1, FP2, FP3, Q, R  
- **Sprint weekend:** FP1, SQ (Sprint Qualifying), S (Sprint), Q, R

---

## 🧹 Cache Management

The `./cache/` folder is managed entirely by FastF1.  
To clear it:

```bash
rm -rf cache/
```

The folder is recreated automatically on next launch.

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Failed to load session" | Check internet connection; F1 API must be reachable |
| Driver `COL` not found | Colapinto only appears from the 2024 Italian GP onwards |
| Slow first load | Normal — FastF1 is downloading & parsing ~50–100 MB of data |
| Port already in use | `streamlit run app.py --server.port 8502` |

---

## 📦 Dependencies

| Package     | Version  | Purpose |
|-------------|----------|---------|
| fastf1      | 3.4.0    | F1 data API + telemetry |
| streamlit   | 1.41.0   | Web UI framework |
| plotly      | 5.24.1   | Interactive charts |
| pandas      | 2.2.3    | Data processing |
| numpy       | 1.26.4   | Numerical ops |
| requests    | 2.32.3   | HTTP client |
