from flask import Flask, request, Response
import json
import os

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    from_number = request.values.get('From', '')
    body = request.values.get('Body', '')

    # Parsear el mensaje: ejemplo "AAPL 0.01 135.00"
    try:
        simbolo, cantidad, precio = body.strip().split()
        cantidad = float(cantidad)
        precio = float(precio)
    except Exception:
        respuesta = "Formato incorrecto. Usa: SIMBOLO CANTIDAD PRECIO"
        return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')

    # Leer JSON
    with open("inversiones.json", "r") as f:
        inversiones = json.load(f)

    # Actualizar JSON
    if simbolo in inversiones:
        inversiones[simbolo].append({"cantidad": cantidad, "precio_compra": precio})
    else:
        inversiones[simbolo] = [{"cantidad": cantidad, "precio_compra": precio}]

    with open("inversiones.json", "w") as f:
        json.dump(inversiones, f, indent=4)

    respuesta = f"Compra registrada: {simbolo} {cantidad} acciones a ${precio}"

    return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
