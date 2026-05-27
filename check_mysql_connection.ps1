if (-not (Test-Path -LiteralPath ".\.env")) {
  Write-Host "Falta el archivo .env. Copia .env.example a .env y configura DB_PASSWORD." -ForegroundColor Red
  exit 1
}

$env:DB_ENGINE = "mysql"
Remove-Item Env:\SQLITE_NAME -ErrorAction SilentlyContinue

.\.venv\Scripts\python.exe manage.py shell -c "from django.db import connection; print(connection.settings_dict['ENGINE'], connection.settings_dict['NAME'], connection.settings_dict['USER'], connection.settings_dict['HOST'], connection.settings_dict['PORT']); connection.ensure_connection(); print('MYSQL_OK')"
