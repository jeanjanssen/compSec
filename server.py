import hashlib
import threading
import time
import json
import signal
import rsa
from socket import *
from typing import Dict
from userhandler import userhandler
from datetime import datetime

HEADER = 64
serverPort = 5053
block_duration = 10

SERVER = "localhost"
ADDR = (SERVER, serverPort)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

Server__Socket = socket(AF_INET, SOCK_STREAM)
Server__Socket.bind(ADDR)

thread_lock = threading.Condition()

#  clients
clients = []

logfile = None

# map username to connection socket
name_to_socket: Dict = dict()

# would communicate with clients after every second
UPDATE_INTERVAL = 1

# user manager manages all the user data
user_manager = userhandler(block_duration, timeout)

def keyboard_interrupt_handler(signal, frame):
    print("\r[SHUTTING OFF] server has shut down...")
    exit(0)

def on_close():
  Server__Socket.close()

def create_log():
    try:
        logfile = open("log.txt", "w")
    except:
        print("[ERROR] problem creating log file.")
    return logfile

def write_log(data, id, value):
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
    f = open('log.txt', 'a')
    if data["action"] == "INCREASE" or data["action"] == "DECREASE":
        f.write(dt_string + " - " + id + " - " + data["action"] + " " + str(data["value"]) + " - VAL = " + str(value) + "\n")
    else:
        f.write(dt_string + " - " + id + " - " + data["action"] + " - VAL = " + value + "\n")

def connection_handler(connection_socket, client_address):

    def real_connection_handler():
        global logfile
        usernamelog = None
        while True:
            try:
                received_data = connection_socket.recv(1024)
            except:
                exit(0)

            # TODO add decryption
            '''
            try:
                return rsa.decrypt(ciphertext, key).decode('ascii')
            except:
                return False
            '''
            # TODO add verification
            '''
            try:
                return rsa.verify(message.encode('ascii'), signature, key, ) == 'SHA-1'
            except:
                return False
            '''
            received_data = received_data.decode()
            received_data = received_data.split("}")

            for i in range(0, len(received_data)):
                received_data[i] += "}"

            received_data = received_data[0:len(received_data)-1]

            for i in range(0, len(received_data)):
                received_data[i] = json.loads(received_data[i])

            for data in received_data:
                action = data["action"]

                with thread_lock:
                    # debugging code, uncomment to use
                    print(client_address, ':', data)

                    # the received_data
                    server_message = dict()
                    server_message["action"] = action

                    # current user name
                    curr_user = user_manager.get_username(client_address)

                    # update the time out when user send anything to server
                    user_manager.refresh_user_timeout(curr_user)

                    if action == 'login':
                        # store client information (IP and Port No) in list
                        username = data["username"]
                        usernamelog = data["username"]
                        password = data["password"]
                        clients.append(client_address)
                        #MD5 HASHING
                        username = hashlib.md5(bytes(username, 'utf-8')).hexdigest()
                        password = hashlib.md5(bytes(password, 'utf-8')).hexdigest()

                        # verify the user and reply the status

                        status = user_manager.new_user(username, password)

                        user_manager.set_address_username(client_address, username)
                        server_message["status"] = status
                        if status == 'SUCCESS':
                            # add the socket to the name-socket map
                            name_to_socket[username] = connection_socket

                    elif action == 'logout':
                        if user_manager.get_username_count(username) == 1:
                            user_manager.set_offline(user_manager.get_username(client_address))
                            user_manager.user_stripper(username, password)
                            user_manager.decrease_user_count(username)
                            write_log(data, usernamelog, "N/A")
                        else:
                            user_manager.decrease_user_count(username)
                        
                        if client_address in clients:
                            clients.remove(client_address)
                            server_message["reply"] = "logged out"

                    elif action == 'INCREASE':
                        user = user_manager.get_user(client_address)
                        user.increaseBalance(data["value"])
                        write_log(data, usernamelog, user.getBalance())
                        print("[UPDATE] user balance changed to: " + str(user.getBalance()))

                    elif action == 'DECREASE':
                        user = user_manager.get_user(client_address)
                        user.decreaseBalance(data["value"])
                        write_log(data, usernamelog, user.getBalance())
                        print("[UPDATE] user balance changed to: " + str(user.getBalance()))

                    else:
                        server_message["reply"] = "Unknown action"
                    
                    try:
                        connection_socket.send(json.dumps(server_message).encode())
                    except:
                        print("[ERROR] could not return message to client, client has probably already disconnected.")
                    # notify the thread waiting
                    thread_lock.notify()

    return real_connection_handler

def recv_handler():

    global thread_lock
    global clients
    global Server__Socket

    while True:
        # create a new connection for a new client
        connection_socket, client_address = Server__Socket.accept()

        # create a new function handler for the client
        socket_handler = connection_handler(connection_socket, client_address)

        # TODO Receive public key client
        # TODO Generate connection-specific key and send to client
        # The code in example found online, this can all be shortened as we probably do not need to store the keys

        def generate_keys():
            public_key, private_key = rsa.newkeys(1024)
            with open('public_key.pem', 'wb') as p:
                p.write(public_key.save_pkcs1('PEM'))
            with open('private_key.pem', 'wb') as p:
                p.write(private_key.save_pkcs1('PEM'))

        def load_keys():
            with open('public_key.pem', 'rb') as p:
                public_key = rsa.PublicKey.load_pkcs1(p.read())
            with open('private_key.pem', 'rb') as p:
                private_key = rsa.PrivateKey.load_pkcs1(p.read())
            return public_key, private_key

        def sendKeys():
            generate_keys()
            private_key, public_key = load_keys()
            Server__Socket.send(public_key.exportKey(format='PEM', passphrase=None, pkcs=1))


        # create a new thread for the client socket
        socket_thread = threading.Thread(name=str(client_address), target=socket_handler)
        socket_thread.daemon = False
        socket_thread.start()

def send_handler():
    global thread_lock
    global clients
    global Server__Socket
    while True:
        # get lock
        with thread_lock:
            ##TODO handle outgoing (buffer incase of overflow??)

            time.sleep(UPDATE_INTERVAL)

sender_thread = threading.Thread(name="SendHandler", target=send_handler)
sender_thread.daemon = True
sender_thread.start()



# we will use two sockets, one for sending and one for receiving
Server__Socket = socket(AF_INET, SOCK_STREAM)
Server__Socket.bind(('localhost', serverPort))
Server__Socket.listen(1)

received_thread = threading.Thread(name="RecvHandler", target=recv_handler)
received_thread.daemon = True
received_thread.start()



# register keyboard interrupt handler
signal.signal(signal.SIGINT, keyboard_interrupt_handler)




# this is the main thread
def start():
    global logfile
    logfile = create_log()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        time.sleep(0.1)

        # update any information of all user data
        user_manager.update()


print("[STARTING] server is starting...")
start()
