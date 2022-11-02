import hashlib
import threading
import time
import json
import signal
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

# TODO Generate keys (code found online, but could be shortened as we probably do not need to store the keys)
# TODO when connection is established, send public key and receive client's private key
'''
def generateKeys():
    (publicKey, privateKey) = rsa.newkeys(1024)
    with open('keys/publcKey.pem', 'wb') as p:
        p.write(publicKey.save_pkcs1('PEM'))
     with open('keys/privateKey.pem', 'wb') as p:
        p.write(privateKey.save_pkcs1('PEM'))

def loadKeys():
    with open('keys/publicKey.pem', 'rb') as p:
        publicKey = rsa.PublicKey.load_pkcs1(p.read())
    with open('keys/privateKey.pem', 'rb') as p:
        privateKey = rsa.PrivateKey.load_pkcs1(p.read())
    return privateKey, publicKey
'''

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
    if data[0] == "INCREASE" or data[0] == "DECREASE":
        f.write(dt_string + " - " + id + " - " + data[0] + " " + str(data[1]) + " - VAL = " + str(value) + "\n")
    else:
        f.write(dt_string + " - " + id + " - " + data[0] + " - VAL = " + value + "\n")

def connection_handler(connection_socket, client_address):

    def real_connection_handler():
        global logfile
        try:
            received_data = connection_socket.recv(1024)
        except:
            exit(0)

        #TODO add decryption and verification
        # decryption
        #try:
        #    return rsa.decrypt(ciphertext, key).decode('ascii')
        #except:
        #    return False
        # verification
        #try:
        #    return rsa.verify(message.encode('ascii'), signature, key, ) == 'SHA-1'
        #except:
        #    return False
        received_data = received_data.decode()
        received_data = json.loads(received_data)

        id = received_data['id']
        password = received_data["password"]
        actions = received_data["actions"]["steps"]
        delay = int(received_data["actions"]["delay"])

        # the received_data
        server_message = dict()
        server_message["action"] = "TEST"

        # current user name
        curr_user = user_manager.get_username(client_address)

        clients.append(client_address)
        hashed_id = hashlib.md5(bytes(id, 'utf-8')).hexdigest()
        hashed_password = hashlib.md5(bytes(password, 'utf-8')).hexdigest()

        status = user_manager.new_user(hashed_id, hashed_password)
        user_manager.set_address_username(client_address, hashed_id)
        server_message["status"] = status
        if status == 'SUCCES':
            name_to_socket[hashed_id] = connection_socket
        
        for action in actions:
            action, value = action.split()
            value = int(value)
            if action == 'INCREASE':
                user = user_manager.get_user(client_address)
                user.increaseBalance(value)
                write_log([action, value], id, user.getBalance())
                print("[UPDATE] user balance changed to: " + str(user.getBalance()))

            elif action == 'DECREASE':
                user = user_manager.get_user(client_address)
                user.decreaseBalance(value)
                write_log([action, value], id, user.getBalance())
                print("[UPDATE] user balance changed to: " + str(user.getBalance()))
                
            time.sleep(delay)
        
        if user_manager.get_username_count(hashed_id) == 1:
                user_manager.set_offline(user_manager.get_username(client_address))
                user_manager.user_stripper(hashed_id, hashed_password)
                user_manager.decrease_user_count(hashed_id)
                write_log(["LOGOUT"], id, "N/A")
        else:
            user_manager.decrease_user_count(hashed_id)
        
        if client_address in clients:
            clients.remove(client_address)
            server_message["reply"] = "logged out"

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
