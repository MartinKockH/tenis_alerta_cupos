import asyncio
from playwright.async_api import async_playwright
import requests
import os

# CONFIGURACIÓN
URL = "https://www.actividadeslbs.cl/categorias/talleres-deportivos"
NTFY_TOPIC = "alerta_tenis_braulio_2026"
ARCHIVO_CONTEO = "conteo_tenis.txt"

# SELECTOR ROBUSTO: Buscamos el input real de Quasar, ignorando el ID dinámico
SELECTOR_BUSCADOR = ".q-field__native"

async def main():
    print("🚀 Iniciando navegador en modo invisible...")
    async with async_playwright() as p:
        # Definimos un tamaño de pantalla de PC (1280x800) para que no cargue la versión móvil
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        try:
            print(f"🔗 Cargando {URL}...")
            # Esperamos a que la red esté inactiva (SPA cargada)
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            
            # 1. Buscar el cuadro de texto y escribir "tenis"
            print(f"⌨️ Intentando encontrar el buscador con el selector: {SELECTOR_BUSCADOR}")
            await page.wait_for_selector(SELECTOR_BUSCADOR, timeout=10000)
            
            # Limpiamos el campo por si acaso y escribimos
            await page.fill(SELECTOR_BUSCADOR, "tenis")
            await page.press(SELECTOR_BUSCADOR, "Enter")
            
            # 2. Esperar a que la página reaccione (animación de filtrado de Vue/Quasar)
            print("⏳ Esperando que aparezcan los resultados...")
            await asyncio.sleep(5) 

            # 3. Contar los talleres usando la palabra "Inscribirse" que aparece en cada tarjeta
            tarjetas = await page.locator("text='Inscribirse'").all()
            conteo_actual = len(tarjetas)
            
            print(f"📊 Talleres de tenis encontrados en pantalla: {conteo_actual}")
            
            # --- LÓGICA DE ALERTA ---
            if os.path.exists(ARCHIVO_CONTEO):
                with open(ARCHIVO_CONTEO, "r") as f:
                    conteo_anterior = int(f.read().strip())
                
                if conteo_actual != conteo_anterior and conteo_actual > 0:
                    diff = conteo_actual - conteo_anterior
                    estado = "AUMENTARON" if diff > 0 else "DISMINUYERON"
                    msg = f"🎾 ¡CAMBIO! Los talleres de tenis {estado}. Antes {conteo_anterior}, ahora {conteo_actual}."
                    
                    requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", 
                                  data=msg.encode('utf-8'),
                                  headers={
                                      "Title": "TENIS LBS", 
                                      "Priority": "urgent",
                                      "Tags": "tennis,rotating_light",
                                      "Click": URL # Al tocar la notificación se abre la página
                                  })
                    print(f"🔔 Alerta enviada a ntfy: {msg}")
                else:
                    print("✅ El número de talleres sigue igual. Sin cambios.")
            else:
                print("💾 Primera ejecución registrada. No se envía alerta todavía.")
            
            # Guardamos el conteo actual para la próxima ejecución
            with open(ARCHIVO_CONTEO, "w") as f:
                f.write(str(conteo_actual))

        except Exception as e:
            print(f"❌ Error crítico: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    # Esta es la forma correcta de correr código async en un script de Python puro
    asyncio.run(main())
