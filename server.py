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
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except:
                client.close()
                if client in clients:
                    clients.remove(client)

def handle_client(client):
    while True:
        try:
            msg = client.recv(1024)
            if msg:
                broadcast(msg, sender_socket=client)
        except:
            if client in clients:
                clients.remove(client)
            client.close()
            break

def receive_connections():
    print(f"Server in ascolto su {HOST}:{PORT}")
    while True:
        client, address = server.accept()
        print(f"Connesso con {address}")
        clients.append(client)
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

receive_connections()
