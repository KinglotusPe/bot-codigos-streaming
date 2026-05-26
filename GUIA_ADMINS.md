# 📚 Guía para Administradores: Sistema de Streaming

Bienvenido al equipo. Esta guía te enseñará cómo gestionar tus cuentas y clientes usando el bot.

## 🚀 1. Cómo empezar

El Owner te dará acceso al bot. Una vez tengas acceso, podrás gestionar tus propias cuentas.

### Comandos Principales

| Comando | Qué hace | Ejemplo |
| :--- | :--- | :--- |
| `/reg` | **Registra** una cuenta nueva en el sistema | `/reg netflix micuenta@gmail.com` |
| `/asig` | **Asigna** un cliente a una cuenta | `/asig 123456789 netflix micuenta@gmail.com` |
| `/miscorreos` | Muestra **todas** tus cuentas registradas | `/miscorreos` |
| `/renov` | **Renueva** a un cliente por 30 días más | `/renov 123456789` |
| `/venc` | Muestra clientes que **vencen** en 7 días | `/venc` |

---

## ⚙️ 2. Configuración OBLIGATORIA (Paso a Paso)

Para que el sistema funcione, **DEBES** configurar el reenvío de correos en cada cuenta de streaming que vendas.

**Si no haces esto, el cliente NUNCA recibirá los códigos.**

### Pasos para configurar el reenvío (Gmail):

1.  Entra al correo de la cuenta de streaming (ej: `cuenta_netflix@gmail.com`).
2.  Ve a **Configuración** (rueda dentada) > **Ver todos los ajustes**.
3.  Ve a la pestaña **Reenvío y correo POP/IMAP**.
4.  Haz clic en **"Añadir una dirección de reenvío"**.
5.  Escribe el correo del sistema: **`gilbertogalardo5@gmail.com`**
6.  El sistema recibirá un código de confirmación. **Pídele al Owner que te lo pase.**
7.  Ingresa el código y verifica.
8.  **IMPORTANTE:** Selecciona la opción **"Reenviar una copia del correo entrante a..."** y guarda los cambios al final de la página.

---

## 🔄 3. Flujo de Venta (Ejemplo Real)

Supongamos que vendes una cuenta de Netflix a un cliente.

1.  **Registra la cuenta en el bot:**
    *   Escribe: `/reg netflix cuenta_netflix@gmail.com`
    *   *El bot te confirmará que la cuenta está registrada.*

2.  **Pídele al cliente su ID de Telegram:**
    *   Dile que inicie el bot (`@userinfobot`) para obtener su ID numérico (ej: `987654321`).

3.  **Asigna la cuenta al cliente:**
    *   Escribe: `/asig 987654321 netflix cuenta_netflix@gmail.com`
    *   *El bot le dará acceso inmediato por 30 días.*

4.  **¡Listo!**
    *   Ahora, cuando el cliente pida un código de hogar o restablecimiento, Netflix enviará el correo a `cuenta_netflix@gmail.com`.
    *   Gmail lo reenviará automáticamente al sistema.
    *   El bot lo leerá y se lo enviará a tu cliente por Telegram.

---

## 💡 Consejos

*   Usa `/miscorreos` frecuentemente para ver qué cuentas tienes libres.
*   Usa `/venc` cada semana para ver a quién debes cobrarle la renovación.
*   Si un cliente ya no paga, no necesitas hacer nada; el sistema lo corta automáticamente a los 30 días.
