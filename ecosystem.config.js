// Configuracion pm2 para servir SaludBot con gunicorn en produccion.
// El deploy la usa con: pm2 startOrReload ecosystem.config.js --update-env
module.exports = {
  apps: [
    {
      name: 'saludbot',
      cwd: '/var/www/chat_bot_salud/app',
      script: '.venv/bin/gunicorn',
      args: 'cesfam_chatbot.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 60',
      // gunicorn no es un script Node: pm2 lo ejecuta directo, sin interprete.
      interpreter: 'none',
      autorestart: true,
      max_restarts: 10,
      // Django carga el resto de la config desde .env via python-dotenv.
      env: {
        DJANGO_SETTINGS_MODULE: 'cesfam_chatbot.settings',
      },
    },
  ],
}
