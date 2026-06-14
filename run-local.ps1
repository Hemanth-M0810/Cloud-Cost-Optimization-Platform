# Quick start script for Windows

echo "Installing dependencies..."
pip install -r services/requirements-dev.txt

echo "Starting approval-api with mock data..."
cd services/approval-api
$env:USE_MOCK_DATA = "true"
$env:PYTHONPATH = "../.."
uvicorn main:app --reload --port 8000

Write-Host "Dashboard API available at: http://localhost:8000"
Write-Host "Open dashboard/index.html in your browser"
