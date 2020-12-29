import logging
import queue
import socket
import threading

import server

logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

debug_log_format = logging.Formatter("%(levelname)s on line %(lineno)s at %(asctime)s: %(message)s", datefmt="%d-%m-%Y, %H:%M")
debug_handler = logging.StreamHandler()
debug_handler.setFormatter(debug_log_format)
debug_handler.setLevel(logging.DEBUG)
logger.addHandler(debug_handler)

error_log_format = logging.Formatter("%(levelname)s on line %(lineno)s at %(asctime)s: %(message)s", datefmt="%d-%m-%Y, %H:%M")
error_handler = logging.FileHandler("client_errors.log", 'w')
error_handler.setFormatter(error_log_format)
error_handler.setLevel(logging.ERROR)
logger.addHandler(error_handler)


header_size = 10
messages = queue.Queue()
lock = threading.Lock()
client = None


def receive_message():
    while True:
        try:
            header = ''
            while not header:
                header = client.recv(header_size).decode("utf-8")
            msg_len = int(header.strip())
            msg = ''
            while len(msg) < msg_len:
                chunk = client.recv(header_size).decode("utf-8")
                msg += chunk
            messages.put(msg)
            logger.info("Recieved a message")
        except Exception as exc:
            logger.error(exc)
            return

def send_message(msg):
    try:
        header = str(len(msg)).rjust(header_size)
        to_send = header + msg
        client.send(to_send.encode("utf-8"))
        return True
    except Exception as exc:
        logger.error(exc)
        return False

def main(ip=None, port=None, name=None):
    global client
    try:
        if not ip and not port:
            ip = input("Enter server\'s address: ")
            port = int(input("Enter port: "))
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ip, port))
        logger.debug("Connected to server...")
        if not name:
            name = input("Enter your name: ").title()
    except Exception as exc:
        logger.critical(exc)
    else:
        print()
        logger.debug("Getting introduced with server...")
        send_message(name)
        logger.debug("Introduced self to server")
        receiver = threading.Thread(target=receive_message)
        receiver.start()
        while True:
            msg = input("You: ")
            if not send_message(msg):
                logger.warning("Failed to send message")
            while not messages.empty():
                message = messages.get()
                logger.debug(message)
                try:
                    sender, message = message.split(": ")
                    if message and name != sender:
                        print(f"{sender}: {message}")
                except:
                    if message != "checking":
                        print(message)
            

if __name__ == "__main__":
    task = input("Enter 0 to start a chat server, Enter 1 to join a chat: ")
    if not task or task == "0":
        print("Starting Server...")
        server.main()
        name = input("\nEnter your name: ").title()
        print("\nWaiting for participants...")
        while not server.first_client:
            pass
        print(f"{server.first_client} has joined the chat...\n")
        main(server.ip, server.port, name)
    elif task == "1":
        main()