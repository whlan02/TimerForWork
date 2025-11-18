## TimerForWork

Lightweight, local desktop app to track working time with manual Start/Pause/Resume/Save, in-app Month/Week views, and Excel storage.

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [How to Run](#how-to-run)

## Introduction
Time Recorder helps you log focused work intervals manually. It stores entries in a local Excel file and visualizes your time on a calendar and week view. No cloud, no background tracking—fully under your control.

## Features
- Start / Pause / Resume / Save workflow
- Large digital Timer view with tenths (HH:MM:SS.t); saved durations use whole seconds
- Month view with per-day coloring by total minutes
- Week view (Mon–Sun) with daily cards, entries, and daily/weekly totals (minutes + HH:MM:SS)
- Local Excel storage (`time_records.xlsx`), auto-created on first run
- English UI and calendar locale

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

