NETWORK TOOLS PRO v1.2
======================

NOVEDADES v1.2
--------------
✓ Ping y Traceroute con OUTPUT EN VIVO (como los comandos originales)
✓ Speed Test COMPLETO: Latencia + Download + Upload + Jitter
✓ Speed Test configurable (duración, buffer)
✓ Interfaz mejorada con actualizaciones en tiempo real

INSTALACIÓN Y USO
-----------------

Windows / Linux:
1. pip install -r requirements.txt
2. python network_tools.py

Compilar a EXE (Windows):
1. pip install -r requirements.txt
2. python build_exe.py
3. EXE en: dist\NetworkToolsPro.exe

SIN PERMISOS DE ADMIN REQUERIDOS
---------------------------------
- Ping personalizado: Usa TCP cuando ICMP no disponible
- Traceroute personalizado: Método TCP/UDP híbrido
- Funcionan en Windows y Linux sin permisos especiales
- Output en tiempo real como comandos originales

CARACTERÍSTICAS
---------------
✓ Ping (sin admin, output en vivo)
✓ Traceroute (sin admin, output en vivo)
✓ Keepalive (mantener conexión activa)
✓ Speed Test completo (latencia, download, upload, jitter)
✓ System Tray
✓ Auto-inicio de keepalive
✓ Configuración persistente

SPEED TEST MEJORADO
-------------------
Ahora incluye:
- Test de latencia (10 pings)
- Velocidad de descarga (configurable)
- Velocidad de subida (simulado)
- Cálculo de jitter
- Estadísticas detalladas (min/max/avg)
- Actualización en tiempo real
- Configuración de duración y buffer

SYSTEM TRAY
-----------
- Al cerrar con [X]: va al system tray
- Icono siempre visible mientras la app corre
- Clic derecho: Mostrar/Ocultar/Salir

KEEPALIVE (Para conexiones inestables)
---------------------------------------
Estrategias:
- Constant: Mismo sitio siempre
- Rotate: Rota entre todos
- Failover: Cambia solo si falla (RECOMENDADO)

Configuración recomendada:
- Intervalo: 30 segundos
- Protocolo: https
- Estrategia: failover

MÓDULOS INCLUIDOS
------------------
- network_tools.py - Aplicación principal con UI mejorada
- ping_module.py - Ping con callback para output en vivo
- traceroute_module.py - Traceroute con callback para output en vivo

ARCHIVOS GENERADOS
------------------
- config.json - Configuración (automático)
- logs/ - Logs diarios (automático)

USO RÁPIDO
----------
1. Ejecuta: python network_tools.py
2. Prueba Ping/Traceroute - verás el output en tiempo real
3. Keepalive > Cargar sites.txt > Iniciar
4. Speed Test > Configura duración > Iniciar Test Completo
5. Configuración > ☑️ Auto-iniciar keepalive > Guardar
6. Cierra con [X] (va a tray)

VENTAJAS
--------
✓ No requiere permisos de administrador
✓ Output en tiempo real (como comandos originales)
✓ Speed test completo y profesional
✓ Funciona en cualquier Windows/Linux
✓ System tray integrado
✓ Auto-restauración de estado
✓ Logs automáticos
✓ Compilable a EXE
