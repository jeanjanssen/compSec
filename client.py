import base64
import ipaddress
import json
import signal
import threading
import time
from socket import *

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from schema import Schema, Use

from key_exchange import Diffie__Hellman

SCHEMA = Schema({
    'id': str,
    'password': str,
    'server': {
        'ip': str,
        'port': Use(int),
    },
    'actions': {
        'delay': Use(int),
        'steps': list
    }
})


def validate(f):
    try:
        data = json.load(f)
    except:
        print("[ERROR] invalid .json formatting")
        return False
    try:
        SCHEMA.validate(data)
    except:
        print("[ERROR] invalid .json formatting")
        return False
    if not data['server']['ip'] == 'localhost':
        try:
            ipaddress.ip_address(data['server']['ip'])
        except:
            print("[ERROR] invalid ip address")
            return False
    if not (1 <= int(data['server']['port']) <= 65535):
        print("[ERROR] invalid port.")
        return False
    if int(data['actions']["delay"]) < 1 or int(data['actions']["delay"]) > 1000:
        print("[ERROR] Invalid delay: 1 <= delay <= 1000 and must be integer.")
        return False
    if len(data['id']) > 1024:
        print("[ERROR] id should not be longer than 1024 characters")
        return False
    if len(data['password']) > 1024:
        print("[ERROR] password should not be longer than 1024 characters")
        return False

    for step in data['actions']['steps']:
        try:
            if len(step) > 1000:
                print("[ERROR] problem reading step: \"" + step + "\"")
                print("[ERROR] action string may not be greater than 1000 characters")
                return False
            action, value = step.split()
            if not int(value) >= 1:
                print("[ERROR] problem reading step: \"" + step + "\"")
                print("[ERROR] value must be an integer >= 1")
                return False
            if not (action == 'INCREASE' or action == "DECREASE"):
                print("[ERROR] problem reading step: \"" + step + "\"")
                print("[ERROR] action must be \'INCREASE\' or \'DECREASE\'")
                return False
        except:
            print("[ERROR] problem reading step: \"" + step + "\"")
            return False

    return True


f = None
data = None
while f == None:
    try:
        fname = input("Please provide the filename of the .json file for this client: ")
        f = open(fname)
        if not validate(f):
            f = None
    except:
        print("[ERROR] Make sure the provided filename is correct.")

f = open(fname)
data = json.load(f)

HEADER = 1024
server_port = int(data['server']['port'])

server_name = data['server']['ip']
ADDR = (server_name, server_port)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

# get the thread
thread_lock = threading.Condition()

client_key = Diffie__Hellman()

client_pub_key = str(client_key.generate_public_KEY())
client_pvt_key = None
server_salt = None

# if set true, main thread will exit at next 0.1 second
to_exit = False

# the program will exit
is_timeout = False

# get the username and password and login
username = data['id']

# username may be overwritten
USERNAME = username
message = json.dumps({
    "action": "login",
    "username": username,
    "password": data['password'],

})

actions = data['actions']


def keyboard_interrupt_handler(signal, frame):
    exit(0)


# logout handler
def logout():
    if is_timeout:
        print("\rYou are timed out.")
    else:
        print("\rYou are logged out.")
        # TODO add encryption
        msg = crypt.encrypt(json.dumps({
            "action": "logout"
        }).encode())
        client__Socket.send(msg)
        client__Socket.close()


# handlesincoming
def sendName():
    # sending name of the client
    client__Socket.send(username.encode(FORMAT))


#  print(username)


def exchangeKeys():
    # exchanging keys
    # getting public key of server
    server_pub_key = int(client__Socket.recv(HEADER).decode(FORMAT))
    # print("exchange client 1 : ", server_pub_key)
    # generating pvt key
    global client_pvt_key
    client_pvt_key = client_key.genenate_shared_KEY(server_pub_key)
    #  print("exchange client 2 : ", client_pvt_key)
    # sending public key of client
    client__Socket.send(client_pub_key.encode(FORMAT))
    #   print("exchange client 3 : ", client_pub_key.encode(FORMAT))
    global server_salt
    server_salt = client__Socket.recv(HEADER)


def reciever_handler():
    global to_exit, is_timeout
    while True:
        login_result = client__Socket.recv(1024)
        data = json.loads(login_result.decode())
        print("recieved data :", data)
        if data['action'] == 'timeout':
            # client timed out by the server
            to_exit = True
            is_timeout = True


# handles all outgoing data
def sending_handler():
    global to_exit
    global actions

    # TODO encryption
    msg = crypt.encrypt(json.dumps(data).encode())
    client__Socket.send(msg)

    to_exit = True
    time.sleep(2)


# start the interaction between client and server
def interact():
    recieved_thread = threading.Thread(name="RecievingHandler", target=reciever_handler)
    recieved_thread.daemon = True
    recieved_thread.start()

    sender_thread = threading.Thread(name="SendingHandler", target=sending_handler)
    sender_thread.daemon = True
    sender_thread.start()

    while True:
        time.sleep(0.1)

        # when set true, exit the main thread
        if to_exit:
            exit(0)


# register keyboard interrupt handler
signal.signal(signal.SIGINT, keyboard_interrupt_handler)

if __name__ == "__main__":
    # start to verify user

    client__Socket = socket(AF_INET, SOCK_STREAM)
    client__Socket.connect((server_name, server_port))

    sendName()

    exchangeKeys()
    salt = server_salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    client_pvt_key_byte = str(client_pvt_key)
    crypt = Fernet(base64.urlsafe_b64encode(kdf.derive(bytes(client_pvt_key_byte, "utf-8"))))

    interact()
