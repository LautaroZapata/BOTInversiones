from flask import Flask, request, Response
import json
import os
from twilio.rest import Client
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import yfinance as yf

app = Flask(__name__)

# Función para enviar resumen por WhatsApp usando Twilio
def generar_resumen_completo():
    base_path = os.path.dirname(__file__)
    json_path = os.path.join(base_path, 'inversiones.json')

    with open(json_path, "r") as file:
        inversiones = json.load(file)

    total_invertido = 0
    valor_actual_total = 0
    resumen = f"📊 *Estado de Inversiones - {datetime.now().strftime('%d/%m/%Y %H:%M')}*\n"

    for simbolo, compras in inversiones.items():
        cantidad_total = 0
        costo_total = 0

        for compra in compras:
            cantidad_total += compra["cantidad"]
            costo_total += compra["cantidad"] * compra["precio_compra"]

        total_invertido += costo_total

        accion = yf.Ticker(simbolo)
        precio_actual = accion.history(period="1d")["Close"].iloc[0]

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

    ganancia_total = valor_actual_total - total_invertido
    ganancia_total_pct = (ganancia_total / total_invertido) * 100 if total_invertido != 0 else 0
    color_final = "🟢" if ganancia_total >= 0 else "🔴"
    signo_final = "+" if ganancia_total >= 0 else ""

    resumen += "\n-----------------------\n"
    resumen += "📋 *Resumen General*\n"
    resumen += f"💸 Total invertido: ${total_invertido:.2f}\n"
    resumen += f"📊 Valor actual: ${valor_actual_total:.2f}\n"
    resumen += f"{color_final} *{'Ganancia' if ganancia_total >= 0 else 'Pérdida'} neta: {signo_final}${ganancia_total:.2f} ({signo_final}{ganancia_total_pct:.2f}%)*\n"

    return resumen

def enviar_resumen_twilio():
    resumen = generar_resumen_completo()

    # Leer variables de entorno para Twilio
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_whatsapp_number = os.environ.get("TWILIO_WHATSAPP_FROM")
    to_whatsapp_number = os.environ.get("TWILIO_WHATSAPP_TO")

    if not all([account_sid, auth_token, from_whatsapp_number, to_whatsapp_number]):
        print("Error: Falta alguna variable de entorno de Twilio.")
        return

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=resumen,
        from_=from_whatsapp_number,
        to=to_whatsapp_number
    )

    print(f"✅ Mensaje automático enviado: {message.sid}")

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    from_number = request.values.get('From', '')
    body = request.values.get('Body', '')

    try:
        comando = body.strip().split()[0].upper()
    except Exception:
        comando = ""

    # Leer JSON actual
    with open("inversiones.json", "r") as f:
        inversiones = json.load(f)

    if comando == "RESUMEN":
        resumen = generar_resumen_completo()
        return Response(f"<Response><Message>{resumen}</Message></Response>", mimetype='text/xml')

    if comando == "BORRAR":
        try:
            _, simbolo, cantidad, precio = body.strip().split()
            cantidad = float(cantidad)
            precio = float(precio)
        except Exception:
            respuesta = "Formato para borrar: BORRAR SIMBOLO CANTIDAD PRECIO"
            return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')

        if simbolo in inversiones:
            encontrado = False
            for op in inversiones[simbolo]:
                if op["cantidad"] == cantidad and op["precio_compra"] == precio:
                    inversiones[simbolo].remove(op)
                    encontrado = True
                    break
            if not encontrado:
                respuesta = "No se encontró esa compra para borrar."
            else:
                if not inversiones[simbolo]:
                    del inversiones[simbolo]
                respuesta = f"Compra borrada: {simbolo} {cantidad} acciones a ${precio}"
        else:
            respuesta = "No hay inversiones para ese símbolo."

    else:
        try:
            simbolo, cantidad, precio = body.strip().split()
            cantidad = float(cantidad)
            precio = float(precio)
        except Exception:
            respuesta = "Formato incorrecto. Usa: SIMBOLO CANTIDAD PRECIO o BORRAR SIMBOLO CANTIDAD PRECIO"
            return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')

        if simbolo in inversiones:
            inversiones[simbolo].append({"cantidad": cantidad, "precio_compra": precio})
        else:
            inversiones[simbolo] = [{"cantidad": cantidad, "precio_compra": precio}]
        respuesta = f"Compra registrada: {simbolo} {cantidad} acciones a ${precio}"

    with open("inversiones.json", "w") as f:
        json.dump(inversiones, f, indent=4)

    resumen = "\n\nInversiones actuales:\n"
    for simbolo, operaciones in inversiones.items():
        total_cantidad = sum(op["cantidad"] for op in operaciones)
        resumen += f"{simbolo}: {total_cantidad} acciones\n"

    respuesta_completa = respuesta + resumen
    return Response(f"<Response><Message>{respuesta_completa}</Message></Response>", mimetype='text/xml')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    # Configurar scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(enviar_resumen_twilio, 'cron', hour='12,17', minute=0)  # 12:00 y 17:00
    scheduler.start()

    atexit.register(lambda: scheduler.shutdown())

    app.run(host="0.0.0.0", port=port)
