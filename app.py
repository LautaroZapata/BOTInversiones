from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import datetime

app = Flask(__name__)

# Zona horaria de Montevideo
montevideo_tz = pytz.timezone('America/Montevideo')

# Simulación de envío de mensaje
def enviar_mensaje():
    ahora = datetime.datetime.now(montevideo_tz).strftime('%H:%M:%S')
    print(f"[{ahora}] 📩 Enviando mensaje automático al chat...")

# Inicializa y configura el scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(enviar_mensaje, 'cron', hour=11, minute=0, timezone=montevideo_tz)
scheduler.add_job(enviar_mensaje, 'cron', hour=17, minute=0, timezone=montevideo_tz)
scheduler.start()

@app.route('/')
def home():
    return "✅ Bot activo. Mensajes automáticos programados."

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
