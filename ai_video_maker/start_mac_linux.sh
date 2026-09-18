#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
echo "Open http://127.0.0.1:5000 in your browser."
echo "If OPENAI_API_KEY is empty, keep Demo Mode enabled."
python app.py
