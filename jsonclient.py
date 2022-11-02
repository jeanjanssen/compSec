import hashlib
import json
import atexit
import threading
import time
import sys
import signal
import readline
from socket import *

f = None
while f == None:
    try:
        fname = input("Please provide the filename of the .json file for this client: ")
        f = open(fname)
    except:
        print("[ERROR] Could not read json file. Make sure it is valid.")


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

try:
    if int(actions["delay"]) < 1:
        sys.exit("[ERROR] delay is not integer >= 1. Aborting...")
except:
    sys.exit("[ERROR] delay is not integer >= 1. Aborting...")

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


# print without breaking input thread
def safe_printer(*args):
    sys.stdout.write('\r' + ' ' * (len(readline.get_line_buffer()) + 2) + '\r')
    print(*args)
    sys.stdout.write('> ' + readline.get_line_buffer())
    sys.stdout.flush()

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
        else:
            # unexpected format
            safe_printer(data)


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


