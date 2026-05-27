if (-not (Test-Path -LiteralPath ".\.env")) {
  Write-Host "Falta el archivo .env. Copia .env.example a .env y configura DB_PASSWORD con tu clave de MySQL." -ForegroundColor Red
  exit 1
}

$env:DB_ENGINE = "mysql"
Remove-Item Env:\SQLITE_NAME -ErrorAction SilentlyContinue

.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
