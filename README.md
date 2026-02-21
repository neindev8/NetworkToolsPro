---

**Network Tools Pro v1.2 — GUI network diagnostics without admin privileges**

Tkinter desktop app for Windows/Linux that provides ping, traceroute, keepalive monitoring, and speed testing — all without requiring administrator permissions.

**Core features:**
- Ping with real-time output (ICMP → TCP fallback, no admin needed)
- Traceroute with live hop-by-hop display (TCP/UDP hybrid, no admin needed)
- Keepalive monitor with 3 strategies: constant, rotate, failover
- Speed test: latency (10-ping), download, upload (simulated), jitter
- System tray integration (minimize-to-tray, background operation)
- Persistent config with auto-restore of keepalive state on relaunch
- Daily rotating log files

**Architecture:**
- `network_tools.py` — main app, tabbed Tkinter GUI, queue-based async UI updates
- `ping_module.py` — custom ICMP ping with TCP fallback (no raw socket needed)
- `traceroute_module.py` — TCP-based traceroute with TTL manipulation
- Graceful fallback to system `ping`/`tracert` if custom modules unavailable
- Threaded operations keep UI responsive

**Build & distribution:**
- `build_exe.py` / `COMPILAR_A_EXE.bat` — PyInstaller single-file EXE compilation
- `INSTALAR_Y_EJECUTAR.bat` — one-click install + run for Windows
- Hidden imports configured for PyInstaller to bundle custom modules
- Frozen-exe-aware path resolution for config and logs

**Dependencies:** requests, pillow, pystray, pyinstaller
