"""
Módulo de Ping personalizado
No requiere permisos de administrador
"""

import socket
import struct
import time
import select

def checksum(data):
    """Calcular checksum para paquete ICMP"""
    s = 0
    n = len(data) % 2
    for i in range(0, len(data) - n, 2):
        s += (data[i] << 8) + data[i + 1]
    if n:
        s += data[-1] << 8
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    s = ~s & 0xFFFF
    return s

def create_packet(id, sequence):
    """Crear paquete ICMP"""
    # Tipo 8 = Echo Request
    header = struct.pack('!BBHHH', 8, 0, 0, id, sequence)
    data = struct.pack('!d', time.time())
    
    # Calcular checksum
    chk = checksum(header + data)
    header = struct.pack('!BBHHH', 8, 0, chk, id, sequence)
    
    return header + data

def ping_once(host, timeout=2):
    """
    Hacer un ping a un host
    Retorna: (success, latency_ms, message)
    """
    try:
        # Intentar resolver el host
        try:
            dest_addr = socket.gethostbyname(host)
        except socket.gaierror:
            return False, 0, f"No se pudo resolver {host}"
        
        # Intentar crear socket ICMP (requiere permisos)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        except PermissionError:
            # Si no tenemos permisos, usar conexión TCP como alternativa
            return tcp_ping(host, timeout)
        
        sock.settimeout(timeout)
        
        # Enviar ping
        packet_id = int(time.time() * 1000) & 0xFFFF
        packet = create_packet(packet_id, 1)
        
        send_time = time.time()
        sock.sendto(packet, (dest_addr, 1))
        
        # Esperar respuesta
        try:
            ready = select.select([sock], [], [], timeout)
            if ready[0]:
                recv_packet, addr = sock.recvfrom(1024)
                recv_time = time.time()
                
                # Extraer datos
                icmp_header = recv_packet[20:28]
                type, code, checksum, p_id, sequence = struct.unpack('!BBHHH', icmp_header)
                
                if type == 0 and p_id == packet_id:  # Echo Reply
                    latency = (recv_time - send_time) * 1000
                    sock.close()
                    return True, latency, f"Reply from {dest_addr}"
            
            sock.close()
            return False, 0, "Request timed out"
            
        except socket.timeout:
            sock.close()
            return False, 0, "Request timed out"
            
    except Exception as e:
        return False, 0, f"Error: {str(e)}"

def tcp_ping(host, timeout=2, port=80):
    """
    Ping alternativo usando conexión TCP
    No requiere permisos de administrador
    """
    try:
        # Resolver host
        try:
            dest_addr = socket.gethostbyname(host)
        except socket.gaierror:
            return False, 0, f"No se pudo resolver {host}"
        
        # Intentar conexión TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        start_time = time.time()
        try:
            sock.connect((dest_addr, port))
            latency = (time.time() - start_time) * 1000
            sock.close()
            return True, latency, f"TCP connection to {dest_addr}:{port}"
        except (socket.timeout, ConnectionRefusedError, OSError):
            # Intentar con puerto 443 si 80 falla
            if port == 80:
                return tcp_ping(host, timeout, 443)
            return False, 0, f"Connection failed to {dest_addr}"
            
    except Exception as e:
        return False, 0, f"Error: {str(e)}"

def ping(host, count=4, timeout=2, callback=None):
    """
    Ejecutar múltiples pings
    callback: función para output en tiempo real callback(texto)
    Retorna string con resultado formateado
    """
    results = []
    
    def output(text):
        results.append(text)
        if callback:
            callback(text)
    
    output(f"Pinging {host}...\n")
    
    # Resolver host primero
    try:
        dest_addr = socket.gethostbyname(host)
        output(f"Resolved to: {dest_addr}\n\n")
    except socket.gaierror:
        output(f"Error: Could not resolve {host}\n")
        return ''.join(results)
    
    # Hacer pings
    success_count = 0
    total_latency = 0
    min_latency = float('inf')
    max_latency = 0
    
    for i in range(count):
        success, latency, message = ping_once(host, timeout)
        
        if success:
            success_count += 1
            total_latency += latency
            min_latency = min(min_latency, latency)
            max_latency = max(max_latency, latency)
            output(f"Reply from {dest_addr}: time={latency:.2f}ms\n")
        else:
            output(f"{message}\n")
        
        if i < count - 1:
            time.sleep(0.5)
    
    # Estadísticas
    output(f"\n--- Ping statistics for {host} ---\n")
    output(f"Packets: Sent = {count}, Received = {success_count}, Lost = {count - success_count}\n")
    
    if success_count > 0:
        avg_latency = total_latency / success_count
        output(f"Latency: Min = {min_latency:.2f}ms, Max = {max_latency:.2f}ms, Avg = {avg_latency:.2f}ms\n")
    
    return ''.join(results)

if __name__ == "__main__":
    # Test
    print(ping("google.com", 4))

