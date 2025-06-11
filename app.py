from flask import Flask, request, Response
import json
import os

app = Flask(__name__)

def guardar_inversiones(inversiones):
    with open("inversiones.json", "w") as f:
        json.dump(inversiones, f, indent=4)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    from_number = request.values.get('From', '')
    body = request.values.get('Body', '').strip()

    inversiones = {}
    try:
        with open("inversiones.json", "r") as f:
            inversiones = json.load(f)
    except FileNotFoundError:
        inversiones = {}

    # Comando borrar
    if body.upper().startswith("BORRAR "):
        try:
            _, simbolo, cantidad_str = body.split()
            cantidad = float(cantidad_str)
        except Exception:
            respuesta = "Formato incorrecto para borrar. Usa: BORRAR SIMBOLO CANTIDAD"
            return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')

        if simbolo in inversiones:
            lista = inversiones[simbolo]
            # Buscar inversión con esa cantidad para borrar
            for i, inv in enumerate(lista):
                if inv.get("cantidad") == cantidad:
                    lista.pop(i)
                    if not lista:
                        inversiones.pop(simbolo)
                    guardar_inversiones(inversiones)
                    respuesta = f"Inversión borrada: {simbolo} {cantidad} acciones."
                    return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')

            respuesta = f"No se encontró inversión con {cantidad} acciones en {simbolo}."
        else:
            respuesta = f"No hay inversiones para {simbolo}."
        return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')

    # Comando agregar compra (default)
    try:
        simbolo, cantidad_str, precio_str = body.split()
        cantidad = float(cantidad_str)
        precio = float(precio_str)
    except Exception:
        respuesta = "Formato incorrecto. Usa: SIMBOLO CANTIDAD PRECIO o BORRAR SIMBOLO CANTIDAD"
        return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')

    if simbolo in inversiones:
        inversiones[simbolo].append({"cantidad": cantidad, "precio_compra": precio})
    else:
        inversiones[simbolo] = [{"cantidad": cantidad, "precio_compra": precio}]

    guardar_inversiones(inversiones)
    respuesta = f"Compra registrada: {simbolo} {cantidad} acciones a ${precio}"
    return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
