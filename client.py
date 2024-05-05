import socket
import threading
import string
import random
import tkinter
import tkinter.scrolledtext
import tkinter.messagebox
from tkinter import simpledialog

class GUI:
    client_socket = None

    def __init__(self, master) -> None:
        self.root = master
        self.chat_text_area = None
        self.chat_input_area = None
        self.send_button = None

        self.alias = None

        self.gui_complete = False
        self.is_admin = False
        self.run = True
        
        self.init_socket()
        self.login_user()
        thread = threading.Thread(target=self.receive_from_server, args=(self.client_socket,))
        thread.start()

    #Connect socket to server
    def init_socket(self):
        host = "YOUR IP HERE" #YOUR IP HERE
        port = 50000 #CHANGE PORT HERE
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        print("Client connected")

    #Ask for user's alias
    def login_user(self):
        message_box = tkinter.Tk()
        message_box.withdraw()

        self.alias = simpledialog.askstring("Alias", "Please choose a nickname: ", parent=message_box).strip()
        if self.alias == "":
            self.alias = self.generate_random_str(5)

    #Ask whether they are creating a room or joining one
    def option_select(self):
        message_box = tkinter.Tk()
        message_box.withdraw()

        selected_option = tkinter.messagebox.askyesno("Create a Chatroom?", "Do you want to create your own room?\n(Press no to join one instead)", parent=message_box)
        return selected_option

    #Generate random_str
    def generate_random_str(self, length):
        characters = string.ascii_letters + string.digits
        random_str = ''.join(random.choice(characters) for i in range(length))
        return random_str

    #Ask for room code   
    def room_select(self):
        message_box = tkinter.Tk()
        message_box.withdraw()

        room_code = simpledialog.askstring("Room Code", "Please enter the chatroom's code: ", parent=message_box).strip()
        return room_code
    
    #Pop up message
    def message_box(self, message, type):
        window = tkinter.Tk()
        window.withdraw()
        w = tkinter.Label(window, text="Alert", font="50")
        w.pack()
        if type == "error":
            tkinter.messagebox.showerror("Error", message, parent=window)
        elif type == "warning":
            tkinter.messagebox.showwarning("Warning", message, parent=window)
        else:
            tkinter.messagebox.showinfo("Alert", message, parent=window)
        window.mainloop()

    #Initialise chat visuals
    def init_gui(self):
        self.root.deiconify()
        self.root.title("Simple Chatter")
        self.root.configure(bg = "Lightgray")
        self.root.resizable(0,0) #can be resized

        self.room_label = tkinter.Label(self.root, text="Chat:", bg="Lightgray")
        self.room_label.config(font=("Arial", 12))
        self.room_label.pack(padx=20, pady=5)

        self.chat_text_area = tkinter.scrolledtext.ScrolledText(self.root)
        self.chat_text_area.pack(padx=20, pady=5)
        self.chat_text_area.config(state="disabled")

        self.msg_label = tkinter.Label(self.root, text="Message:", bg="Lightgray")
        self.msg_label.config(font=("Arial", 12))
        self.msg_label.pack(padx=20, pady=5)    

        self.chat_input_area = tkinter.Text(self.root, height=1)
        self.chat_input_area.pack(padx=20, pady=5)  
        self.chat_input_area.bind('<Return>', self.on_enter_key)

        self.send_button = tkinter.Button(self.root, text="Send", command=self.write_message)
        self.send_button.config(font=("Arial", 12))
        self.send_button.pack(padx=20, pady=5) 

        self.gui_complete = True
        
    #Close chat forcefully
    def shutdown_room(self):
        self.client_socket.send("LEAVE".encode("utf-8"))
        self.run = False
        self.root.quit()
        self.client_socket.close()
        exit(0)

    def close_room(self):
        if tkinter.messagebox.askokcancel("Leave", "Are you sure you want to leave?"):
            self.client_socket.send("LEAVE".encode("utf-8"))
            self.run = False
            self.root.quit()
            self.client_socket.close()
            exit(0)

    #Show message in chat (private)
    def visualise_message(self, message):
        try:
            if self.gui_complete == True:
                self.chat_text_area.config(state="normal")
                self.chat_text_area.insert('end', message)
                self.chat_text_area.yview('end')
                self.chat_text_area.config(state="disabled")
        except:
            self.shutdown_room()

    #Send message when you press enter
    def on_enter_key(self, event=None):
        self.write_message()

    #Send message to be broadcasted
    def write_message(self):
        input_message = self.chat_input_area.get('1.0', 'end').strip()
        message = f"{self.alias}: {input_message}" + "\n"
        
        self.client_socket.send(message.encode("utf-8"))
        self.chat_input_area.delete('1.0', 'end')

        if input_message.startswith('/'):
            if self.is_admin == True:
                if input_message.startswith("/kick"):
                    self.client_socket.send(f"KICK {input_message[6:]}".encode("utf-8"))
                elif input_message.startswith("/ban"):
                    self.client_socket.send(f"BAN {input_message[5:]}".encode("utf-8"))
                else:
                    self.visualise_message("Command doesn't exist!\n")
            else:
                self.visualise_message("Commands can only be executed by the administrator!\n")
         
    #Listen to incoming messages
    def receive_from_server(self, socket):
        while True:
            try:
                buffer = socket.recv(1024)
                if not buffer:
                    break
                message = buffer.decode("utf-8")

                #SPECIAL MESSAGES
                if message == "ALIAS?":
                    #Ask whether you are creating a room or joining one
                    selected_option = self.option_select()
                    if selected_option:
                        socket.send(f"MAKE! {self.alias}".encode("utf-8"))
                    else:
                        socket.send(f"JOIN! {self.alias}".encode("utf-8"))
                    
                    validation_message = socket.recv(1024).decode("utf-8")
                    if not validation_message:
                        self.shutdown_room()
                        break
                    # -> Succesfully joining a room
                    if validation_message == "ROOM?":
                        room_code = self.room_select()
                        socket.send(room_code.encode("utf-8"))
                        validation_message = socket.recv(1024).decode("utf-8")
                        if validation_message == "SUCCESS!":
                            print("Connection successful!")
                            self.init_gui()
                        # -> Unsuccesfully joining a room: Alias previously banned from chatroom
                        elif validation_message == "REFUSE!":
                            self.message_box(message="Connection refused because of chatroom ban\nClosing down", type="error")
                            self.shutdown_room()
                    # -> Creating a room
                    elif validation_message == "ADMIN!":
                        self.is_admin = True
                        room_code = socket.recv(1024).decode("utf-8")
                        self.init_gui()
                    # -> Unsuccesfully joining a room: Alias banned from server
                    elif validation_message == "BAN!":
                        self.message_box(message="Connection refused because of server ban. \nClosing down", type="error")
                        self.shutdown_room()
                    # -> Unsuccesfully joining a room: Room doesn't exist
                    elif validation_message == "NO ROOM!":
                        self.message_box(message="Chatroom doesn't exist. \nClosing down", type="error")
                        self.shutdown_room()
                # User has become the admin
                elif message == "ADMIN!":
                    self.visualise_message("You are now the admin!\n")
                    self.is_admin = True
                # User has been kicked
                elif message == "KICK!":
                    self.shutdown_room()
                
                # Ordinary messages are broadcasted
                else:
                    self.visualise_message(message)
            except ConnectionAbortedError:
                break  
            except:
                if self.run == True:
                    self.root.destroy()
                    self.client_socket.close()
                    exit(0)
                break
        socket.close()


root = tkinter.Tk()
root.withdraw()
gui = GUI(root)
root.protocol("WM_DELETE_WINDOW", gui.close_room)
root.mainloop()