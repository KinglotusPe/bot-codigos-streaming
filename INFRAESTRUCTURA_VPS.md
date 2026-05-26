# 🏢 Arquitectura e Infraestructura de Servidores (VPS)

> [!IMPORTANT]
> **DOCUMENTO CRÍTICO DE REFERENCIA**
> Este documento contiene el mapeo exacto de en qué servidor físico (VPS) se encuentra alojado cada Bot en producción tras la migración cruzada del 11 de Mayo de 2026. 
> **Siempre consulta este documento antes de realizar comandos SSH, reinicios o despliegues.**

---

## 📱 BOT SMS (`@FlashVerifyPeruBot`)
*El bot encargado de vender números virtuales y bypass de SMS.*

*   **Proveedor VPS:** RackNerd
*   **Dirección IP:** `172.245.137.93`
*   **Puerto SSH:** `22`
*   **Usuario:** `root`
*   **Método de Acceso:** Llave SSH (`id_vps_sms`) o Contraseña.
*   **Directorio del Proyecto:** `/root/bot-sms/`
*   **Servicio de Sistema:** `bot-sms.service` (Manejado con `systemctl restart bot-sms`)
*   **Webhook de Pagos (Cryptomus):** `http://172.245.137.93:49490/cryptomus/webhook` *(Asignado dinámicamente vía API en `url_callback`)*

---

## 🔑 BOT CÓDIGOS (`@AccessLotus_Bot`)
*El bot encargado de gestionar cuentas de streaming y pines.*

*   **Proveedor VPS:** RackNerd (Antigua VPS del Bot SMS)
*   **Dirección IP:** `23.94.29.30`
*   **Puerto SSH:** `49489` *(Atención al puerto personalizado)*
*   **Usuario:** `root`
*   **Método de Acceso:** Llave SSH (`id_vps_sms`)
*   **Directorio del Proyecto:** `/root/bot-codigos/`
*   **Servicio de Sistema:** `bot-codigos.service` (Manejado con `systemctl restart bot-codigos`)

---

## 🔒 Notas de DevSecOps
> [!WARNING]
> Nunca modifiques bases de datos en caliente sin antes detener el servicio de `systemd` correspondiente. Los respaldos de ambos bots en formato `.tar.gz` se encuentran guardados en el directorio `/root/` de sus respectivas máquinas, así como en la carpeta `d:\ideas\Bot-Codigos\` del entorno local del administrador.
