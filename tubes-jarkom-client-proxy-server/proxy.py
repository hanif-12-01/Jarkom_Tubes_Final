import socket
import threading
import os
import time

PROXY_PORT = 8080
WEB_SERVER_ADDR = ('127.0.0.1', 8000)
CACHE_DIR = "cache/"

if not os.path.exists(CACHE_DIR): os.makedirs(CACHE_DIR)

def handle_client(client_conn):
    try:
        request = client_conn.recv(1024).decode()
        if not request: return
        
        filename = request.split()[1].lstrip('/')
        if filename == "": filename = "index.html"
        cache_path = os.path.join(CACHE_DIR, filename.replace('/', '_'))

        start_time = time.time()

        # CEK CACHE HIT
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                content = f.read()
            duration = (time.time() - start_time) * 1000
            print(f"[PROXY LOG] HIT: /{filename} ({duration:.2f} ms)")
            client_conn.sendall(content.encode())

        # CACHE MISS
        else:
            print(f"[PROXY LOG] MISS: /{filename}. Meminta ke Web Server...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as web_sock:
                web_sock.connect(WEB_SERVER_ADDR)
                web_sock.sendall(request.encode())
                response = web_sock.recv(4096)
                
                # Simpan ke cache jika file ditemukan (200 OK)
                if b"200 OK" in response:
                    with open(cache_path, 'wb') as f:
                        f.write(response)
                
                duration = (time.time() - start_time) * 1000
                print(f"[PROXY LOG] MISS Selesai ({duration:.2f} ms)")
                client_conn.sendall(response)
                
    except Exception as e:
        client_conn.sendall(b"HTTP/1.1 504 Gateway Timeout\n\nWeb Server Mati")
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
