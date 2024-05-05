# simple_python_gui_chat
A server that allows clients to make or join private chatrooms.

Both python files require you to change the 'ip' and 'host' variables respectively to your own ip address (See lines 22 of server.py and 32 of client.py). This repository is meant for learning, so it has only been tested in my local ip.

The user that creates the room will be the admin, who is given a private code to share with any user that wants to join. The admin is also capable of kicking or banning other users from that specific chatroom. To ban an alias in all rooms, the alias must be written manually in the BANS_LIST.txt file. All bans are checked by alias, which is chosen by the client when they first connect, so this is not to be used seriously, it's just meant for showcase.

Once an admin leaves, the role should be handed to the user that has been connected the longest, if there is any.

If any errors arise, please feel free to md me.




