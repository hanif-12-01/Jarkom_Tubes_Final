import socket
import threading
import os
import time

PROXY_PORT = 8080
WEB_SERVER_ADDR = ('127.0.0.1', 8000)
CACHE_DIR = "cache/"

if not os.path.exists(CACHE_DIR): os.makedirs(CACHE_DIR)

def get_request_path(request_text):
    parts = request_text.split()
    if len(parts) < 2:
        return "index.html"

    filename = parts[1].split('?', 1)[0].split('#', 1)[0].lstrip('/')
    if filename == "":
        filename = "index.html"
    return filename.replace('\\', '/')

def get_cache_path(filename):
    safe_name = filename.replace('/', '_').replace('\\', '_')
    return os.path.join(CACHE_DIR, safe_name)

def recv_all(sock):
    chunks = []
    while True:
        data = sock.recv(4096)
        if not data:
            break
        chunks.append(data)
    return b''.join(chunks)

def split_header_body(response):
    separator = b'\r\n\r\n'
    if separator not in response:
        separator = b'\n\n'
    if separator not in response:
        return response, b''
    header, body = response.split(separator, 1)
    return header, body

def is_200_ok(response):
    first_line = response.splitlines()[0] if response else b''
    return b' 200 ' in first_line or first_line.endswith(b' 200 OK')

def cache_is_complete(response):
    header, body = split_header_body(response)
    for line in header.splitlines():
        if line.lower().startswith(b'content-length:'):
            try:
                content_length = int(line.split(b':', 1)[1].strip())
                return len(body) == content_length
            except ValueError:
                return False
    return True

def cache_has_content_type(response):
    header, _ = split_header_body(response)
    return any(line.lower().startswith(b'content-type:') for line in header.splitlines())

def handle_client(client_conn):
    try:
        request = client_conn.recv(4096)
        if not request:
            return
        
        request_text = request.decode('iso-8859-1', errors='replace')
        filename = get_request_path(request_text)
        cache_path = get_cache_path(filename)

        start_time = time.time()

        # CEK CACHE HIT
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                content = f.read()
            if cache_is_complete(content) and cache_has_content_type(content):
                duration = (time.time() - start_time) * 1000
                print(f"[PROXY LOG] CACHE HIT: /{filename} ({duration:.2f} ms)")
                client_conn.sendall(content)
                return
            print(f"[PROXY LOG] CACHE MISS: /{filename}. Cache lama tidak valid, meminta ulang ke Web Server...")

        # CACHE MISS
        if not os.path.exists(cache_path):
            print(f"[PROXY LOG] CACHE MISS: /{filename}. Meminta ke Web Server...")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as web_sock:
            web_sock.connect(WEB_SERVER_ADDR)
            web_sock.sendall(request)
            response = recv_all(web_sock)
            
            # Simpan ke cache jika file ditemukan (200 OK)
            if is_200_ok(response):
                with open(cache_path, 'wb') as f:
                    f.write(response)
            
            duration = (time.time() - start_time) * 1000
            print(f"[PROXY LOG] CACHE MISS selesai: /{filename} ({duration:.2f} ms)")
            client_conn.sendall(response)
                
    except Exception as e:
        body = f"Web Server Mati: {str(e)}".encode('utf-8')
        response = (
            b"HTTP/1.1 504 Gateway Timeout\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            + f"Content-Length: {len(body)}\r\n".encode('iso-8859-1')
            + b"Connection: close\r\n\r\n"
            + body
        )
        client_conn.sendall(response)
    finally:
        client_conn.close()

# --- Kode menjalankan socket tetap sama ---
proxy_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy_sock.bind(('127.0.0.1', PROXY_PORT))
proxy_sock.listen(5)
print(f"Proxy jalan di port {PROXY_PORT}...")
while True:
    c, _ = proxy_sock.accept()
    threading.Thread(target=handle_client, args=(c,)).start()
