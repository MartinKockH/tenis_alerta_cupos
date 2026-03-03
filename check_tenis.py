import os
import requests
import hashlib

# Configuración
URL_OBJETIVO = "https://www.actividadeslbs.cl/taller/tenis-adulto-pato-cornejo/24684/18635485-0/339177"
NTFY_TOPIC = "alerta_tenis_braulio_2026"

cookie = os.environ.get("MI_COOKIE")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Cookie": cookie
}

def alertar(mensaje, prioridad="urgent"):
    requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", 
                  data=mensaje.encode('utf-8'),
                  headers={"Title": "🎾 ALERTA TENIS LBS", "Priority": prioridad})

try:
    response = requests.get(URL_OBJETIVO, headers=headers, timeout=15)
    html = response.text

    # 1. Validar sesión
    if "Iniciar sesión" in html or len(html) < 2000:
        alertar("❌ Tu cookie expiró o te bloquearon. Actualiza el secreto en GitHub.", "high")
        print("Sesión expirada.")
        exit()

    # 2. Crear una huella (hash) del HTML actual para comparar fácilmente
    # Limpiamos espacios en blanco extra que a veces cambian sin afectar el contenido
    html_limpio = "".join(html.split())
    hash_actual = hashlib.md5(html_limpio.encode('utf-8')).hexdigest()
    
    archivo_hash = "ultimo_hash.txt"

    # 3. Leer el hash de la ejecución anterior
    if os.path.exists(archivo_hash):
        with open(archivo_hash, "r") as f:
            hash_anterior = f.read().strip()
            
        if hash_actual != hash_anterior:
            # ¡EL HTML CAMBIÓ!
            print("¡Cambio detectado!")
            alertar("⚠️ LA PÁGINA HA CAMBIADO. Revisa rápido si se abrieron los cupos.", "urgent")
            
            # Actualizamos el archivo para que no envíe alertas infinitas
            with open(archivo_hash, "w") as f:
                f.write(hash_actual)
        else:
            print("La página sigue igual. No hay cambios.")
            
    else:
        # Es la primera vez que corre el script, guardamos el estado base
        print("Guardando estado inicial de la página...")
        with open(archivo_hash, "w") as f:
            f.write(hash_actual)

except Exception as e:
    print(f"Error en ejecución: {e}")
