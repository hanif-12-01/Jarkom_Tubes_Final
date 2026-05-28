import socket
import threading
import os
from datetime import datetime # Untuk timestamp

HOST = '127.0.0.1'
HTTP_PORT = 8000
UDP_PORT = 9000
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

CONTENT_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.mp4': 'video/mp4',
}

def get_content_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    return CONTENT_TYPES.get(ext, 'application/octet-stream')

def build_http_response(status_code, body, content_type='text/plain; charset=utf-8'):
    header = (
        f"HTTP/1.1 {status_code}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode('iso-8859-1')
    return header + body

def is_project_file(file_path):
    try:
        return os.path.commonpath([PROJECT_ROOT, file_path]) == PROJECT_ROOT
    except ValueError:
        return False

def get_request_path(raw_path):
    path = raw_path.split('?', 1)[0].split('#', 1)[0]
    path = path.replace('\\', '/')
    return path

def handle_http_client(connection, address):
    status_code = "200 OK" # Default status
    path = "-"
    response = b""
    
    try:
        request = connection.recv(1024).decode('iso-8859-1', errors='replace')
        if not request:
            return
        
        # Ambil path file (misal: /index.html)
        lines = request.split('\n')
        if len(lines) > 0:
            path = lines[0].split()[1]
        
        request_path = get_request_path(path)
        filename = request_path.lstrip('/')
        if filename == "": filename = "index.html"
        file_path = os.path.abspath(os.path.join(PROJECT_ROOT, filename))

        # Proses baca file dalam mode binary agar HTML/CSS/assets tidak error encoding.
        if is_project_file(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
            response = build_http_response("200 OK", content, get_content_type(file_path))
        else:
            status_code = "404 Not Found"
            response = build_http_response(
                status_code,
                "Yeee ketipu lu wkwkw, gak ada isinya :P".encode('utf-8')
            )
            
    except Exception as e:
        # Poin: Handler 500 Internal Server Error jika proses gagal
        status_code = "500 Internal Server Error"
        response = build_http_response(
            status_code,
            f"Error: {str(e)}".encode('utf-8')
        )
    
    finally:
        # Poin: Menambahkan log (IP Proxy, Path, Timestamp, Status Code)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # address[0] adalah IP Proxy yang menghubungi Web Server
        print(f"[{timestamp}] LOG: {address[0]} meminta {path} -> {status_code}")
        
        if response:
            connection.sendall(response)
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
