import logging
import queue
import socket
import threading


logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

debug_log_format = logging.Formatter("%(levelname)s on line %(lineno)s at %(asctime)s: %(message)s", datefmt="%d-%m-%Y, %H:%M")
debug_handler = logging.StreamHandler()
debug_handler.setFormatter(debug_log_format)
debug_handler.setLevel(logging.DEBUG)
logger.addHandler(debug_handler)

error_log_format = logging.Formatter("%(levelname)s on line %(lineno)s at %(asctime)s: %(message)s", datefmt="%d-%m-%Y, %H:%M")
error_handler = logging.FileHandler("server_errors.log", 'w')
error_handler.setFormatter(error_log_format)
error_handler.setLevel(logging.ERROR)
logger.addHandler(error_handler)

host = socket.gethostname()
ip = socket.gethostbyname(host)
port = 7118
header_size = 10
all_clients = []
first_client = None
messages = queue.Queue()
lock = threading.Lock()


def receive_message(client: socket.socket):
    try:
        logger.debug("Waiting for header")
        header = ''
        while not header:
            header = client.recv(header_size).decode("utf-8")
        logger.debug(f"Header received, message lenght: {header}")
        msg_len = int(header.strip())
        logger.debug("Waiting for whole message to be received")
        msg = ''
        while len(msg) < msg_len:
            chunk = client.recv(header_size).decode("utf-8")
            msg += chunk
        logger.debug("Message successfully received...")
        return msg
    except Exception as exc:
        logger.warning(exc)
        return

def handle_client(client: socket.socket):
    try:
        global all_clients
        global messages
        global first_client
        logger.debug("Waiting for introdution of new client")
        name = receive_message(client)
        logger.debug(f"New Client: {name}")
        if __name__ == "__main__":
            print(f"New user joined: {name}")
        if not first_client:
            first_client = name
            logger.debug(f"first client: {first_client}")
        send_to_all(f"{name} joined conversation.")
        with lock:
            i = len(all_clients)
            all_clients.append((client, name))
        while True:
            message = receive_message(client)
            if not message:
                try:
                    client.send("checking".encode("utf-8"))
                except:
                    logger.info(f"Client {name} is offline.")
                    if len(all_clients) > i and all_clients[i] == (client, name):
                        print(f"{name} has left the conversation")
                        send_to_all(f"{name} has left the conversation")
                    return
            messages.put((name, message))
    except Exception as exc:
        logger.error(exc)
        return

def send_to_all(message):
    try:
        message = ": ".join(message) if type(message) is not str else message
        header = str(len(message)).rjust(header_size)
        to_send = header + message
        with lock:
            for client in all_clients:
                try:
                    client[0].send(to_send.encode("utf-8"))
                except Exception as exc:
                    logger.warning("Failed to send message to " + str(client[1]))
    except Exception as exc:
        logger.error(exc)

def forward_message():
    try:
        while True:
            message = messages.get()
            logger.debug("forwarding message " + "from " + message[0])
            send_to_all(message)
    except Exception as exc:
        logger.error(exc)

def accept_client(server : socket.socket):
    try:
        while True:
            client, addr = server.accept()
            logger.info(f"Accepted new client")
            thread = threading.Thread(target=handle_client, args=(client, ))
            thread.start()
    except Exception as exc:
        logger.error(exc)


def main():
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((ip, port))
        server.listen()
    except Exception as exc:
        logger.critical(exc)
    else:
        logger.debug(f"first_client: {first_client}")
        print("Server running...")
        print(f"IP: {ip}\nPort: {port}")
        acceptor = threading.Thread(target=accept_client, args=[server])
        acceptor.start()
        forwarder = threading.Thread(target=forward_message)
        forwarder.start()

if __name__ == "__main__":
    main()