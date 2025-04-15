import socket
import threading
import json
import os
import hashlib

HOST = '127.0.0.1'
PORT = 12345

# File per memorizzare gli utenti
USERS_FILE = "users.json"


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

# Dizionario per tenere traccia dei client connessi e dei loro username
clients = {}
online_users = []

# Carica gli utenti dal file o crea un nuovo file se non esiste
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Errore nel file utenti. Creazione di un nuovo file.")
            return {}
    else:
        return {}


# Salva gli utenti nel file
def save_users(users):
   with open(USERS_FILE, 'w') as f:
       json.dump(users, f)


# Hash della password per maggiore sicurezza
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users = load_users()

def broadcast(message, sender_socket=None):
    for client_socket in clients:
        if client_socket != sender_socket:
            try:
                client_socket.send(message)
            except:
                # Gestito dalla funzione handle_client quando il client è disconnesso
                pass


def handle_client(client_socket, username):
    try:
        # Notifica a tutti che un nuovo utente è entrato
        broadcast(f"SERVER: {username} è entrato nella chat.".encode("utf-8"))

        # Invia la lista degli utenti online
        send_online_users(client_socket)

        while True:
            try:
                message = client_socket.recv(1024).decode("utf-8")

                if not message:  # Se il client si disconnette
                    break

                if message.startswith("/online"):
                    send_online_users(client_socket)
                else:
                    broadcast(message.encode("utf-8"), sender_socket=client_socket)
            except:
                break
    finally:
        # Rimuovi il client disconnesso
        if client_socket in clients:
            username = clients[client_socket]
            del clients[client_socket]

            if username in online_users:
                online_users.remove(username)

            broadcast(f"SERVER: {username} è uscito dalla chat.".encode("utf-8"))

        try:
            client_socket.close()
        except:
            pass

        print(f"Cliente {username} disconnesso")

def receive_connections():
    print(f"Server in ascolto su {HOST}:{PORT}")
    while True:
        client, address = server.accept()
        print(f"Connesso con {address}")
        clients.append(client)
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

receive_connections()
