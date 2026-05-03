import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import CORREO_ORIGEN, CONTRASENA_APP, CORREO_DESTINO

def enviar_alerta(resultados):
    """
    resultados = lista de dicts con keys:
    ticker, precio_actual, señal_hoy, prob_sube, capital_modelo, capital_bh
    """
    compras = [r for r in resultados if r['señal_hoy'] == 'COMPRAR']
    ventas  = [r for r in resultados if r['señal_hoy'] == 'VENDER']

    # Solo enviar si hay señales activas
    if not compras and not ventas:
        print("📭 Sin señales hoy — no se envía correo")
        return

    # ── Construir HTML del correo ──────────────────────────────────────────
    filas_compra = ""
    for r in compras:
        filas_compra += f"""
        <tr style="background:#0d2818">
          <td style="padding:12px;font-weight:700;color:#3fb950">{r['ticker']}</td>
          <td style="padding:12px">${r['precio_actual']:,.2f}</td>
          <td style="padding:12px;color:#3fb950">💚 COMPRAR</td>
          <td style="padding:12px">{r['prob_sube']*100:.1f}%</td>
          <td style="padding:12px">${r['capital_modelo']:,.0f}</td>
        </tr>"""

    filas_venta = ""
    for r in ventas:
        filas_venta += f"""
        <tr style="background:#2d1b1b">
          <td style="padding:12px;font-weight:700;color:#f85149">{r['ticker']}</td>
          <td style="padding:12px">${r['precio_actual']:,.2f}</td>
          <td style="padding:12px;color:#f85149">🔴 VENDER</td>
          <td style="padding:12px">{r['prob_sube']*100:.1f}%</td>
          <td style="padding:12px">${r['capital_modelo']:,.0f}</td>
        </tr>"""

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#0d1117;color:#e6edf3;padding:20px">
      <div style="max-width:700px;margin:0 auto">
        
        <h1 style="color:#58a6ff;border-bottom:1px solid #30363d;padding-bottom:16px">
          📈 IA Predictor — Señales del día
        </h1>
        
        <p style="color:#8b949e">Análisis automático de {len(resultados)} acciones</p>

        {'<h2 style="color:#3fb950;margin-top:24px">💚 Señales de COMPRA</h2><table width="100%" style="border-collapse:collapse;background:#161b22;border-radius:8px"><tr style="background:#21262d"><th style="padding:12px;text-align:left">Acción</th><th style="padding:12px;text-align:left">Precio</th><th style="padding:12px;text-align:left">Señal</th><th style="padding:12px;text-align:left">Prob. Sube</th><th style="padding:12px;text-align:left">Capital IA</th></tr>' + filas_compra + '</table>' if compras else ''}

        {'<h2 style="color:#f85149;margin-top:24px">🔴 Señales de VENTA</h2><table width="100%" style="border-collapse:collapse;background:#161b22;border-radius:8px"><tr style="background:#21262d"><th style="padding:12px;text-align:left">Acción</th><th style="padding:12px;text-align:left">Precio</th><th style="padding:12px;text-align:left">Señal</th><th style="padding:12px;text-align:left">Prob. Sube</th><th style="padding:12px;text-align:left">Capital IA</th></tr>' + filas_venta + '</table>' if ventas else ''}

        <div style="margin-top:32px;padding:16px;background:#161b22;border-radius:8px;border:1px solid #30363d">
          <p style="color:#d29922;margin:0">⚠️ <strong>Aviso:</strong> Este análisis es educativo. 
          Siempre investiga antes de invertir dinero real.</p>
        </div>

        <p style="color:#8b949e;font-size:0.8rem;margin-top:20px">
          Generado automáticamente por tu IA Predictor de Acciones
        </p>
      </div>
    </body></html>
    """

    # ── Enviar correo ──────────────────────────────────────────────────────
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📈 IA Predictor — {len(compras)} compras, {len(ventas)} ventas detectadas"
    msg['From']    = CORREO_ORIGEN
    msg['To']      = CORREO_DESTINO
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(CORREO_ORIGEN, CONTRASENA_APP)
            smtp.send_message(msg)
        print(f"✅ Correo enviado a {CORREO_DESTINO}")
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")