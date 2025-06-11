from flask import Flask, request, Response
import json
import os

app = Flask(__name__)

def resumen_inversiones(inversiones):
    # Construye un string con todas las inversiones actuales para enviar en el mensaje
    resumen = "Inversiones actuales:\n"
    for simbolo, operaciones in inversiones.items():
        total_cantidad = sum(op["cantidad"] for op in operaciones)
        resumen += f"{simbolo}: {total_cantidad} acciones\n"
    return resumen

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

    if comando == "BORRAR":
        # Esperamos formato: BORRAR SIMBOLO CANTIDAD PRECIO (para borrar una operación)
        try:
            _, simbolo, cantidad, precio = body.strip().split()
            cantidad = float(cantidad)
            precio = float(precio)
        except Exception:
            respuesta = "Formato para borrar: BORRAR SIMBOLO CANTIDAD PRECIO"
            return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')

        if simbolo in inversiones:
            # Buscamos la compra exacta para eliminarla
            encontrado = False
            for op in inversiones[simbolo]:
                if op["cantidad"] == cantidad and op["precio_compra"] == precio:
                    inversiones[simbolo].remove(op)
                    encontrado = True
                    break
            if not encontrado:
                respuesta = "No se encontró esa compra para borrar."
            else:
                # Si queda vacío, borrar la clave entera
                if not inversiones[simbolo]:
                    del inversiones[simbolo]
                respuesta = f"Compra borrada: {simbolo} {cantidad} acciones a ${precio}"
        else:
            respuesta = "No hay inversiones para ese símbolo."

    else:
        # Asumimos que es compra: SIMBOLO CANTIDAD PRECIO
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

    # Guardar cambios
    with open("inversiones.json", "w") as f:
        json.dump(inversiones, f, indent=4)

    # Agregar resumen actualizado al mensaje
    resumen = resumen_inversiones(inversiones)
    respuesta_completa = respuesta + "\n\n" + resumen

    return Response(f"<Response><Message>{respuesta_completa}</Message></Response>", mimetype='text/xml')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
