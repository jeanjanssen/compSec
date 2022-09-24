import hashlib
import threading
import time
import json
import signal
from socket import *
from typing import Dict
from userhandler import userhandler

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

# map username to connection socket
name_to_socket: Dict = dict()

# would communicate with clients after every second
UPDATE_INTERVAL = 1

# user manager manages all the user data
user_manager = userhandler(block_duration, timeout)

def keyboard_interrupt_handler(signal, frame):
    print("\rServer is shutdown")
    exit(0)

def on_close():
  Server__Socket.close()

def connection_handler(connection_socket, client_address):

    def real_connection_handler():
        while True:
            try:
                received_data = connection_socket.recv(1024)
            except:
                exit(0)

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
                        else:
                            user_manager.decrease_user_count(username)
                        
                        if client_address in clients:
                            clients.remove(client_address)
                            server_message["reply"] = "logged out"

                    elif action == 'INCREASE':
                        user = user_manager.get_user(client_address)
                        user.increaseBalance(data["value"])
                        print("[UPDATE] user balance changed to: " + str(user.getBalance()))

                    elif action == 'DECREASE':
                        user = user_manager.get_user(client_address)
                        user.decreaseBalance(data["value"])
                        print("[UPDATE] user balance changed to: " + str(user.getBalance()))

                    else:
                        server_message["reply"] = "Unknown action"
                    
                    try:
                        connection_socket.send(json.dumps(server_message).encode())
                    except:
                        print("[ERROR] could not return message to client, has probably already disconnected.")
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
    print(f"[LISTENING] Server is listening on {SERVER}")
    print('Server is up.')
    while True:
        time.sleep(0.1)

        # update any information of all user data
        user_manager.update()


print("[STARTING] server is starting...")
start()
