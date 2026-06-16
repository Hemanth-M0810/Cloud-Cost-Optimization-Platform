#!/bin/bash
# Quick start script to run the dashboard locally with Azure data

set -e

echo "Installing dependencies..."
pip install -r services/requirements-dev.txt

if [ -f .env ]; then
	echo "Loading environment variables from .env ..."
	set -a
	# shellcheck disable=SC1091
	source .env
	set +a
fi

export USE_MOCK_DATA=false

if [ -z "${BLOB_ACCOUNT_URL:-}" ]; then
	echo "BLOB_ACCOUNT_URL is not set. Add it to .env or export it in this shell."
	exit 1
fi

echo "Starting approval-api with Azure Blob data..."
cd services/approval-api
export PYTHONPATH=../..
uvicorn main:app --reload --port 8000

echo "Dashboard available at: http://127.0.0.1:8000"
