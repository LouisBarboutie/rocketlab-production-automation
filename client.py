import socket
import sys
import select
import struct

# to use multicast, first check if it is available
# ip route show | grep 224
# enable it with (mask /4 matches first 4 bits for the entier multicast range, dev lo enables loopback)
# sudo ip route add 224.0.0.0/4 dev lo

# "TEST;CMD=START;DURATION=5;RATE=1000;"
# "TEST;CMD=STOP;"

# TARGET = "localhost"
TARGET = "224.3.11.15"
# TARGET = "0.0.0.0"


def client(port: int, data: str) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to the multicast port so we can receive on it
    sock.bind(("localhost", 0))
    mreq = struct.pack("4sL", socket.inet_aton(TARGET), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    sock.sendto(data.encode("iso-8859-1"), (TARGET, port))
    print(f"Sent to {TARGET}:{port} from socket {sock.getsockname()}")

    while True:
        ready = select.select([sock], [], [], 5)
        if ready[0]:
            data, address = sock.recvfrom(1024)
            print(f"Received: {data.decode("iso-8859-1")} from {address}")
            continue

        print("Timed out!")
        break


if __name__ == "__main__":
    client(int(sys.argv[1]), sys.argv[2])
