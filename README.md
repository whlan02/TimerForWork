## TimerForWork

Lightweight, local desktop app to track working time with manual Start/Pause/Resume/Save, modern heatmap visualizations, and Excel storage. It helps you log focused work intervals manually. It stores entries in a local Excel file and visualizes your time with interactive week and month heatmaps. No cloud, no background tracking—fully under your control.


## Table of Contents
- [Features](#features)
- [How to Run](#how-to-run)

## Features
- **Modern Timer Interface**: Clean, minimal design with Start/Pause/Resume/Save workflow
- **Week View Heatmap**: Visualize daily work patterns across Morning (0-12), Afternoon (12-18), and Evening (18-24) periods
  - Hover over blocks to see time details
  - Click blocks or day labels to view detailed records
  - Navigate between weeks with prev/next buttons
- **Month View Heatmap**: Calendar-style overview of monthly work activity
  - Hover over days to see daily totals
  - Click any day to view all records for that date
  - Navigate between months with prev/next buttons
- **Record Details**: View start time, end time, duration, and notes for any time period
- **Local Excel Storage**: All data saved to `time_records.xlsx`, auto-created on first run
- **English UI**: English interface and calendar locale

## How to Run
1) (Recommended) Create and activate a virtual environment

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Launch the app

```bash
python -m app.main
```

Tips
- Close Excel before saving entries if `time_records.xlsx` is open (Windows locks the file).
- Data file lives alongside the app; you can back it up or analyze it with any tool that reads XLSX.

