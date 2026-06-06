# 🎯 GUÍA DEFINITIVA: Cómo Usar el Bot Correctamente

## ✅ Tu Código HBO Max Actual

**🔑 CÓDIGO: F6F6F6**

Este código ya fue enviado a tu Telegram.

## 📱 Los Mensajes SÍ LLEGANa Telegram

Según tu captura:
- ✅ Mensaje de prueba recibido (04:08)
- ✅ Código HBO recibido (04:16)
- ✅ Comunicación funcionando perfectamente

## ⚠️ EL PROBLEMA

Estás ejecutando **scripts manuales**, pero el bot tiene un modo **automático** que debe correr todo el tiempo.

## 🚀 SOLUCIÓN: Ejecutar el Bot Automático

### Paso 1: Detener Cualquier Proceso Actual

Si tienes algún script corriendo, deténlo con `Ctrl+C`.

### Paso 2: Ejecutar el Bot Completo

```bash
python main.py
```

Deberías ver:
```
============================================================
🤖 Telegram Streaming Account Manager Bot
============================================================
🔧 Initializing database...
✅ Database initialized
🚀 Starting bot...
✅ Email monitoring started in background
✅ Scheduler started
```

### Paso 3: Dejar el Bot Corriendo

**IMPORTANTE**: NO cierres la ventana. El bot debe estar corriendo TODO EL TIEMPO.

## 🔄 Cómo Funciona Automáticamente

Una vez que `python main.py` está corriendo:

1. **Email Monitor**: Revisa tu Gmail cada 60 segundos
2. **Detección**: Cuando llega un email de HBO Max automáticamente:
   - Extrae el destinatario (`s*********@gmail.com`)
   - Valida que sea email de seguridad
   - Extrae el código
   - Lo envía a Telegram
3. **Sin intervención**: Todo es automático

## 📋 Flujo Completo Automático

```
HBO Max envía código → Gmail lo reenvía → Bot lo detecta (en 60s)
                                               ↓
                                        Bot extrae código
                                               ↓
                                     Bot lo envía a Telegram
                                               ↓
                                         Tú recibes el código
```

## 🧪 Para Probar Que Funciona

### Opción 1: Solicitar Nuevo Código HBO

1. Asegúrate que `python main.py` está corriendo
2. Ve a HBO Max
3. Solicita código para `s**********o@gmail.com`
4. Espera máximo 60 segundos
5. El código llegará automáticamente a Telegram

### Opción 2: Marcar Email Actual como No Leído

1. Abre Gmail
2. Marca el email HBO como "No leído"
3. El bot lo detectará en el próximo ciclo (máx 60s)
4. Te enviará el código de nuevo

## ❌ Lo Que NO Debes Hacer

- ❌ NO ejecutar scripts manuales mientras el bot está corriendo
- ❌ NO cerrar la terminal donde corre `python main.py`
- ❌ NO tener múltiples instancias del bot corriendo

## ✅ Lo Que Debes Hacer

- ✅ Ejecutar `python main.py` UNA vez
- ✅ Dejarlo corriendo
- ✅ Solicitar códigos normalmente en HBO Max
- ✅ Los códigos llegarán automáticamente a Telegram

## 🔍 Verificar Que el Bot Está Corriendo

### En la Terminal

Deberías ver logs cada vez que:
- Se conecta al email server
- Procesa un email
- Envía un mensaje

### En Telegram

El bot responderá a comandos:
- `/list` - Ver tus cuentas
- `/historial` - Ver códigos recibidos
- `/cmds` - Ver ayuda

## 💡 Para Ejecutar en Segundo Plano (Opcional)

### Windows PowerShell:
```powershell
Start-Process python -ArgumentList "main.py" -WindowStyle Hidden
```

### O simplemente minimiza la ventana y déjala corriendo.

## 🎯 Resumen

1. **Ejecuta UNA vez**: `python main.py`
2. **Déjalo corriendo**: No cierres la terminal
3. **Solicita códigos**: En HBO Max normalmente
4. **Recibe automáticamente**: En Telegram en máx 60s

Todo lo demás (scripts de diagnóstico, send_code_now.py, etc.) son HERRAMIENTAS DE DEBUGGING, no para uso normal.

## ✅ Tu Configuración Actual

- ✅ Código extraído correctamente: F6F6F6
- ✅ Telegram funcionando: @AccessLotus_Bot
- ✅ Base de datos configurada: s**********@gmail.com → Usuario 8188519256
- ✅ Platform config arreglado: Detecta "Urgente: Tu..."

**TODO ESTÁ LISTO**. Solo necesitas ejecutar `python main.py` y dejarlo corriendo.
