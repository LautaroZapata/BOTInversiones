from flask import Flask, request, Response
import json
import os
import traceback

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    try:
        print("Nuevo mensaje recibido")
        from_number = request.values.get('From', '')
        body = request.values.get('Body', '')
        print(f"De: {from_number}, Mensaje: {body}")

        # Parsear el mensaje
        try:
            simbolo, cantidad, precio = body.strip().split()
            cantidad = float(cantidad)
            precio = float(precio)
            print(f"Datos parseados: {simbolo}, {cantidad}, {precio}")
        except Exception:
            respuesta = "Formato incorrecto. Usa: SIMBOLO CANTIDAD PRECIO"
            print("Error en parseo del mensaje")
            return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')

        # Crear archivo si no existe
        if not os.path.exists("inversiones.json"):
            with open("inversiones.json", "w") as f:
                f.write("{}")
            print("Archivo inversiones.json creado")

        # Leer inversiones
        with open("inversiones.json", "r") as f:
            inversiones = json.load(f)
        print("Archivo inversiones.json leído")

        # Actualizar inversiones
        if simbolo in inversiones:
            inversiones[simbolo].append({"cantidad": cantidad, "precio_compra": precio})
        else:
            inversiones[simbolo] = [{"cantidad": cantidad, "precio_compra": precio}]

        with open("inversiones.json", "w") as f:
            json.dump(inversiones, f, indent=4)
        print("Archivo inversiones.json actualizado")

        respuesta = f"Compra registrada: {simbolo} {cantidad} acciones a ${precio}"

    except Exception as e:
        print("Error inesperado:", e)
        traceback.print_exc()
        respuesta = f"Error procesando mensaje."

    return Response(f"<Response><Message>{respuesta}</Message></Response>", mimetype='text/xml')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Iniciando app en puerto {port}")
    app.run(host="0.0.0.0", port=port)
