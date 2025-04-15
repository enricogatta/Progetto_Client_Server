import socket
import threading
import json
import os
import hashlib

HOST = '0.0.0.0'  # Modificato per accettare connessioni da qualsiasi interfaccia
PORT = 12345

# File per memorizzare gli utenti e le chat
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


# Carica le chat dal file o crea un nuovo file se non esiste
def load_chats():
    global chat_users, available_chats
    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, 'r') as f:
                chat_data = json.load(f)
                chat_users = chat_data.get("chat_users", {"principale": []})
                available_chats = chat_data.get("available_chats", ["principale"])

                # Assicurati che il semaforo sia correttamente inizializzato
                global chat_semaphore
                remaining_slots = max(0, 5 - len(available_chats))
                chat_semaphore = threading.Semaphore(remaining_slots)

                return
        except json.JSONDecodeError:
            print("Errore nel file chat. Creazione di un nuovo file.")

    # Se non esiste o c'è un errore, inizializza con valori predefiniti
    chat_users = {"principale": []}
    available_chats = ["principale"]
    save_chats()


# Salva gli utenti nel file
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)


# Salva le chat nel file
def save_chats():
    with open(CHATS_FILE, 'w') as f:
        chat_data = {
            "chat_users": chat_users,
            "available_chats": available_chats
        }
        json.dump(chat_data, f)


# Hash della password per maggiore sicurezza
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Carica i dati all'avvio
users = load_users()
load_chats()


# Invia messaggio solo agli utenti in una specifica chat
def broadcast_to_chat(chat_name, message, sender_socket=None):
    usernames_in_chat = chat_users.get(chat_name, [])
    for client_socket, username in clients.items():
        if client_socket != sender_socket and username in usernames_in_chat:
            try:
                client_socket.send(message)
            except:
                # Gestito dalla funzione handle_client quando il client è disconnesso
                pass


# Notifica a tutti gli utenti online della disponibilità di una nuova chat
def notify_chat_change():
    chat_list = ",".join(available_chats)
    update_message = f"CHATLIST:{chat_list}".encode("utf-8")

    for client_socket in clients:
        try:
            client_socket.send(update_message)
        except:
            # Errori gestiti altrove
            pass


# Invia a tutti gli utenti
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


def send_chat_list(client_socket):
    chat_creation_allowed = len(available_chats) < 5
    chats_list = ",".join(available_chats)
    client_socket.send(f"CHATLIST:{chats_list}:{chat_creation_allowed}".encode("utf-8"))


def handle_client(client_socket, username):
    try:
        # Inizialmente l'utente non è in nessuna chat
        current_chat = None

        # Invia la lista delle chat disponibili
        send_chat_list(client_socket)

        while True:
            try:
                message = client_socket.recv(1024).decode("utf-8")
                if not message:  # Se il client si disconnette
                    break

                # Gestione comandi speciali
                if message.startswith("/"):
                    if message == "/online":
                        send_online_users(client_socket)
                    elif message == "/listchats":
                        send_chat_list(client_socket)
                    elif message.startswith("/joinchat:"):
                        chat_name = message.split(":", 1)[1]
                        if chat_name in available_chats:
                            # Rimuovi l'utente dalla chat corrente se esiste
                            if current_chat and username in chat_users.get(current_chat, []):
                                chat_users[current_chat].remove(username)
                                broadcast_to_chat(current_chat,
                                                  f"SERVER: {username} è uscito dalla chat.".encode("utf-8"))

                            # Aggiungi l'utente alla nuova chat
                            if chat_name not in chat_users:
                                chat_users[chat_name] = []

                            chat_users[chat_name].append(username)
                            user_chats[username] = chat_name
                            current_chat = chat_name

                            # Notifica nella chat che un nuovo utente è entrato
                            broadcast_to_chat(chat_name,
                                              f"SERVER: {username} è entrato nella chat.".encode("utf-8"))

                            # Invia lista utenti nella chat
                            chat_users_list = ", ".join(chat_users.get(chat_name, []))
                            client_socket.send(
                                f"SERVER: Utenti nella chat '{chat_name}': {chat_users_list}".encode("utf-8"))
                        else:
                            client_socket.send(f"SERVER: La chat '{chat_name}' non esiste.".encode("utf-8"))

                    elif message.startswith("/createchat:"):
                        chat_name = message.split(":", 1)[1]
                        if chat_name in available_chats:
                            client_socket.send(f"SERVER: La chat '{chat_name}' esiste già.".encode("utf-8"))
                        elif len(available_chats) >= 5:
                            client_socket.send(f"SERVER: Numero massimo di chat (5) raggiunto.".encode("utf-8"))
                        else:
                            # Utilizzo del semaforo per controllare il numero di chat
                            if chat_semaphore.acquire(blocking=False):
                                available_chats.append(chat_name)
                                chat_users[chat_name] = []
                                save_chats()
                                client_socket.send(f"SERVER: Chat '{chat_name}' creata con successo.".encode("utf-8"))

                                # Notifica tutti gli utenti online della nuova chat disponibile
                                notify_chat_change()
                            else:
                                client_socket.send(f"SERVER: Numero massimo di chat (5) raggiunto.".encode("utf-8"))

                    elif message == "/disconnect":
                        break

                # Messaggi normali
                elif current_chat:
                    broadcast_to_chat(current_chat, message.encode("utf-8"), sender_socket=client_socket)
                else:
                    # Se l'utente non è in nessuna chat, invia un messaggio di errore
                    client_socket.send("SERVER: Non sei in nessuna chat. Unisciti prima a una chat.".encode("utf-8"))

            except Exception as e:
                print(f"Errore nella gestione del client: {e}")
                break

    finally:
        # Rimuovi il client disconnesso da tutte le strutture dati
        if client_socket in clients:
            username = clients[client_socket]
            del clients[client_socket]

            if username in online_users:
                online_users.remove(username)

            # Rimuovi l'utente da tutte le chat
            for chat_name, users_list in chat_users.items():
                if username in users_list:
                    users_list.remove(username)
                    broadcast_to_chat(chat_name, f"SERVER: {username} è uscito dalla chat.".encode("utf-8"))

            # Rimuovi dalla mappatura user_chats
            if username in user_chats:
                del user_chats[username]

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