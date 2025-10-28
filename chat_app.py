import socket
import select
import sys
import threading

TCP_PORT = 8080
UDP_PORT = 9090
SERVER_IP = "127.0.0.1"
BUF_SIZE = 1024
MAX_CLIENTS = 10

# ================= SERVER CODE =================
def run_server():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind(("", TCP_PORT))
    tcp_sock.listen(5)

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("", UDP_PORT))

    client_socks = []
    print(f"Server started. TCP port {TCP_PORT}, UDP port {UDP_PORT}")

    while True:
        sockets_list = [tcp_sock, udp_sock] + client_socks
        read_sockets, _, _ = select.select(sockets_list, [], [])

        for sock in read_sockets:
            # New TCP connection
            if sock == tcp_sock:
                client_sock, addr = tcp_sock.accept()
                client_socks.append(client_sock)
                print(f"New TCP client connected from {addr}")

            # Incoming UDP message
            elif sock == udp_sock:
                data, addr = udp_sock.recvfrom(BUF_SIZE)
                msg = data.decode().strip()
                print(f"UDP msg from {addr}: {msg}")

                # Broadcast UDP message to all TCP clients
                for c in client_socks:
                    try:
                        c.sendall(data)
                    except:
                        c.close()
                        client_socks.remove(c)

            # Message from TCP client
            else:
                try:
                    data = sock.recv(BUF_SIZE)
                    if not data:
                        print("TCP client disconnected.")
                        client_socks.remove(sock)
                        sock.close()
                        continue

                    msg = data.decode().strip()
                    print(f"TCP msg: {msg}")

                    # Broadcast message to all TCP clients
                    for c in client_socks:
                        try:
                            c.sendall(data)
                        except:
                            c.close()
                            client_socks.remove(c)
                except:
                    client_socks.remove(sock)
                    sock.close()

# ================= CLIENT CODE =================
def run_client():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect((SERVER_IP, TCP_PORT))

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_addr = (SERVER_IP, UDP_PORT)

    print("Connected to server.")
    print("Type 'u:<msg>' for UDP, anything else for TCP.")

    def receive_tcp():
        while True:
            try:
                data = tcp_sock.recv(BUF_SIZE)
                if not data:
                    print("Disconnected from server.")
                    break
                print(f"Server: {data.decode().strip()}")
            except:
                break

    threading.Thread(target=receive_tcp, daemon=True).start()

    while True:
        try:
            msg = input()
            if msg.startswith("u:"):
                udp_sock.sendto(msg[2:].encode(), udp_addr)
            else:
                tcp_sock.sendall(msg.encode())
        except KeyboardInterrupt:
            print("\nExiting client...")
            break
        except:
            break

    tcp_sock.close()
    udp_sock.close()

# ================= MAIN =================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage:\n  python {sys.argv[0]} server   -> Run as server")
        print(f"  python {sys.argv[0]} client   -> Run as client")
        sys.exit(1)

    if sys.argv[1] == "server":
        run_server()
    elif sys.argv[1] == "client":
        run_client()
    else:
        print("Invalid option. Use 'server' or 'client'.")
