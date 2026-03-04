#!/bin/bash
# Stock Tracker - Daily Report Runner
# Runs the stock tracker and sends report to Discord

cd /home/admin/.openclaw/workspace/stock-tracker

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the stock tracker
python3 src/main.py --config config/settings.json 2>&1 | tee logs/$(date +%Y-%m-%d).log
