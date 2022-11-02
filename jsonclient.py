import hashlib
import json
import atexit
import threading
import time
import sys
import signal
import readline
import rsa
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

# TODO generate keys for signing messages and receive PublicKey server
# TODO Immediately send own public key for signing messages
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

del data

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
    
    # handle input and send to server
    delay = int(actions['delay'])

    for step in actions['steps']:
        if step.startswith("INCREASE"):
            try: 
                action, value = step.split()
                if int(value) >= 1:
                    commandmsg = json.dumps({
                    "action": action,
                    "value": int(value)
                    })
                    client__Socket.send(commandmsg.encode())
                else:
                    print("[ERROR] value must be an integer >= 1")
            except:
                print("[ERROR] problem reading step: \"" + step + "\"")

        elif step.startswith("DECREASE"):
            try: 
                action, value = step.split()
                if int(value) >= 1:
                    commandmsg = json.dumps({
                    "action": action,
                    "value": int(value)
                    })

                    # TODO Add encryption using server publicKey
                    # encrypt_message rsa.encrypt(message.encode('ascii'), key)
                    # TODO Add signature using own privateKey
                    # signature = sign(message, privateKey)
                    # TODO Send both encrypted message and signature
                    client__Socket.send(commandmsg.encode())
                else:
                    print("[ERROR] value must be an integer >= 1")
            except:
                print("[ERROR] problem reading step: \"" + step + "\"")
        
        else:
            print("Invalid action: \"" + step + "\"")
        time.sleep(delay)

    logout()
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


# log in then start interaction if successfully authenticated
def log_in_attempt():
    global message
    # TODO Add encryption
    # encrypt_message rsa.encrypt(message.encode('ascii'), key)
    # TODO Add signature
    # signature = sign(message, privateKey)
    # TODO Send both encrypted message and signature
    client__Socket.send(message.encode())

    # wait for the reply from the server
    login_status = client__Socket.recv(1024)
    login_status = json.loads(login_status.decode())

    if login_status["action"] == 'login' and login_status["status"] == "SUCCESS":
        # successfully authenticated
        print("You are logged in")
        # register on logout cleanup
        atexit.register(logout)


        # start interaction
        interact()
   # elif login_status["action"] == 'login' and login_status["status"] == "ALREADY_LOGGED_IN":
   #     print("You have already logged in.")
    elif login_status["action"] == 'login' and login_status["status"] == "INVALID_PASSWORD_BLOCKED":
        print("Invalid password. Your account has been blocked. Please try again later.")
    elif login_status["action"] == 'login' and login_status["status"] == "BLOCKED":
        print("Due to multiple failed log in attempts , you have been blocked.")
    elif login_status["action"] == 'login' and login_status["status"] == "INVALID_PASSWORD":
        # invalid password, try again
        message = json.dumps({
            "action": "login",
            "username": username,
            "password": input("Invalid password. Try again: "),
        })
        log_in_attempt()
  #  elif login_status["action"] == 'login' and login_status["status"] == "ALREADY_LOGGED_IN":
  #      print(login_status["status"])
    elif login_status["action"] == 'login' and login_status["status"] == "USERNAME_NOT_EXIST":
        print(login_status["status"])
    else:
        # things unexpected
        print(" unexpected message")
        exit(1)


# register keyboard interrupt handler
signal.signal(signal.SIGINT, keyboard_interrupt_handler)

if __name__ == "__main__":
    # start to verify user
    log_in_attempt()


