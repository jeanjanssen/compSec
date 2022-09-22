from typing import Dict
from time import time


class userhandeler:


    def __init__(self, block_dur: int, time_out_dur: int):
        self.users_dict: Dict[str, userhandeler.__User] = dict()
        self.address2username_map: Dict[str, str] = dict()
        self.username2address_map: Dict[str, str] = dict()
        self.blockduration: int = block_dur
        self.time_out: int = time_out_dur
        self.read_file()

    def add_file(self, username_input: str, password_input: str):

            try:
                with open("logins.txt", "a") as credential_file:
                    new_acc =[ "" ,username_input+" "+password_input]
                    credential_file.write("\n".join(new_acc))
                    self.read_file()
            except:
             print(" error adding logins.txt")
             exit(1)




    def read_file(self):
        try:
            with open("logins.txt", "r") as credential_file:
                for credential in credential_file:
                    username, password = credential.strip().split()
                    self.users_dict[username] = userhandeler.__User(username, password,
                                                                    self.blockduration,
                                                                    self.time_out)
        except:
            print("error reading logins.txt")
            exit(1)



    def new_user(self, username_input: str, password_input: str):
        if username_input not in self.users_dict:
            # username unknown
            print("Creating new user")
            self.add_file(username_input, password_input)

            return "SUCCESS"
        else :
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



    def refresh_user_timeout(self, username):
        # update a user's last active time
        if username in self.users_dict:
            self.users_dict[username].refresh_user_timeout()

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
            self.Balance: int = 0

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

        def update_time_out(self):
            # update time out status, return true if should lof out this user because of timeout
            if self.is_online() and self.inactive_since + self.timeout < time():
                self.set_offline()
                return True
            return False

        def refresh_user_timeout(self):
            self.inactive_since = time()

        def Increasebalance(self, int):
            self.balance = self.balance +int

        def Decreasebalance(self, int):
            self.balance = self.balance - int

        def authenticate(self, password_input: str):
            # authenticate, return the status of the updated user

            #if self.online:
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
            self.refresh_user_timeout()
            return "SUCCESS"
