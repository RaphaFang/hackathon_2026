# Kolding Pulse — Backend

## Setup

### 1. Install Python dependencies
```
pip install -r requirements.txt
```

### 2. Start Ollama (required for AI endpoints)

Make sure Ollama is installed (https://ollama.com/download).

Pull the model used by the app:
```
ollama pull llama3:8b
```

Start the Ollama server (runs in background on port 11434):
```
ollama serve
```

Verify it's running:
```
ollama list
```
You should see `llama3:8b` in the list.

### 3. Place data files in `data/`

Required files:
- Movement.xlsx
- StayDuration.xlsx
- clean_kolding_events.csv
- movement_stats_hourly.csv
- akseltorv_locations_cleaned_data.csv
- Holidays_data_updated
- cache_parking_hourly_sim.csv
- cache_parking_baseline.csv
- parking_snapshot.csv

### 4. Run the backend
```
uvicorn main:app --reload
```

API docs: http://127.0.0.1:8000/docs

---

## Project Structure

```
backend/
  main.py           ← FastAPI app entry point
  config.py         ← Shared paths and model config
  requirements.txt
  data/             ← All data files go here
  routers/          ← One file per feature group
    overview.py     ← /overview /movement /stay /events /vitality
    ai.py           ← /ask /insight
    parking.py      ← /parking-analysis /parking-insight
    forecast.py     ← /forecast-data /forecast-insight
    city.py         ← /city-insight
  services/         ← Business logic, no HTTP concerns
    analysis.py     ← Data loading + overview functions
    agent.py        ← Ollama AI calls
    parking.py      ← Parking analytics
    forecast.py     ← Forecast model
    city.py         ← City activity analysis
```

## Notes

- The Ollama model is set in `config.py` (`OLLAMA_MODEL`). Change it there if you want a different model.
- `/city-insight` is computed lazily on first request and cached for the session (it's slow — runs heavy analysis + 3 AI calls).
- All data paths are resolved relative to `config.py` using `pathlib.Path`, so the working directory doesn't matter.
