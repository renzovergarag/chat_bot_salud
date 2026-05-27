$env:DB_ENGINE = "sqlite"
$env:SQLITE_NAME = "$env:TEMP\cesfam_chatbot.sqlite3"

.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
