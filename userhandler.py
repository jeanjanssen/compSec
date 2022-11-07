from time import time
from typing import Dict


class userhandler:

    def __init__(self, block_dur: int, time_out_dur: int):
        self.users_dict: Dict[str, userhandler.__User] = dict()
        self.address2username_map: Dict[str, str] = dict()
        self.username2address_map: Dict[str, str] = dict()
        self.username2count_map: Dict[str, int] = dict()
        self.blockduration: int = block_dur
        self.time_out: int = time_out_dur
        self.read_file()

    def user_stripper(self, username_input: str, password_input: str):
        try:
            del self.users_dict[username_input]
            with open('logins.txt', 'r') as file:
                text = file.read()

            # Delete text and Write
            with open('logins.txt', 'w') as file:
                # Delete
                new_text = text.replace(username_input + " " + password_input + "\n", '')
                # Write
                file.write(new_text)
        except:
            print("error delete user")
            exit(1)

    def add_file(self, username_input: str, password_input: str):

        try:
            with open("logins.txt", "a") as credential_file:
                new_acc = username_input + " " + password_input + "\n"
                credential_file.write(new_acc)
                self.read_file()
        except:
            print(" error adding logins.txt")
            exit(1)

    def read_file(self):
        open('logins.txt', 'w').close()
        try:
            with open("logins.txt", "r") as credential_file:
                for credential in credential_file:
                    username, password = credential.strip().split()
                    self.users_dict[username] = userhandler.__User(username, password,
                                                                   self.blockduration,
                                                                   self.time_out)
        except:
            print("error reading logins.txt")
            exit(1)

    def get_user(self, client_address):
        try:
            return self.users_dict[self.get_username(client_address)]
        except:
            print("[ERROR] could not find user")

    def new_user(self, username_input: str, password_input: str):
        print("[LOGGING IN USER]")
        if username_input not in self.users_dict:
            print("[CREATING NEW USER]")
            # username unknown
            self.add_file(username_input, password_input)
            self.users_dict[username_input] = userhandler.__User(username_input, password_input,
                                                                 self.blockduration,
                                                                 self.time_out)

            return "SUCCESS"
        else:
            print("[VERIFYING THROUGH EXISTING USER]")
            status = self.verify(username_input, password_input)
        return status

    def verify(self, username_input: str, password_input: str):
        # verify user and update status
        # return updated status in a string format

        if username_input not in self.users_dict:
            # username unknown
            return "USERNAME_NOT_EXIST"
        return self.users_dict[username_input].authenticate(password_input)

    def set_address_username(self, address: str, username: str):
        self.address2username_map[address] = username
        self.username2address_map[username] = address
        if username in self.username2count_map:
            self.username2count_map[username] += 1
        else:
            self.username2count_map[username] = 1

    def get_username_count(self, username: str):
        return self.username2count_map[username]

    def decrease_user_count(self, username: str):
        self.username2count_map[username] -= 1

    def get_username(self, address: str) -> str:
        if address in self.address2username_map:
            return self.address2username_map[address]
        else:
            return ""

    def get_address(self, username: str) -> str:
        if username in self.username2address_map:
            return self.username2address_map[username]
        else:
            return ""

    def set_offline(self, username):
        if username in self.users_dict:
            self.users_dict[username].set_offline()

    def update(self):
        # update all user's block status
        for user_credential in self.users_dict.values():
            user_credential.update()

    class __User:

        # manage username, password, online status, number of consecutive fail trials,
        # blocked timestamp

        def __init__(self, username: str, password: str, block_duration: int, timeout: int):
            self.username: str = username
            self.password: str = password
            self.block_duration: int = block_duration
            self.timeout: int = timeout
            self.online: bool = False
            self.blocked: bool = False
            self.consecutive_fails: int = 0
            self.blocked_since: int = 0
            self.balance: int = 0

        def getBalance(self):
            return self.balance

        def block(self, username: str):
            self.__blocked_users.add(username)

        def unblock(self, username: str):
            if username in self.__blocked_users:
                self.__blocked_users.remove(username)

        def update(self):
            # unblock users if any
            if self.blocked and self.blocked_since + self.block_duration < time():
                self.blocked = False

        def set_offline(self):
            self.online = False
            self.consecutive_fails = 0
            self.blocked_since = 0

        def is_online(self):
            return self.online

        def increaseBalance(self, int):
            self.balance = self.balance + int

        def decreaseBalance(self, int):
            self.balance = self.balance - int

        def authenticate(self, password_input: str):
            # authenticate, return the status of the updated user

            # if self.online:
            # user is already logged in
            # return "ALREADY_LOGGED_IN"

            if self.blocked:
                # user is blocked
                return "BLOCKED"

            if self.password != password_input:
                # incorrect password
                self.consecutive_fails += 1
                if self.consecutive_fails >= 3:
                    self.blocked_since = time()
                    self.blocked = True
                    return "INVALID_PASSWORD_BLOCKED"
                return "INVALID_PASSWORD"

            # is able to login. update status
            self.online = False
            self.__last_login = int(time())
            return "SUCCESS"
