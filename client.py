import socket
import sys
import select

# "TEST;CMD=START;DURATION=5;RATE=1000;"
# "TEST;CMD=STOP;"

TARGET = "localhost"


def client(port: int, data: str) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.sendto(data.encode("iso-8859-1"), (TARGET, port))
    print(f"Sent to {TARGET}:{port} from socket {sock.getsockname()}")

    while True:
        ready = select.select([sock], [], [], 5)
        if ready[0]:
            print(f"Received: {sock.recv(1024).decode("iso-8859-1")}")
            continue

        print("Timed out!")
        break


if __name__ == "__main__":
    client(int(sys.argv[1]), sys.argv[2])
