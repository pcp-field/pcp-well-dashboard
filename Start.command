#!/bin/zsh
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv || exit 1
fi
if ! .venv/bin/python -c 'import streamlit,matplotlib,pandas' 2>/dev/null; then
  .venv/bin/python -m pip install -r requirements.txt || exit 1
fi
exec .venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
