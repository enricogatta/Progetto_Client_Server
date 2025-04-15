import socket
import threading
import json
import os
import hashlib


HOST = '127.0.0.1'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []

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
