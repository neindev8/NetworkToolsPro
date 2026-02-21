import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import threading
import time
import json
import os
import platform
import subprocess
import socket
import requests
from datetime import datetime
import sys
from queue import Queue

# Importar módulos personalizados
try:
    import ping_module
    import traceroute_module
    CUSTOM_MODULES = True
except ImportError:
    CUSTOM_MODULES = False

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

class NetworkToolsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Tools Pro v1.2")
        self.root.geometry("900x600")

        # Base directory: next to the EXE (frozen) or next to the script
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Variables
        self.config_file = os.path.join(self.base_dir, "config.json")
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.keepalive_running = False
        self.keepalive_thread = None
        self.config = self.load_config()
        self.update_queue = Queue()
        self.tray_icon = None
        
        # Crear directorio de logs
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        
        # Crear interfaz
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Iniciar system tray
        if TRAY_AVAILABLE:
            self.setup_tray()
        
        # Procesar cola
        self.process_queue()
        
        # Restaurar estado si está configurado
        if self.config.get("auto_start_keepalive", False) and self.config.get("last_keepalive_running", False):
            self.root.after(1000, self.auto_start_keepalive)
    
    def load_config(self):
        default = {
            "keepalive_interval": 30,
            "keepalive_protocol": "https",
            "keepalive_strategy": "failover",
            "sites_list": [
                "https://www.google.com",
                "https://www.cloudflare.com",
                "https://1.1.1.1"
            ],
            "custom_sites": [],
            "ping_count": 4,
            "traceroute_max_hops": 30,
            "auto_start_keepalive": False,
            "last_keepalive_running": False
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    default.update(loaded)
            except:
                pass
        
        return default
    
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def log_event(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        log_file = os.path.join(self.logs_dir, f"log_{datetime.now().strftime('%Y%m%d')}.txt")
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
        except:
            pass
    
    def create_widgets(self):
        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Pestañas
        self.create_ping_tab()
        self.create_traceroute_tab()
        self.create_keepalive_tab()
        self.create_speedtest_tab()
        self.create_config_tab()
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Listo", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_ping_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Ping")
        
        # Controles
        ctrl = ttk.Frame(frame)
        ctrl.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(ctrl, text="Host:").pack(side='left', padx=5)
        self.ping_host = ttk.Entry(ctrl, width=30)
        self.ping_host.pack(side='left', padx=5)
        self.ping_host.insert(0, "google.com")
        
        ttk.Label(ctrl, text="Count:").pack(side='left', padx=5)
        self.ping_count = ttk.Entry(ctrl, width=10)
        self.ping_count.pack(side='left', padx=5)
        self.ping_count.insert(0, "4")
        
        self.ping_btn = ttk.Button(ctrl, text="Ping", command=self.run_ping)
        self.ping_btn.pack(side='left', padx=5)
        
        # Output
        self.ping_output = scrolledtext.ScrolledText(frame, height=20)
        self.ping_output.pack(fill='both', expand=True, padx=10, pady=5)
    
    def create_traceroute_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Traceroute")
        
        # Controles
        ctrl = ttk.Frame(frame)
        ctrl.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(ctrl, text="Host:").pack(side='left', padx=5)
        self.trace_host = ttk.Entry(ctrl, width=30)
        self.trace_host.pack(side='left', padx=5)
        self.trace_host.insert(0, "google.com")
        
        ttk.Label(ctrl, text="Max Hops:").pack(side='left', padx=5)
        self.trace_hops = ttk.Entry(ctrl, width=10)
        self.trace_hops.pack(side='left', padx=5)
        self.trace_hops.insert(0, "30")
        
        self.trace_btn = ttk.Button(ctrl, text="Traceroute", command=self.run_traceroute)
        self.trace_btn.pack(side='left', padx=5)
        
        # Output
        self.trace_output = scrolledtext.ScrolledText(frame, height=20)
        self.trace_output.pack(fill='both', expand=True, padx=10, pady=5)
    
    def create_keepalive_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Keepalive")
        
        # Config
        cfg = ttk.LabelFrame(frame, text="Configuración")
        cfg.pack(fill='x', padx=10, pady=10)
        
        # Interval
        f1 = ttk.Frame(cfg)
        f1.pack(fill='x', padx=5, pady=3)
        ttk.Label(f1, text="Intervalo (seg):").pack(side='left', padx=5)
        self.ka_interval = ttk.Entry(f1, width=10)
        self.ka_interval.pack(side='left', padx=5)
        self.ka_interval.insert(0, str(self.config.get("keepalive_interval", 30)))
        
        # Protocol
        f2 = ttk.Frame(cfg)
        f2.pack(fill='x', padx=5, pady=3)
        ttk.Label(f2, text="Protocolo:").pack(side='left', padx=5)
        self.ka_protocol = tk.StringVar(value=self.config.get("keepalive_protocol", "https"))
        ttk.Combobox(f2, textvariable=self.ka_protocol, values=["http", "https", "icmp"], 
                     state='readonly', width=15).pack(side='left', padx=5)
        
        # Strategy
        f3 = ttk.Frame(cfg)
        f3.pack(fill='x', padx=5, pady=3)
        ttk.Label(f3, text="Estrategia:").pack(side='left', padx=5)
        self.ka_strategy = tk.StringVar(value=self.config.get("keepalive_strategy", "failover"))
        ttk.Combobox(f3, textvariable=self.ka_strategy, values=["constant", "rotate", "failover"],
                     state='readonly', width=15).pack(side='left', padx=5)
        
        # Sites
        sites_frame = ttk.LabelFrame(frame, text="Sitios")
        sites_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.sites_listbox = tk.Listbox(sites_frame, height=6)
        self.sites_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        self.refresh_sites_list()
        
        # Site buttons
        btn_frame = ttk.Frame(sites_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text="Agregar", command=self.add_site).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Eliminar", command=self.remove_site).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Cargar archivo", command=self.load_sites_file).pack(side='left', padx=2)
        
        # Control buttons
        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(fill='x', padx=10, pady=5)
        
        self.ka_start_btn = ttk.Button(ctrl_frame, text="Iniciar", command=self.start_keepalive)
        self.ka_start_btn.pack(side='left', padx=5)
        
        self.ka_stop_btn = ttk.Button(ctrl_frame, text="Detener", command=self.stop_keepalive, state='disabled')
        self.ka_stop_btn.pack(side='left', padx=5)
        
        self.ka_status = ttk.Label(ctrl_frame, text="Estado: Detenido", foreground="red")
        self.ka_status.pack(side='left', padx=10)
        
        # Output
        self.ka_output = scrolledtext.ScrolledText(frame, height=8)
        self.ka_output.pack(fill='both', expand=True, padx=10, pady=5)
    
    def create_speedtest_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Speed Test")
        
        # Config
        cfg = ttk.LabelFrame(frame, text="Configuración")
        cfg.pack(fill='x', padx=10, pady=10)
        
        # Servidor
        f1 = ttk.Frame(cfg)
        f1.pack(fill='x', padx=5, pady=3)
        ttk.Label(f1, text="Servidor:").pack(side='left', padx=5)
        self.speedtest_server = ttk.Entry(f1, width=40)
        self.speedtest_server.pack(side='left', padx=5)
        self.speedtest_server.insert(0, "https://speed.cloudflare.com")
        
        # Duración
        f2 = ttk.Frame(cfg)
        f2.pack(fill='x', padx=5, pady=3)
        ttk.Label(f2, text="Duración (seg):").pack(side='left', padx=5)
        self.speedtest_duration = ttk.Entry(f2, width=10)
        self.speedtest_duration.pack(side='left', padx=5)
        self.speedtest_duration.insert(0, "10")
        
        # Chunk size
        f3 = ttk.Frame(cfg)
        f3.pack(fill='x', padx=5, pady=3)
        ttk.Label(f3, text="Tamaño buffer (KB):").pack(side='left', padx=5)
        self.speedtest_chunk = ttk.Entry(f3, width=10)
        self.speedtest_chunk.pack(side='left', padx=5)
        self.speedtest_chunk.insert(0, "8")
        
        # Control
        ctrl = ttk.Frame(frame)
        ctrl.pack(fill='x', padx=10, pady=5)
        
        self.speedtest_btn = ttk.Button(ctrl, text="Iniciar Test Completo", command=self.run_speedtest)
        self.speedtest_btn.pack(side='left', padx=5)
        
        ttk.Label(ctrl, text="(Latencia + Download + Upload + Jitter)", foreground="gray").pack(side='left', padx=5)
        
        # Output
        self.speedtest_output = scrolledtext.ScrolledText(frame, height=20)
        self.speedtest_output.pack(fill='both', expand=True, padx=10, pady=5)
    
    def create_config_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Configuración")
        
        # Options
        opts = ttk.LabelFrame(frame, text="Opciones de Inicio")
        opts.pack(fill='x', padx=10, pady=10)
        
        self.auto_start_var = tk.BooleanVar(value=self.config.get("auto_start_keepalive", False))
        ttk.Checkbutton(opts, text="Auto-iniciar keepalive al abrir app", 
                       variable=self.auto_start_var).pack(anchor='w', padx=10, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Guardar Config", command=self.save_configuration).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Exportar", command=self.export_config).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Importar", command=self.import_config).pack(side='left', padx=5)
        
        # Info
        info = scrolledtext.ScrolledText(frame, height=15, wrap='word')
        info.pack(fill='both', expand=True, padx=10, pady=10)
        
        modules_status = "✓ Activos (sin permisos requeridos)" if CUSTOM_MODULES else "✗ No disponibles (usa comandos sistema)"
        tray_status = "✓ Disponible" if TRAY_AVAILABLE else "✗ No disponible"
        
        info.insert('1.0', f"""Network Tools Pro v1.2

Estado de Módulos:
- Ping/Traceroute personalizados: {modules_status}
- System Tray: {tray_status}

Herramientas:
- Ping: Test de conectividad (sin permisos admin)
- Traceroute: Rastreo de ruta (sin permisos admin)
- Keepalive: Mantener conexión activa
- Speed Test: Test de velocidad

Estrategias Keepalive:
- Constant: Mismo sitio siempre
- Rotate: Rota entre todos
- Failover: Cambia solo si falla (RECOMENDADO)

Ventajas módulos personalizados:
- No requieren permisos de administrador
- Ping usa TCP cuando ICMP no disponible
- Traceroute usa método TCP/UDP híbrido

Con auto-inicio activado, keepalive se restaura automáticamente al abrir la app.
""")
        info.config(state='disabled')
    
    def refresh_sites_list(self):
        self.sites_listbox.delete(0, tk.END)
        all_sites = self.config.get("sites_list", []) + self.config.get("custom_sites", [])
        for site in all_sites:
            self.sites_listbox.insert(tk.END, site)
    
    def add_site(self):
        site = simpledialog.askstring("Agregar Sitio", "URL del sitio:")
        if site:
            if not site.startswith(("http://", "https://")):
                site = "https://" + site
            if "custom_sites" not in self.config:
                self.config["custom_sites"] = []
            self.config["custom_sites"].append(site)
            self.refresh_sites_list()
            self.save_config()
    
    def remove_site(self):
        sel = self.sites_listbox.curselection()
        if not sel:
            messagebox.showwarning("Advertencia", "Seleccione un sitio")
            return
        site = self.sites_listbox.get(sel[0])
        if site in self.config.get("custom_sites", []):
            self.config["custom_sites"].remove(site)
            self.refresh_sites_list()
            self.save_config()
        else:
            messagebox.showinfo("Info", "No se pueden eliminar sitios por defecto")
    
    def load_sites_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    sites = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                if "custom_sites" not in self.config:
                    self.config["custom_sites"] = []
                for site in sites:
                    if not site.startswith(("http://", "https://")):
                        site = "https://" + site
                    if site not in self.config["custom_sites"]:
                        self.config["custom_sites"].append(site)
                self.refresh_sites_list()
                self.save_config()
                messagebox.showinfo("OK", f"Cargados {len(sites)} sitios")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def run_ping(self):
        host = self.ping_host.get()
        count = self.ping_count.get()
        if not host:
            messagebox.showwarning("Advertencia", "Ingrese un host")
            return
        
        self.ping_btn.config(state='disabled')
        self.status_bar.config(text="Ejecutando ping...")
        threading.Thread(target=self._ping_thread, args=(host, count), daemon=True).start()
    
    def _ping_thread(self, host, count):
        try:
            count_int = int(count)
        except:
            count_int = 4
        
        try:
            if CUSTOM_MODULES:
                # Callback para actualizar UI en tiempo real
                def ping_callback(text):
                    self.update_queue.put(('ping_append', text))
                
                # Limpiar output
                self.update_queue.put(('ping_clear', None))
                
                # Usar nuestro módulo personalizado con callback
                ping_module.ping(host, count_int, timeout=3, callback=ping_callback)
                self.log_event(f"Ping a {host} (módulo personalizado)")
            else:
                # Fallback al comando del sistema
                if platform.system().lower() == 'windows':
                    param = '-n'
                else:
                    param = '-c'
                
                cmd = ['ping', param, str(count_int), host]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                output = result.stdout if result.stdout else result.stderr
                
                if not output:
                    output = f"Ping ejecutado a {host}\nSin respuesta o timeout"
                
                self.update_queue.put(('ping_output', output))
                self.log_event(f"Ping a {host} (comando sistema)")
        except Exception as e:
            error_msg = f"Error en ping: {str(e)}\n\n"
            if not CUSTOM_MODULES:
                error_msg += "Tip: Los módulos personalizados no requieren permisos de administrador.\n"
            self.update_queue.put(('ping_output', error_msg))
        finally:
            self.update_queue.put(('ping_btn_enable', None))
            self.update_queue.put(('status', "Listo"))
    
    def run_traceroute(self):
        host = self.trace_host.get()
        hops = self.trace_hops.get()
        if not host:
            messagebox.showwarning("Advertencia", "Ingrese un host")
            return
        
        self.trace_btn.config(state='disabled')
        self.status_bar.config(text="Ejecutando traceroute...")
        threading.Thread(target=self._trace_thread, args=(host, hops), daemon=True).start()
    
    def _trace_thread(self, host, hops):
        try:
            hops_int = int(hops)
        except:
            hops_int = 30
        
        try:
            if CUSTOM_MODULES:
                # Callback para actualizar UI en tiempo real
                def trace_callback(text):
                    self.update_queue.put(('trace_append', text))
                
                # Limpiar output
                self.update_queue.put(('trace_clear', None))
                
                # Usar nuestro módulo personalizado con callback
                traceroute_module.traceroute(host, hops_int, timeout=3, callback=trace_callback)
                self.log_event(f"Traceroute a {host} (módulo personalizado)")
            else:
                # Fallback al comando del sistema
                if platform.system().lower() == 'windows':
                    cmd = ['tracert', '-h', str(hops_int), host]
                else:
                    cmd = ['traceroute', '-m', str(hops_int), host]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
                output = result.stdout if result.stdout else result.stderr
                
                if not output:
                    output = f"Traceroute ejecutado a {host}\nSin respuesta"
                
                self.update_queue.put(('trace_output', output))
                self.log_event(f"Traceroute a {host} (comando sistema)")
        except Exception as e:
            error_msg = f"Error en traceroute: {str(e)}\n\n"
            if not CUSTOM_MODULES:
                error_msg += "Tip: Los módulos personalizados no requieren permisos de administrador.\n"
            self.update_queue.put(('trace_output', error_msg))
        finally:
            self.update_queue.put(('trace_btn_enable', None))
            self.update_queue.put(('status', "Listo"))
    
    def start_keepalive(self):
        if self.keepalive_running:
            return
        
        try:
            interval = int(self.ka_interval.get())
            if interval < 1:
                messagebox.showerror("Error", "Intervalo mínimo: 1 segundo")
                return
            self.config["keepalive_interval"] = interval
            self.config["keepalive_protocol"] = self.ka_protocol.get()
            self.config["keepalive_strategy"] = self.ka_strategy.get()
        except ValueError:
            messagebox.showerror("Error", "Intervalo inválido")
            return
        
        self.keepalive_running = True
        self.config["last_keepalive_running"] = True
        self.save_config()
        
        self.ka_start_btn.config(state='disabled')
        self.ka_stop_btn.config(state='normal')
        self.ka_status.config(text="Estado: Ejecutando", foreground="green")
        
        self.keepalive_thread = threading.Thread(target=self._keepalive_thread, daemon=True)
        self.keepalive_thread.start()
        self.log_event("Keepalive iniciado")
    
    def stop_keepalive(self):
        self.keepalive_running = False
        self.config["last_keepalive_running"] = False
        self.save_config()
        
        self.ka_start_btn.config(state='normal')
        self.ka_stop_btn.config(state='disabled')
        self.ka_status.config(text="Estado: Detenido", foreground="red")
        self.log_event("Keepalive detenido")
    
    def auto_start_keepalive(self):
        """Auto-start keepalive si estaba corriendo"""
        try:
            self.start_keepalive()
            msg = f"[{datetime.now().strftime('%H:%M:%S')}] Keepalive auto-iniciado\n"
            self.ka_output.insert(tk.END, msg)
            self.ka_output.see(tk.END)
        except:
            pass
    
    def _keepalive_thread(self):
        interval = self.config.get("keepalive_interval", 30)
        protocol = self.config.get("keepalive_protocol", "https")
        strategy = self.config.get("keepalive_strategy", "failover")
        
        all_sites = self.config.get("sites_list", []) + self.config.get("custom_sites", [])
        if not all_sites:
            self.update_queue.put(('ka_output', "No hay sitios\n"))
            self.keepalive_running = False
            return
        
        current_index = 0
        
        while self.keepalive_running:
            try:
                if strategy == "constant":
                    site = all_sites[0]
                elif strategy == "rotate":
                    site = all_sites[current_index % len(all_sites)]
                    current_index += 1
                elif strategy == "failover":
                    site = all_sites[current_index % len(all_sites)]
                
                success = False
                if protocol in ["http", "https"]:
                    try:
                        resp = requests.get(site, timeout=5)
                        success = resp.status_code < 400
                        msg = f"Status {resp.status_code}"
                    except Exception as e:
                        msg = str(e)
                elif protocol == "icmp":
                    try:
                        host = site.replace("https://", "").replace("http://", "").split("/")[0]
                        param = '-n' if platform.system().lower() == 'windows' else '-c'
                        result = subprocess.run(['ping', param, '1', host], 
                                              capture_output=True, timeout=5)
                        success = result.returncode == 0
                        msg = "OK" if success else "Fail"
                    except Exception as e:
                        msg = str(e)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                status = "✓" if success else "✗"
                output = f"[{timestamp}] {status} {site}: {msg}\n"
                
                self.update_queue.put(('ka_output', output))
                
                if not success and strategy == "failover":
                    current_index += 1
                    if current_index >= len(all_sites):
                        current_index = 0
                
                time.sleep(interval)
            except Exception as e:
                self.update_queue.put(('ka_output', f"Error: {e}\n"))
                time.sleep(interval)
    
    def run_speedtest(self):
        server = self.speedtest_server.get()
        if not server:
            messagebox.showwarning("Advertencia", "Ingrese servidor")
            return
        
        self.speedtest_btn.config(state='disabled')
        self.status_bar.config(text="Ejecutando speed test...")
        threading.Thread(target=self._speedtest_thread, args=(server,), daemon=True).start()
    
    def _speedtest_thread(self, server):
        try:
            # Leer configuración
            try:
                duration = int(self.speedtest_duration.get())
                chunk_size = int(self.speedtest_chunk.get()) * 1024
            except:
                duration = 10
                chunk_size = 8192
            
            def output(text):
                self.update_queue.put(('speedtest_append', text))
            
            # Limpiar
            self.update_queue.put(('speedtest_output', ""))
            
            output(f"╔════════════════════════════════════════╗\n")
            output(f"║   NETWORK SPEED TEST - Comprehensive   ║\n")
            output(f"╚════════════════════════════════════════╝\n\n")
            output(f"Servidor: {server}\n")
            output(f"Duración: {duration}s por test\n")
            output(f"Buffer: {chunk_size/1024:.0f} KB\n\n")

            avg_latency = None
            download_mbps = None
            
            # ═══ Test 1: Latencia (Ping múltiple) ═══
            output("─" * 40 + "\n")
            output("TEST 1: LATENCIA (10 pings)\n")
            output("─" * 40 + "\n")
            
            latencies = []
            for i in range(10):
                start = time.time()
                try:
                    resp = requests.head(server, timeout=5)
                    latency = (time.time() - start) * 1000
                    latencies.append(latency)
                    output(f"  Ping {i+1}: {latency:.2f} ms\n")
                except Exception as e:
                    output(f"  Ping {i+1}: Error - {str(e)[:30]}\n")
                time.sleep(0.2)
            
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                output(f"\n  Min: {min_latency:.2f} ms\n")
                output(f"  Max: {max_latency:.2f} ms\n")
                output(f"  Avg: {avg_latency:.2f} ms\n")
                
                # Calcular jitter
                if len(latencies) > 1:
                    jitter = sum(abs(latencies[i] - latencies[i-1]) for i in range(1, len(latencies))) / (len(latencies) - 1)
                    output(f"  Jitter: {jitter:.2f} ms\n")
            
            # ═══ Test 2: Download Speed ═══
            output("\n" + "─" * 40 + "\n")
            output("TEST 2: VELOCIDAD DE DESCARGA\n")
            output("─" * 40 + "\n")
            
            try:
                output("Iniciando descarga...\n")
                start = time.time()
                resp = requests.get(server, timeout=duration+5, stream=True)
                total = 0
                last_update = start
                
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    total += len(chunk)
                    current = time.time()
                    
                    # Actualizar cada segundo
                    if current - last_update >= 1.0:
                        elapsed = current - start
                        speed = (total * 8) / (elapsed * 1000000)
                        output(f"  {elapsed:.1f}s: {speed:.2f} Mbps ({total/(1024*1024):.2f} MB)\n")
                        last_update = current
                    
                    if current - start > duration:
                        break
                
                elapsed = time.time() - start
                download_mbps = (total * 8) / (elapsed * 1000000)

                output(f"\n  Total descargado: {total/(1024*1024):.2f} MB\n")
                output(f"  Tiempo: {elapsed:.2f} s\n")
                output(f"  ► VELOCIDAD DESCARGA: {download_mbps:.2f} Mbps\n")
            except Exception as e:
                output(f"  Error en descarga: {str(e)}\n")
            
            # ═══ Test 3: Upload Speed (simulado) ═══
            output("\n" + "─" * 40 + "\n")
            output("TEST 3: VELOCIDAD DE SUBIDA (simulado)\n")
            output("─" * 40 + "\n")
            
            try:
                # Simular upload con POST
                output("Iniciando subida...\n")
                data = b'0' * (chunk_size * 10)  # Datos de prueba
                start = time.time()
                total_uploaded = 0
                iterations = 0
                
                while time.time() - start < duration and iterations < 20:
                    try:
                        resp = requests.post(server, data=data, timeout=5)
                        total_uploaded += len(data)
                        iterations += 1
                        
                        elapsed = time.time() - start
                        speed = (total_uploaded * 8) / (elapsed * 1000000)
                        output(f"  {elapsed:.1f}s: {speed:.2f} Mbps ({total_uploaded/(1024*1024):.2f} MB)\n")
                    except:
                        break
                
                elapsed = time.time() - start
                if elapsed > 0 and total_uploaded > 0:
                    speed_mbps = (total_uploaded * 8) / (elapsed * 1000000)
                    output(f"\n  Total subido: {total_uploaded/(1024*1024):.2f} MB\n")
                    output(f"  Tiempo: {elapsed:.2f} s\n")
                    output(f"  ► VELOCIDAD SUBIDA: {speed_mbps:.2f} Mbps\n")
                else:
                    output(f"  Upload no soportado por este servidor\n")
            except Exception as e:
                output(f"  Upload no soportado: {str(e)[:50]}\n")
            
            # ═══ Resumen ═══
            output("\n" + "═" * 40 + "\n")
            output("RESUMEN\n")
            output("═" * 40 + "\n")
            if avg_latency is not None:
                output(f"  Latencia promedio: {avg_latency:.2f} ms\n")
            if download_mbps is not None:
                output(f"  Descarga: {download_mbps:.2f} Mbps\n")
            output(f"  Estado servidor: OK\n")
            output("\n✓ Test completado\n")

            self.log_event(f"Speed test completado: {download_mbps} Mbps")
            
        except Exception as e:
            self.update_queue.put(('speedtest_output', f"Error: {str(e)}"))
            self.log_event(f"Error en speed test: {str(e)}")
        finally:
            self.update_queue.put(('speedtest_btn_enable', None))
            self.update_queue.put(('status', "Listo"))
    
    def save_configuration(self):
        self.config["auto_start_keepalive"] = self.auto_start_var.get()
        self.save_config()
        messagebox.showinfo("OK", "Configuración guardada")
    
    def export_config(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", 
                                                 filetypes=[("JSON", "*.json")])
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                messagebox.showinfo("OK", "Exportado")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def import_config(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported = json.load(f)
                self.config.update(imported)
                self.save_config()
                messagebox.showinfo("OK", "Importado. Reinicie la app.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def process_queue(self):
        try:
            while not self.update_queue.empty():
                action, data = self.update_queue.get_nowait()
                
                if action == 'ping_clear':
                    self.ping_output.delete('1.0', tk.END)
                elif action == 'ping_append':
                    self.ping_output.insert(tk.END, data)
                    self.ping_output.see(tk.END)
                elif action == 'ping_output':
                    self.ping_output.delete('1.0', tk.END)
                    self.ping_output.insert('1.0', data)
                elif action == 'trace_clear':
                    self.trace_output.delete('1.0', tk.END)
                elif action == 'trace_append':
                    self.trace_output.insert(tk.END, data)
                    self.trace_output.see(tk.END)
                elif action == 'trace_output':
                    self.trace_output.delete('1.0', tk.END)
                    self.trace_output.insert('1.0', data)
                elif action == 'speedtest_output':
                    self.speedtest_output.delete('1.0', tk.END)
                    self.speedtest_output.insert('1.0', data)
                elif action == 'speedtest_append':
                    self.speedtest_output.insert(tk.END, data)
                    self.speedtest_output.see(tk.END)
                elif action == 'ka_output':
                    self.ka_output.insert(tk.END, data)
                    self.ka_output.see(tk.END)
                    lines = self.ka_output.get('1.0', tk.END).split('\n')
                    if len(lines) > 100:
                        self.ka_output.delete('1.0', '50.0')
                elif action == 'ping_btn_enable':
                    self.ping_btn.config(state='normal')
                elif action == 'trace_btn_enable':
                    self.trace_btn.config(state='normal')
                elif action == 'speedtest_btn_enable':
                    self.speedtest_btn.config(state='normal')
                elif action == 'status':
                    self.status_bar.config(text=data)
        except:
            pass
        
        self.root.after(100, self.process_queue)
    
    def setup_tray(self):
        """Configurar icono de system tray"""
        if not TRAY_AVAILABLE:
            return
        
        try:
            # Crear imagen para el icono
            image = Image.new('RGB', (64, 64), color='#1E90FF')
            draw = ImageDraw.Draw(image)
            draw.rectangle([16, 16, 48, 48], fill='white')
            draw.text((20, 20), "NT", fill='#1E90FF')
            
            # Crear menú
            menu = pystray.Menu(
                pystray.MenuItem("Mostrar", self.show_window, default=True),
                pystray.MenuItem("Ocultar", self.hide_window),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Salir", self.quit_app)
            )
            
            self.tray_icon = pystray.Icon("NetworkTools", image, "Network Tools Pro", menu)
            
            # Iniciar en thread separado
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"Error creando tray icon: {e}")
            self.tray_icon = None
    
    def show_window(self, icon=None, item=None):
        """Mostrar ventana"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def hide_window(self, icon=None, item=None):
        """Ocultar ventana a tray"""
        self.root.withdraw()
    
    def quit_app(self, icon=None, item=None):
        """Cerrar completamente"""
        self.keepalive_running = False
        self.config["last_keepalive_running"] = False
        self.save_config()
        
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass
        
        sys.exit(0)
    
    def on_closing(self):
        """Al cerrar ventana, ir a tray"""
        if TRAY_AVAILABLE and self.tray_icon:
            self.hide_window()
        else:
            self.quit_app()

def main():
    root = tk.Tk()
    app = NetworkToolsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
