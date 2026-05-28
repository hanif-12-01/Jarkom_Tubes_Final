import socket
import time

def fetch_web(filename):
    print(f"\n--- Meminta file: /{filename} ---")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 8080)) # Ke Proxy
            request = f"GET /{filename} HTTP/1.1\r\nHost: localhost\r\n\r\n"
            s.sendall(request.encode())
            response = s.recv(4096).decode()
            print(response)
    except Exception as e:
        print(f"Gagal terhubung ke Proxy: {e}")

def hitung_jitter(rtts):
    if len(rtts) < 2:
        return 0.0

    selisih_rtt = []
    for i in range(1, len(rtts)):
        selisih_rtt.append(abs(rtts[i] - rtts[i - 1]))

    rata_rata = sum(selisih_rtt) / len(selisih_rtt)
    variasi = sum((nilai - rata_rata) ** 2 for nilai in selisih_rtt) / len(selisih_rtt)
    return variasi ** 0.5

def run_qos_test():
    server_addr = ('127.0.0.1', 9000)
    total_paket = 10
    timeout = 1.0
    rtts = []
    bytes_diterima = 0

    print("\n--- Memulai UDP/QoS Test ---")
    print(f"Target UDP Echo Server: {server_addr[0]}:{server_addr[1]}")

    waktu_mulai_test = time.time()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.settimeout(timeout)

        for seq in range(1, total_paket + 1):
            timestamp = time.time()
            payload = f"Ping {seq} {timestamp}"
            waktu_kirim = time.time()

            client_socket.sendto(payload.encode(), server_addr)

            try:
                data, _ = client_socket.recvfrom(1024)
                waktu_terima = time.time()
                rtt = (waktu_terima - waktu_kirim) * 1000
                rtts.append(rtt)
                bytes_diterima += len(data)
                print(f"Packet {seq}: RTT = {rtt:.2f} ms | Payload = {data.decode()}")
            except socket.timeout:
                print(f"Packet {seq}: Request timed out")

    durasi_test = max(time.time() - waktu_mulai_test, 0.000001)
    packets_sent = total_paket
    packets_received = len(rtts)
    packet_loss = ((packets_sent - packets_received) / packets_sent) * 100
    throughput = (bytes_diterima * 8) / durasi_test

    print("\n--- Statistik UDP/QoS ---")
    print(f"Packets Sent: {packets_sent}")
    print(f"Packets Received: {packets_received}")
    print(f"Packet Loss: {packet_loss:.2f}%")

    if rtts:
        print(f"Min RTT: {min(rtts):.2f} ms")
        print(f"Avg RTT: {sum(rtts) / len(rtts):.2f} ms")
        print(f"Max RTT: {max(rtts):.2f} ms")
        print(f"Jitter: {hitung_jitter(rtts):.2f} ms")
    else:
        print("Min RTT: -")
        print("Avg RTT: -")
        print("Max RTT: -")
        print("Jitter: -")

    print(f"Throughput: {throughput:.2f} bps")

if __name__ == "__main__":
    # Skenario sesuai screenshot Tahap 3
    fetch_web("index.html")    # Harusnya 200 OK
    fetch_web("missing.html")  # Harusnya 404 Not Found
    fetch_web("page.html")     # Request Pertama -> Proxy Log MISS
    fetch_web("page.html")     # Request Kedua   -> Proxy Log HIT
    run_qos_test()
