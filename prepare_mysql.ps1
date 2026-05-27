if (-not (Test-Path -LiteralPath ".\.env")) {
  Write-Host "Falta el archivo .env. Configura DB_PASSWORD antes de preparar MySQL." -ForegroundColor Red
  exit 1
}

$env:DB_ENGINE = "mysql"
Remove-Item Env:\SQLITE_NAME -ErrorAction SilentlyContinue

.\.venv\Scripts\python.exe manage.py migrate solicitudes --fake
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

.\.venv\Scripts\python.exe manage.py migrate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

.\.venv\Scripts\python.exe manage.py showmigrations
