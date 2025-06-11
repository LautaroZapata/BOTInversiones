import os
from dotenv import load_dotenv

load_dotenv()

import yfinance as yf
import json
from twilio.rest import Client
from datetime import datetime

# 1. Leer inversiones con ruta relativa al script
base_path = os.path.dirname(__file__)
json_path = os.path.join(base_path, 'inversiones.json')

with open(json_path, "r") as file:
    inversiones = json.load(file)

# 2. Procesar inversiones
total_invertido = 0
valor_actual_total = 0
resumen = f"📊 *Estado de Inversiones - {datetime.now().strftime('%d/%m/%Y')}*\n"

for simbolo, compras in inversiones.items():
    cantidad_total = 0
    costo_total = 0

    for compra in compras:
        cantidad_total += compra["cantidad"]
        costo_total += compra["cantidad"] * compra["precio_compra"]

    total_invertido += costo_total

    accion = yf.Ticker(simbolo)
    precio_actual = accion.history(period="1d")["Close"][0]
    valor_actual = cantidad_total * precio_actual
    valor_actual_total += valor_actual

    ganancia = valor_actual - costo_total
    ganancia_pct = (ganancia / costo_total) * 100 if costo_total != 0 else 0

    color = "🟢" if ganancia >= 0 else "🔴"
    emoji_trend = "📈" if ganancia >= 0 else "📉"
    signo = "+" if ganancia >= 0 else ""

    resumen += f"\n{color} *{simbolo}*\n"
    resumen += f"💵 Invertiste: ${costo_total:.2f}\n"
    resumen += f"💰 Valor actual: ${valor_actual:.2f}\n"
    resumen += f"{emoji_trend} {'Ganancia' if ganancia >= 0 else 'Pérdida'}: {signo}${ganancia:.2f} ({signo}{ganancia_pct:.2f}%) {color}\n"

# 3. Resumen general
ganancia_total = valor_actual_total - total_invertido
ganancia_total_pct = (ganancia_total / total_invertido) * 100 if total_invertido != 0 else 0
color_final = "🟢" if ganancia_total >= 0 else "🔴"
signo_final = "+" if ganancia_total >= 0 else ""

resumen += "\n-----------------------\n"
resumen += "📋 *Resumen General*\n"
resumen += f"💸 Total invertido: ${total_invertido:.2f}\n"
resumen += f"📊 Valor actual: ${valor_actual_total:.2f}\n"
resumen += f"{color_final} *{'Ganancia' if ganancia_total >= 0 else 'Pérdida'} neta: {signo_final}${ganancia_total:.2f} ({signo_final}{ganancia_total_pct:.2f}%)*\n"

# 4. Leer variables entorno para Twilio
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
from_whatsapp_number = os.environ.get("TWILIO_WHATSAPP_FROM")
to_whatsapp_number = os.environ.get("TWILIO_WHATSAPP_TO")

if not all([account_sid, auth_token, from_whatsapp_number, to_whatsapp_number]):
    raise Exception("Error: Falta alguna variable de entorno de Twilio. Revisa tu archivo .env")

client = Client(account_sid, auth_token)

message = client.messages.create(
    body=resumen,
    from_=from_whatsapp_number,
    to=to_whatsapp_number
)

print("✅ Mensaje enviado por WhatsApp:", message.sid)
