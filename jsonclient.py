import json
import threading
import time
import signal
import ipaddress
from socket import *
from schema import Schema, Use, SchemaError

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

HEADER = 64
server_port = int(data['server']['port'])

server_name = data['server']['ip']
ADDR = (server_name, server_port)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

# connect to the server
client__Socket = socket(AF_INET, SOCK_STREAM)
client__Socket.connect((server_name, server_port))

# get the thread
thread_lock = threading.Condition()

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
        client__Socket.send(json.dumps({
            "action": "logout"
        }).encode())
        client__Socket.close()

# handlesincoming
def reciever_handler():
    global to_exit, is_timeout
    while True:
        login_result = client__Socket.recv(1024)
        data = json.loads(login_result.decode())
        if data['action'] == 'timeout':
            # client timed out by the server
            to_exit = True
            is_timeout = True


# handles all outgoing data
def sending_handler():
    global to_exit
    global actions
    
    client__Socket.send(json.dumps(data).encode())

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
    interact()


