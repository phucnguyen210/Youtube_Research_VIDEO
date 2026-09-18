# AI Visual Storyteller

Source code is in [`ai_video_maker/`](ai_video_maker/). See its [README](ai_video_maker/README.md) for features and usage.

## Run locally (Windows)

```powershell
cd ai_video_maker
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your own `OPENAI_API_KEY` to `.env`, then run `start_windows.bat`. You can enable Demo Mode in the app to test without API calls.

Generated projects, videos, audio, image cache, the virtual environment, and `.env` stay on your computer and are ignored by Git. The `assets/` folder is included because it contains the character and style references required by the app.
