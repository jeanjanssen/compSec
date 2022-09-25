# Computer Security Project guide

Guide to run the code:

[Option 1]

1. Set the Server Port of jsonclient.py and server.py to the same server.
2. Run server.py
3. Run jsonclient.py
4. Give jsonclient.py a .json file configured as described in the "Project - Step 1" manual.
5. jsonclient.py will login and perform the actions as described in the provided .json file.
6. All the information about the actions received from a specific connection will be displayed on the terminal of the server.
7. All the feedback messages from the server will be displayed on the terminal of the client.
8. When all the actions from the json file have been sent to the server, the client disconnects.

[Option 2]

1. Set the Server Port of manualclient.py and server.py to the same server.
2. Run server.py
3. Run manualclient.py
4. In manualclient.py login with a username and password
5. Type either "INCREASE" or "DECREASE" followed by an integer >= 1 to change the value of the account which the client is connected to.
6. All the information about the actions received from a specific connection will be displayed on the terminal of the server.
7. All the feedback messages from the server will be displayed on the terminal of the client.
8. Once you are done with the client type "logout" to disconnect the client.
