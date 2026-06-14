#!/bin/bash
# Quick start script to run the dashboard locally with mock data

set -e

echo "Installing dependencies..."
pip install -r services/requirements-dev.txt

echo "Starting approval-api with mock data..."
cd services/approval-api
export USE_MOCK_DATA=true
export PYTHONPATH=../..
uvicorn main:app --reload --port 8000

echo "Dashboard available at: http://localhost:8000"
echo "Open dashboard/index.html in your browser"
