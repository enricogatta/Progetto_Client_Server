import socket              # Importa il modulo per la comunicazione di rete
import threading           # Importa il modulo per gestire thread paralleli
import json                # Importa il modulo per la gestione di dati JSON
import os                  # Importa il modulo per operazioni sul sistema operativo
import hashlib             # Importa il modulo per funzioni crittografiche di hash

HOST = '0.0.0.0'           # Indirizzo server: '0.0.0.0' accetta connessioni da qualsiasi interfaccia di rete
PORT = 12345               # Porta su cui il server sarà in ascolto

# Definizione dei file per memorizzare dati persistenti
USERS_FILE = "users.json"  # File per memorizzare i dati degli utenti registrati
CHATS_FILE = "chats.json"  # File per memorizzare i dati delle chat

# Inizializzazione del socket TCP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Crea un socket TCP/IP
server.bind((HOST, PORT))  # Associa il socket all'indirizzo e porta specificati
server.listen()            # Mette il socket in modalità ascolto per connessioni in arrivo

# Strutture dati per gestire le connessioni e le chat
clients = {}               # Dizionario che associa socket dei client ai loro username
online_users = []          # Lista degli utenti attualmente connessi
user_chats = {}            # Dizionario che associa username alla chat attualmente attiva
chat_users = {"principale": []}  # Dizionario che associa nome chat agli utenti al suo interno
available_chats = ["principale"]  # Lista delle chat disponibili (all'inizio solo quella principale)


# Funzione per caricare gli utenti dal file o creare un file nuovo se non esiste
def load_users():
    if os.path.exists(USERS_FILE):  # Verifica se il file degli utenti esiste
        try:
            with open(USERS_FILE, 'r') as f:  # Apre il file in modalità lettura
                return json.load(f)  # Carica il JSON e lo converte in dizionario Python
        except json.JSONDecodeError:  # Gestisce errori di decodifica JSON
            print("Errore nel file utenti. Creazione di un nuovo file.")
            return {}  # Restituisce un dizionario vuoto in caso di errore
    else:
        return {}  # Restituisce un dizionario vuoto se il file non esiste


# Funzione per salvare gli utenti nel file
def save_users(users):
    with open(USERS_FILE, 'w') as f:  # Apre il file in modalità scrittura
        json.dump(users, f)  # Converte il dizionario in JSON e lo salva nel file


# Funzione per salvare i dati delle chat nel file
def save_chats():
    with open(CHATS_FILE, 'w') as f:  # Apre il file in modalità scrittura
        chat_data = {  # Crea un dizionario con i dati delle chat
            "chat_users": chat_users,  # Associazioni tra chat e utenti
            "available_chats": available_chats  # Lista delle chat disponibili
        }
        json.dump(chat_data, f)  # Converte il dizionario in JSON e lo salva nel file


# Funzione per generare l'hash della password per maggiore sicurezza
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()  # Codifica la password in SHA-256


# Carica i dati degli utenti all'avvio del server
users = load_users()


# Funzione per inviare un messaggio solo agli utenti in una specifica chat
def broadcast_to_chat(chat_name, message, sender_socket=None):
    usernames_in_chat = chat_users.get(chat_name, [])  # Ottiene la lista degli utenti nella chat
    for client_socket, username in clients.items():  # Itera su tutti i client connessi
        if client_socket != sender_socket and username in usernames_in_chat:  # Escludi il mittente e verifica appartenenza alla chat
            try:
                client_socket.send(message)  # Invia il messaggio al client
            except:
                # Errori di invio sono gestiti dalla funzione handle_client quando il client è disconnesso
                pass


# Funzione per notificare a tutti gli utenti online della disponibilità di una nuova chat
def notify_chat_change():
    chat_list = ",".join(available_chats)  # Crea una stringa con tutte le chat separate da virgole
    update_message = f"CHATLIST:{chat_list}".encode("utf-8")  # Formatta e codifica il messaggio

    for client_socket in clients:  # Itera su tutti i client connessi
        try:
            client_socket.send(update_message)  # Invia l'aggiornamento al client
        except:
            # Errori di invio sono gestiti altrove
            pass


# Funzione per inviare un messaggio a tutti gli utenti connessi
def broadcast(message, sender_socket=None):
    for client_socket in clients:  # Itera su tutti i client connessi
        if client_socket != sender_socket:  # Esclude il mittente
            try:
                client_socket.send(message)  # Invia il messaggio al client
            except:
                # Errori di invio sono gestiti dalla funzione handle_client
                pass


# Funzione per inviare la lista degli utenti online a un client specifico
def send_online_users(client_socket):
    users_list = ", ".join(online_users)  # Crea una stringa con tutti gli utenti separati da virgole
    client_socket.send(f"SERVER: Utenti online: {users_list}".encode("utf-8"))  # Invia la lista


# Funzione per inviare la lista delle chat disponibili a un client specifico
def send_chat_list(client_socket):
    chat_creation_allowed = len(available_chats) < 5  # Verifica se è possibile creare nuove chat (max 5)
    chats_list = ",".join(available_chats)  # Crea una stringa con tutte le chat separate da virgole
    client_socket.send(f"CHATLIST:{chats_list}:{chat_creation_allowed}".encode("utf-8"))  # Invia la lista


# Funzione principale per gestire le comunicazioni con un client autenticato
def handle_client(client_socket, username):
    try:
        # Inizialmente l'utente non è in nessuna chat
        current_chat = None

        # Invia la lista delle chat disponibili al client appena connesso
        send_chat_list(client_socket)

        while True:
            try:
                message = client_socket.recv(1024).decode("utf-8")  # Riceve e decodifica il messaggio
                if not message:  # Se il client si disconnette
                    break

                # Gestione comandi speciali (iniziano con "/")
                if message.startswith("/"):
                    if message == "/online":  # Comando per vedere gli utenti online
                        send_online_users(client_socket)
                    elif message == "/listchats":  # Comando per vedere le chat disponibili
                        send_chat_list(client_socket)
                    elif message.startswith("/joinchat:"):  # Comando per entrare in una chat
                        chat_name = message.split(":", 1)[1]  # Estrae il nome della chat
                        if chat_name in available_chats:  # Verifica se la chat esiste
                            # Rimuovi l'utente dalla chat corrente se esiste
                            if current_chat and username in chat_users.get(current_chat, []):
                                chat_users[current_chat].remove(username)
                                broadcast_to_chat(current_chat,
                                                  f"SERVER: {username} è uscito dalla chat.".encode("utf-8"))

                            # Aggiungi l'utente alla nuova chat
                            if chat_name not in chat_users:
                                chat_users[chat_name] = []

                            chat_users[chat_name].append(username)  # Aggiunge l'utente alla chat
                            user_chats[username] = chat_name  # Aggiorna la chat corrente dell'utente
                            current_chat = chat_name  # Aggiorna la chat corrente nel contesto della funzione

                            # Notifica nella chat che un nuovo utente è entrato
                            broadcast_to_chat(chat_name,
                                              f"SERVER: {username} è entrato nella chat.".encode("utf-8"))

                            # Invia lista utenti nella chat al client
                            chat_users_list = ", ".join(chat_users.get(chat_name, []))
                            client_socket.send(
                                f"SERVER: Utenti nella chat '{chat_name}': {chat_users_list}".encode("utf-8"))
                        else:
                            client_socket.send(f"SERVER: La chat '{chat_name}' non esiste.".encode("utf-8"))

                    elif message.startswith("/leavechat:"):  # Comando per uscire da una chat
                        chat_name = message.split(":", 1)[1]  # Estrae il nome della chat
                        if current_chat == chat_name and username in chat_users.get(chat_name, []):
                            # Rimuovi l'utente dalla chat
                            chat_users[chat_name].remove(username)
                            broadcast_to_chat(chat_name,
                                              f"SERVER: {username} è uscito dalla chat.".encode("utf-8"))

                            # Aggiorna lo stato dell'utente
                            if username in user_chats:
                                del user_chats[username]  # Rimuove l'associazione utente-chat
                            current_chat = None  # Azzera la chat corrente

                            # Invia la lista delle chat disponibili
                            send_chat_list(client_socket)
                        else:
                            client_socket.send(f"SERVER: Non sei nella chat '{chat_name}'.".encode("utf-8"))

                    elif message.startswith("/createchat:"):  # Comando per creare una nuova chat
                        chat_name = message.split(":", 1)[1]  # Estrae il nome della chat
                        if chat_name in available_chats:  # Verifica se la chat esiste già
                            client_socket.send(f"SERVER: La chat '{chat_name}' esiste già.".encode("utf-8"))
                        elif len(available_chats) >= 5:  # Verifica il limite massimo di chat
                            client_socket.send(f"SERVER: Numero massimo di chat (5) raggiunto.".encode("utf-8"))
                        else:
                            available_chats.append(chat_name)  # Aggiunge la nuova chat
                            chat_users[chat_name] = []  # Inizializza la lista degli utenti
                            save_chats()  # Salva le modifiche nel file
                            client_socket.send(f"SERVER: Chat '{chat_name}' creata con successo.".encode("utf-8"))
                            # Notifica tutti gli utenti online della nuova chat disponibile
                            notify_chat_change()

                    elif message == "/disconnect":  # Comando per disconnettersi
                        break

                # Gestione messaggi normali (non comandi)
                elif current_chat:  # Se l'utente è in una chat
                    broadcast_to_chat(current_chat, message.encode("utf-8"), sender_socket=client_socket)
                else:
                    # Se l'utente non è in nessuna chat, invia un messaggio di errore
                    client_socket.send("SERVER: Non sei in nessuna chat. Unisciti prima a una chat.".encode("utf-8"))

            except Exception as e:
                print(f"Errore nella gestione del client: {e}")
                break

    finally:
        # Blocco di pulizia eseguito quando il client si disconnette o c'è un errore
        # Rimuovi il client disconnesso da tutte le strutture dati
        if client_socket in clients:
            username = clients[client_socket]
            del clients[client_socket]  # Rimuove il client dalla lista dei connessi

            if username in online_users:
                online_users.remove(username)  # Rimuove l'utente dalla lista degli online

            # Rimuovi l'utente da tutte le chat
            for chat_name, users_list in chat_users.items():
                if username in users_list:
                    users_list.remove(username)
                    broadcast_to_chat(chat_name, f"SERVER: {username} è uscito dalla chat.".encode("utf-8"))

            # Rimuovi dalla mappatura user_chats
            if username in user_chats:
                del user_chats[username]  # Rimuove l'associazione utente-chat

        try:
            client_socket.close()  # Chiude il socket del client
        except:
            pass  # Ignora errori durante la chiusura

        print(f"Cliente {username} disconnesso")  # Notifica nel log del server


# Funzione per gestire l'autenticazione dei client
def handle_auth(client_socket, address):
    print(f"Gestione autenticazione per {address}")
    try:
        while True:
            try:
                auth_data = client_socket.recv(1024).decode("utf-8")  # Riceve i dati di autenticazione
                if not auth_data:  # Se il client si disconnette durante l'autenticazione
                    print(f"Client {address} disconnesso durante l'autenticazione")
                    client_socket.close()
                    return

                print(f"Ricevuto da {address}: {auth_data}")

                # Formato atteso: ACTION:username:password
                parts = auth_data.split(":", 2)  # Divide la stringa in tre parti
                if len(parts) != 3:  # Verifica che il formato sia corretto
                    client_socket.send("ERROR:Formato non valido".encode("utf-8"))
                    continue

                action, username, password = parts  # Estrae azione, username e password

                if action == "LOGIN":  # Gestione login
                    if username in users and users[username] == hash_password(password):  # Verifica credenziali
                        if username in online_users:  # Verifica se l'utente è già connesso
                            client_socket.send("ERROR:Utente già connesso".encode("utf-8"))
                        else:
                            client_socket.send(f"SUCCESS:{username}".encode("utf-8"))
                            clients[client_socket] = username  # Associa il socket all'username
                            online_users.append(username)  # Aggiunge l'utente alla lista online
                            print(f"Utente {username} connesso")
                            # Avvia il thread per gestire i messaggi del client
                            threading.Thread(target=handle_client, args=(client_socket, username)).start()
                            return  # Esce dalla funzione di autenticazione
                    else:
                        client_socket.send("ERROR:Username o password non validi".encode("utf-8"))

                elif action == "REGISTER":  # Gestione registrazione
                    if username in users:  # Verifica se l'username esiste già
                        client_socket.send("ERROR:Username già esistente".encode("utf-8"))
                    else:
                        users[username] = hash_password(password)  # Salva l'hash della password
                        save_users(users)  # Salva gli utenti nel file
                        client_socket.send(f"SUCCESS:{username}".encode("utf-8"))
                        clients[client_socket] = username  # Associa il socket all'username
                        online_users.append(username)  # Aggiunge l'utente alla lista online
                        print(f"Nuovo utente registrato: {username}")
                        # Avvia il thread per gestire i messaggi del client
                        threading.Thread(target=handle_client, args=(client_socket, username)).start()
                        return  # Esce dalla funzione di autenticazione
                else:
                    client_socket.send("ERROR:Azione non valida".encode("utf-8"))

            except Exception as e:
                print(f"Errore durante l'autenticazione: {e}")
                client_socket.close()
                return
    except Exception as e:
        print(f"Errore critico durante l'autenticazione: {e}")
        try:
            client_socket.close()  # Chiude il socket in caso di errore
        except:
            pass


# Funzione principale per ricevere e gestire le connessioni in arrivo
def receive_connections():
    print(f"Server in ascolto su {HOST}:{PORT}")
    try:
        while True:
            client_socket, address = server.accept()  # Accetta una nuova connessione
            print(f"Connesso con {address}")
            # Avvia un thread per gestire l'autenticazione del client
            threading.Thread(target=handle_auth, args=(client_socket, address)).start()
    except KeyboardInterrupt:  # Gestisce l'interruzione da tastiera (Ctrl+C)
        print("Server interrotto")
    except Exception as e:
        print(f"Errore durante l'accettazione delle connessioni: {e}")
    finally:
        server.close()  # Chiude il socket del server
        print("Server chiuso")


# Punto di ingresso del programma
if __name__ == "__main__":
    print("Avvio del server...")
    try:
        receive_connections()  # Avvia la funzione principale
    except Exception as e:
        print(f"Errore fatale: {e}")  # Gestisce errori non previsti