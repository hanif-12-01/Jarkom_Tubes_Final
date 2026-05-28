import socket
import threading
import os
from datetime import datetime # Untuk timestamp

HOST = '127.0.0.1'
HTTP_PORT = 8000
UDP_PORT = 9000

def handle_http_client(connection, address):
    status_code = "200 OK" # Default status
    path = "-"
    
    try:
        request = connection.recv(1024).decode()
        if not request: return
        
        # Ambil path file (misal: /index.html)
        lines = request.split('\n')
        if len(lines) > 0:
            path = lines[0].split()[1]
        
        filename = path.lstrip('/')
        if filename == "": filename = "index.html"

        # Proses baca file
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                content = f.read()
            response = f"HTTP/1.1 200 OK\nContent-Length: {len(content)}\n\n{content}"
        else:
            status_code = "404 Not Found"
            response = "HTTP/1.1 404 Not Found\n\nYeee ketipu lu wkwkw, gak ada isinya :P"
            
    except Exception as e:
        # Poin: Handler 500 Internal Server Error jika proses gagal
        status_code = "500 Internal Server Error"
        response = f"HTTP/1.1 500 Internal Server Error\n\nError: {str(e)}"
    
    finally:
        # Poin: Menambahkan log (IP Proxy, Path, Timestamp, Status Code)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # address[0] adalah IP Proxy yang menghubungi Web Server
        print(f"[{timestamp}] LOG: {address[0]} meminta {path} -> {status_code}")
        
        connection.sendall(response.encode())
        connection.close()

# --- Sisanya (UDP Echo & Start Server) tetap sama ---
def start_udp_echo():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((HOST, UDP_PORT))
    while True:
        data, addr = udp_sock.recvfrom(1024)
        udp_sock.sendto(data, addr)

threading.Thread(target=start_udp_echo, daemon=True).start()
http_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
http_sock.bind((HOST, HTTP_PORT))
http_sock.listen(5)

print(f"Web Server jalan di port {HTTP_PORT}...")
while True:
    client_conn, client_addr = http_sock.accept()
    threading.Thread(target=handle_http_client, args=(client_conn, client_addr)).start()
