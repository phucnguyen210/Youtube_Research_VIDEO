@echo off
setlocal
cd /d %~dp0
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env >nul
echo.
echo Open http://127.0.0.1:5000 in your browser.
echo If you have not added OPENAI_API_KEY to .env, keep Demo Mode enabled.
echo.
python app.py
pause
