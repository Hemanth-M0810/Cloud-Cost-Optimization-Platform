# Quick start script for Windows (Azure data mode)

Write-Host "Installing dependencies..."
pip install -r services/requirements-dev.txt

if (Test-Path ".env") {
	Write-Host "Loading environment variables from .env ..."
	Get-Content ".env" | ForEach-Object {
		if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
		$parts = $_ -split '=', 2
		if ($parts.Length -eq 2) {
			[System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
		}
	}
}

$env:USE_MOCK_DATA = "false"
$env:PYTHONPATH = "../.."

if (-not $env:BLOB_ACCOUNT_URL) {
	Write-Error "BLOB_ACCOUNT_URL is not set. Add it to .env or export it in this shell."
	exit 1
}

Write-Host "Starting approval-api with Azure Blob data..."
Set-Location services/approval-api
uvicorn main:app --reload --port 8000

Write-Host "Dashboard available at: http://127.0.0.1:8000"
