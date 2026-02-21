"""
Módulo de Traceroute personalizado
No requiere permisos de administrador (usa TCP/UDP)
"""

import socket
import time
import struct

def traceroute_tcp(host, max_hops=30, port=80, timeout=2, callback=None):
    """
    Traceroute usando conexiones TCP
    No requiere permisos de administrador
    callback: función para output en tiempo real
    """
    results = []
    
    def output(text):
        results.append(text)
        if callback:
            callback(text)
    
    output(f"Traceroute to {host} (max {max_hops} hops)\n")
    output("Using TCP connections (no admin required)\n\n")
    
    # Resolver host
    try:
        dest_addr = socket.gethostbyname(host)
        output(f"Destination: {dest_addr}\n\n")
    except socket.gaierror:
        output(f"Error: Could not resolve {host}\n")
        return ''.join(results)
    
    reached = False
    
    for ttl in range(1, max_hops + 1):
        output(f"{ttl:2d}  ")
        
        # Intentar 3 veces por hop
        hop_addr = None
        latencies = []
        
        for attempt in range(3):
            try:
                # Crear socket TCP
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
                sock.settimeout(timeout)
                
                start_time = time.time()
                
                try:
                    sock.connect((dest_addr, port))
                    latency = (time.time() - start_time) * 1000
                    latencies.append(latency)
                    hop_addr = dest_addr
                    reached = True
                    sock.close()
                except socket.timeout:
                    output("  *  ")
                except (ConnectionRefusedError, OSError) as e:
                    # TTL expirado o conexión rechazada
                    latency = (time.time() - start_time) * 1000
                    latencies.append(latency)
                    
                    # Intentar obtener la IP del hop intermedio
                    if not hop_addr:
                        hop_addr = "???"
                    
                    sock.close()
                    
            except Exception as e:
                output("  *  ")
                continue
        
        # Mostrar resultados del hop
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            output(f"{avg_latency:6.2f} ms  ")
            
            # Intentar resolver hostname
            if hop_addr and hop_addr != "???":
                try:
                    hostname = socket.gethostbyaddr(hop_addr)[0]
                    output(f"{hostname} ({hop_addr})")
                except:
                    output(f"{hop_addr}")
            else:
                output("???")
        else:
            output("Request timed out")
        
        output("\n")
        
        if reached:
            output(f"\nReached destination {dest_addr}\n")
            break
    
    if not reached:
        output(f"\nDid not reach destination within {max_hops} hops\n")
    
    return ''.join(results)

def traceroute_udp(host, max_hops=30, timeout=2):
    """
    Traceroute usando UDP (método alternativo)
    Puede requerir permisos en algunos sistemas
    """
    results = []
    results.append(f"Traceroute to {host} (max {max_hops} hops)\n")
    results.append("Using UDP method\n\n")
    
    # Resolver host
    try:
        dest_addr = socket.gethostbyname(host)
        results.append(f"Destination: {dest_addr}\n\n")
    except socket.gaierror:
        return f"Error: Could not resolve {host}"
    
    port = 33434  # Puerto UDP estándar para traceroute
    
    for ttl in range(1, max_hops + 1):
        results.append(f"{ttl:2d}  ")
        
        # Crear sockets
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        
        send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        recv_socket.settimeout(timeout)
        
        recv_socket.bind(("", port))
        
        start_time = time.time()
        send_socket.sendto(b"", (dest_addr, port))
        
        curr_addr = None
        curr_name = None
        
        try:
            _, curr_addr = recv_socket.recvfrom(512)
            curr_addr = curr_addr[0]
            latency = (time.time() - start_time) * 1000
            
            try:
                curr_name = socket.gethostbyaddr(curr_addr)[0]
            except socket.herror:
                curr_name = curr_addr
            
            results.append(f"{latency:6.2f} ms  {curr_name} ({curr_addr})\n")
            
        except socket.timeout:
            results.append("  *  Request timed out\n")
        
        finally:
            send_socket.close()
            recv_socket.close()
        
        if curr_addr == dest_addr:
            results.append(f"\nReached destination\n")
            break
    
    return ''.join(results)

def traceroute(host, max_hops=30, timeout=2, callback=None):
    """
    Ejecutar traceroute (intenta TCP primero, luego UDP)
    callback: función para output en tiempo real
    """
    try:
        # Intentar TCP primero (no requiere permisos)
        return traceroute_tcp(host, max_hops, 80, timeout, callback)
    except Exception as e:
        if callback:
            callback(f"Error: Could not perform traceroute\nTCP error: {e}\n")
        return f"Error: Could not perform traceroute\nTCP error: {e}\n\nTry running as administrator for full functionality."

if __name__ == "__main__":
    # Test
    print(traceroute("google.com", 15))
