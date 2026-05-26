# 🔐 Guía para Crear Contraseña de Aplicación de Gmail

Para que el bot pueda leer correos, necesitas una contraseña especial. No uses tu contraseña normal.

## Paso 1: Activar Verificación en 2 Pasos (Si no la tienes)
1. Ve a **[myaccount.google.com/security](https://myaccount.google.com/security)**.
2. Baja hasta la sección "Cómo inicias sesión en Google".
3. Si "Verificación en dos pasos" dice "Desactivada", haz clic y actívala. (Necesitarás tu teléfono).

## Paso 2: Crear la Contraseña de Aplicación
1. Una vez activada la verificación en 2 pasos, ve directamente a:
   👉 **[https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)**
   
   *(Si el enlace no funciona, ve a Seguridad > Verificación en dos pasos > Ve al final de la página > Contraseñas de aplicaciones)*.

2. **Nombre de la app**: Escribe `Bot Telegram`.
3. Haz clic en **Crear**.
4. Te dará una contraseña de 16 letras (ejemplo: `xxxx xxxx xxxx xxxx`).

## Paso 3: Configurar el Bot
1. Copia esa contraseña.
2. Abre el archivo `.env` en tu proyecto.
3. Pégala en `EMAIL_PASSWORD` (sin espacios es mejor, pero con espacios también suele funcionar).

```env
EMAIL_USERNAME=tu_correo@gmail.com
EMAIL_PASSWORD=xxxxxxxxxxxxxxxx
```
