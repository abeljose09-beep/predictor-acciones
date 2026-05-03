import schedule, time, subprocess, json, sys
from datetime import datetime
from alertas import enviar_alerta
from config import ACCIONES, HORA_EJECUCION

def analizar_todas():
    print(f"\n{'='*50}")
    print(f"🤖 Iniciando análisis — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📊 Analizando {len(ACCIONES)} acciones: {', '.join(ACCIONES)}")
    print(f"{'='*50}")

    resultados = []

    for ticker in ACCIONES:
        print(f"\n⏳ Procesando {ticker}...")
        try:
            result = subprocess.run(
                [sys.executable, 'modelo.py', ticker],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                resultados.append(data)

                emoji = '💚' if data['señal_hoy'] == 'COMPRAR' else '🔴' if data['señal_hoy'] == 'VENDER' else '🟡'
                print(f"  {emoji} {ticker}: {data['señal_hoy']} | Precio: ${data['precio_actual']} | Prob subida: {data['prob_sube']*100:.1f}%")
            else:
                print(f"  ❌ {ticker}: Error — {result.stderr[:100]}")
        except Exception as e:
            print(f"  ❌ {ticker}: {e}")

    print(f"\n📧 Enviando resumen por correo...")
    enviar_alerta(resultados)

    compras = [r for r in resultados if r['señal_hoy'] == 'COMPRAR']
    esperas = [r for r in resultados if r['señal_hoy'] == 'ESPERAR']
    ventas  = [r for r in resultados if r['señal_hoy'] == 'VENDER']

    print(f"\n{'='*50}")
    print(f"✅ RESUMEN FINAL")
    print(f"  💚 COMPRAR: {len(compras)} — {[r['ticker'] for r in compras]}")
    print(f"  🔴 VENDER:  {len(ventas)}  — {[r['ticker'] for r in ventas]}")
    print(f"  🟡 ESPERAR: {len(esperas)}")
    print(f"{'='*50}\n")

# ── Programar ejecución diaria ─────────────────────────────────────────────
print(f"⏰ Programado para correr cada día a las {HORA_EJECUCION}")
print(f"📊 Acciones: {', '.join(ACCIONES)}")
print(f"💡 Presiona Ctrl+C para detener\n")

schedule.every().day.at(HORA_EJECUCION).do(analizar_todas)

# Opción: correr UNA VEZ ahora para probar
respuesta = input("¿Correr análisis AHORA también? (s/n): ")
if respuesta.lower() == 's':
    analizar_todas()

# Mantener corriendo
while True:
    schedule.run_pending()
    time.sleep(60)