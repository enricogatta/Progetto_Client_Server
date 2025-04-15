import socket
import threading
import json
import os
import hashlib

#HOST = '127.0.0.1'
HOST = '0.0.0.0'
PORT = 12345

# File per memorizzare gli utenti
USERS_FILE = "users.json"
CHATS_FILE = "chats.json"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

# Dizionario per tenere traccia dei client connessi e dei loro username
clients = {}  # socket -> username
online_users = []  # lista username online
user_chats = {}  # username -> chat_name
chat_users = {"principale": []}  # chat_name -> [users]
available_chats = ["principale"]  # lista di chat disponibili

# Semaforo per limitare il numero di chat
chat_semaphore = threading.Semaphore(5)  # Limite di 5 chat totali


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


def send_online_users(client_socket):
    users_list = ", ".join(online_users)
    client_socket.send(f"SERVER: Utenti online: {users_list}".encode("utf-8"))


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


def handle_auth(client_socket, address):
    print(f"Gestione autenticazione per {address}")
    try:
        while True:
            try:
                auth_data = client_socket.recv(1024).decode("utf-8")
                if not auth_data:
                    print(f"Client {address} disconnesso durante l'autenticazione")
                    client_socket.close()
                    return

                print(f"Ricevuto da {address}: {auth_data}")

                # Formato atteso: ACTION:username:password
                parts = auth_data.split(":", 2)
                if len(parts) != 3:
                    client_socket.send("ERROR:Formato non valido".encode("utf-8"))
                    continue

                action, username, password = parts

                if action == "LOGIN":
                    if username in users and users[username] == hash_password(password):
                        if username in online_users:
                            client_socket.send("ERROR:Utente già connesso".encode("utf-8"))
                        else:
                            client_socket.send(f"SUCCESS:{username}".encode("utf-8"))
                            clients[client_socket] = username
                            online_users.append(username)
                            print(f"Utente {username} connesso")
                            # Avvia il thread per gestire i messaggi del client
                            threading.Thread(target=handle_client, args=(client_socket, username)).start()
                            return
                    else:
                        client_socket.send("ERROR:Username o password non validi".encode("utf-8"))

                elif action == "REGISTER":
                    if username in users:
                        client_socket.send("ERROR:Username già esistente".encode("utf-8"))
                    else:
                        users[username] = hash_password(password)
                        save_users(users)
                        client_socket.send(f"SUCCESS:{username}".encode("utf-8"))
                        clients[client_socket] = username
                        online_users.append(username)
                        print(f"Nuovo utente registrato: {username}")
                        # Avvia il thread per gestire i messaggi del client
                        threading.Thread(target=handle_client, args=(client_socket, username)).start()
                        return
                else:
                    client_socket.send("ERROR:Azione non valida".encode("utf-8"))

            except Exception as e:
                print(f"Errore durante l'autenticazione: {e}")
                client_socket.close()
                return
    except Exception as e:
        print(f"Errore critico durante l'autenticazione: {e}")
        try:
            client_socket.close()
        except:
            pass


def receive_connections():
    print(f"Server in ascolto su {HOST}:{PORT}")
    try:
        while True:
            client_socket, address = server.accept()
            print(f"Connesso con {address}")
            # Avvia un thread per gestire l'autenticazione del client
            threading.Thread(target=handle_auth, args=(client_socket, address)).start()
    except KeyboardInterrupt:
        print("Server interrotto")
    except Exception as e:
        print(f"Errore durante l'accettazione delle connessioni: {e}")
    finally:
        server.close()
        print("Server chiuso")

if __name__ == "__main__":
   print("Avvio del server...")
   try:
       receive_connections()
   except Exception as e:
       print(f"Errore fatale: {e}")
