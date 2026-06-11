#!/bin/bash

cd "$(dirname "$0")"

export PYTHONPATH="$(pwd)/src"

.venv/bin/python run_gui.py