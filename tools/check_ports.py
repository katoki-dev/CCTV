import socket
def check_port(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

if __name__ == "__main__":
    print(f"Port 5000: {'OPEN' if check_port('127.0.0.1', 5000) else 'CLOSED'}")
    print(f"Port 80: {'OPEN' if check_port('127.0.0.1', 80) else 'CLOSED'}")
