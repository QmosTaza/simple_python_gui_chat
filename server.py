import socket
import threading
from _thread import *
import string
import random
import time

class Server:
    chatroom_count = 0
    chatrooms = []

    users = 0
    clients = []
    aliases = []
    banned = []

    def __init__(self):
        self.server_socket = None
        self.init_server()

    def init_server(self):
        ip = "YOUR IP HERE" #YOUR IP HERE
        port = 50000 #CHANGE PORT HERE
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Server socket open")
        self.server_socket.bind((ip,port))
        print("Bind to local port")
        self.server_socket.listen(20) #max number of connections at once
        print("Started listening")
        self.receive_client()

    #Listen for clients
    def receive_client(self):
        while True:
            client, address = self.server_socket.accept()
            print(f"Server connected to {str(address)}")

            #Ask for Alias
            client.send("ALIAS?".encode("utf-8"))
            client_login = client.recv(1024).decode("utf-8")
            alias = client_login[6:]
            # -> ¿Alias banned from Server? 
            with open("BANS_LIST.txt", 'r') as f:
                bans = f.readlines()
                f.close()
            if alias+'\n' in bans:
                client.send("BAN!".encode("utf-8"))
                client.close()
                print(f"Client connected to {str(address)} disconnected")
                continue
            else:
                # -> Create your own chat 
                if client_login.startswith("MAKE!"):
                    client.send("ADMIN!".encode("utf-8"))
                    self.chatroom_count += 1
                    room_code = self.generate_code(8)
                    self.chatrooms.append(room_code)
                    self.users += 1
                    self.clients.append([client])
                    self.aliases.append([alias])
                    self.banned.append([])
                    client.send(f"{room_code}".encode("utf-8"))
                    thread = threading.Thread(target=self.receive_messages, args=(client, room_code))
                    thread.start()
                    client.send(f"You are the administrator! The room code is {room_code}\n".encode("utf-8"))

                # -> Join someone else's chat
                elif client_login.startswith("JOIN!"):
                    client.send("ROOM?".encode("utf-8"))
                    room_code = client.recv(1024).decode("utf-8")
                    if room_code in self.chatrooms:
                        room_index = self.chatrooms.index(room_code)
                        if alias not in self.banned[room_index]:
                            client.send("SUCCESS!".encode("utf-8"))
                            self.users += 1
                            self.clients[room_index].append(client)
                            self.aliases[room_index].append(alias)
                            thread = threading.Thread(target=self.receive_messages, args=(client, room_code))
                            thread.start()
                            self.broadcast(f"{alias} has joined the room!\n".encode("utf-8"), room_code)
                        else:
                            client.send("REFUSE!".encode("utf-8"))
                    else:
                        client.send("NO ROOM!".encode("utf-8"))
                else:
                    continue
            
    #Generate room code
    def generate_code(self, length):
        characters = string.ascii_letters + string.digits
        random_str = ''.join(random.choice(characters) for i in range(length))
        if self.chatroom_count > 0 and random_str not in self.chatrooms:
            return random_str
        elif self.chatroom_count > 0:
            return self.generate_code(8)

    #Broadcast to all.users in room
    def broadcast(self, message, room_code):
        if self.chatroom_count > 0 and room_code in self.chatrooms:
            index = self.chatrooms.index(room_code)
            for client in self.clients[index]:
                client.send(message)

    #Broadcast to all.users but one
    def exclude_broadcast(self, message, user, room_code):
        if self.chatroom_count > 0 and room_code in self.chatrooms:
            index = self.chatrooms.index(room_code)
            for client in self.clients[index]:
                if client != user:
                    client.send(message)

    #Remove room
    def del_room(self, room_code):
        print("Room disconnected")
        if room_code in self.chatrooms:
            self.chatrooms.remove(room_code)
            self.chatroom_count -= 1

    #Remove user
    def del_user(self, client, room_code):
        client.close()
        print("Client disconnected")
        if room_code in self.chatrooms:
            index = self.chatrooms.index(room_code)
            if client in self.clients[index]:
                client_index = self.clients[index].index(client)
                alias = self.aliases[index][client_index]
                self.users -= 1
                self.clients[index].remove(client)
                self.aliases[index].remove(alias)
                #User was the only one left in room
                if len(self.clients[index]) == 0:
                    self.del_room(room_code)
                else:
                    self.broadcast(f"{alias} has left the room.\n".encode("utf-8"), room_code)
                    #User was admin
                    if client_index == 0:
                        alias = self.aliases[index][0]
                        self.exclude_broadcast(f"{alias} is the new admin.\n".encode("utf-8"), self.clients[index][0], room_code)
                        time.sleep(0.5)
                        self.clients[index][0].send("ADMIN!".encode("utf-8"))

    #Kick user from chat
    def kick_user(self, alias, room_code):
        index = self.chatrooms.index(room_code)
        if alias in self.aliases[index]:
            alias_index = self.aliases[index].index(alias)
            client = self.clients[index][alias_index]
            client.send("You were kicked out by the admin!\n".encode("utf-8"))
            time.sleep(0.5)
            client.send("KICK!".encode("utf-8"))
            #self.del_user(client, room_code)
            self.exclude_broadcast(f"{alias} has been kicked out by the admin!\n".encode("utf-8"), client, room_code)

    #Handle connected client
    def receive_messages(self, client, room_code):
        while True:
            try:
                buffer = client.recv(1024)
                if not buffer:
                    break
                message = buffer.decode("utf-8")
                #PROCESS SPECIAL MESSAGES HERE
                # -> Kick user
                if message.startswith("KICK"):   
                    index = self.chatrooms.index(room_code)
                    if self.clients[index].index(client) == 0:
                        kicked_alias = message[5:]
                        self.kick_user(kicked_alias, room_code)
                        print(f"{kicked_alias} was kicked")
                    else:
                        client.send("Command was refused.\n".encode("utf-8"))
                # -> Ban user
                elif message.startswith("BAN"):
                    index = self.chatrooms.index(room_code)
                    if self.clients[index].index(client) == 0:
                        kicked_alias = message[4:]
                        self.banned[index].append(kicked_alias)
                        self.kick_user(kicked_alias, room_code)
                        print(f"{kicked_alias} was banned")
                    else:
                        client.send("Command was refused.\n".encode("utf-8"))
                # -> User leaves chat
                elif message.startswith("LEAVE"):
                    self.del_user(client, room_code)
                    break
                # -> Public message, to be broadcasted
                else:
                    self.broadcast(message.encode("utf-8"), room_code)
            except (ConnectionAbortedError, ConnectionResetError) :
                break
            except:
                self.del_user(client, room_code)
                break


Server()
