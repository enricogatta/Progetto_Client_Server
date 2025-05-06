# Analisi dettagliata del codice client chat Python
import socket                           # Importa il modulo socket per le comunicazioni di rete
import threading                        # Importa il modulo threading per gestire thread paralleli
import dearpygui.dearpygui as dpg       # Importa la libreria Dear PyGui per l'interfaccia grafica

# Sostituisci con l'indirizzo IP del computer che esegue il server
# HOST = '172.20.10.10'                 # Indirizzo IP commentato, probabilmente usato in precedenza
HOST = '192.168.78.184'                 # Indirizzo IP attuale del server, usato per la connessione
PORT = 12345                            # Porta utilizzata per la connessione al server

username = ""                           # Variabile globale per memorizzare il nome utente
# Dichiarazione globale per poterla ricreare quando necessario
client_socket = None                    # Socket client dichiarato globalmente
receive_thread = None                   # Thread di ricezione dichiarato globalmente
current_chat = ""                       # Variabile per tenere traccia della chat corrente


# === FUNZIONE DISCONNESSIONE ===
def disconnect(sender=None, app_data=None, user_data=None):  # Funzione per disconnettersi dal server
    global client_socket                # Accede alla variabile socket globale

    try:
        client_socket.send("/disconnect".encode("utf-8"))  # Invia comando di disconnessione al server
    except:
        pass                            # Ignora eventuali errori nella disconnessione

    # Chiudi la connessione
    try:
        client_socket.close()           # Chiude il socket di connessione
    except:
        pass                            # Ignora eventuali errori nella chiusura

    # Chiudi le finestre aperte
    if dpg.does_item_exist("chat_window"):     # Controlla se esiste la finestra chat
        dpg.delete_item("chat_window")         # Elimina la finestra di chat

    if dpg.does_item_exist("chat_selection_window"):  # Controlla se esiste la finestra di selezione chat
        dpg.delete_item("chat_selection_window")     # Elimina la finestra di selezione chat

    # Resetta l'errore e mostra la finestra di autenticazione
    dpg.set_value("error_text", "")     # Pulisce eventuali messaggi di errore
    dpg.show_item("auth_window")        # Mostra la finestra di login/registrazione


# === FUNZIONE ESCI DALLA CHAT ===
def exit_chat(sender=None, app_data=None, user_data=None):  # Funzione per uscire dalla chat corrente
    global current_chat                 # Accede alla variabile chat corrente globale

    if current_chat:                    # Verifica che l'utente sia in una chat
        try:
            # Invia il comando per lasciare la chat attuale
            client_socket.send(f"/leavechat:{current_chat}".encode("utf-8"))  # Informa il server
            current_chat = ""           # Resetta la variabile della chat corrente
        except:
            pass                        # Ignora eventuali errori nell'invio

    # Chiudi la finestra della chat
    if dpg.does_item_exist("chat_window"):    # Controlla se esiste la finestra chat
        dpg.delete_item("chat_window")        # Elimina la finestra di chat

    # Richiedi la lista aggiornata delle chat e mostra la finestra di selezione
    request_chat_list()                 # Richiede l'elenco aggiornato delle chat
    dpg.show_item("chat_selection_window")  # Mostra la finestra di selezione chat


# === FUNZIONE RICEZIONE MESSAGGI ===
def receive_messages():                 # Funzione eseguita in un thread separato per ricevere messaggi
    global client_socket                # Accede alla variabile socket globale
    while True:                         # Loop infinito per ricevere messaggi
        try:
            message = client_socket.recv(1024).decode("utf-8")  # Riceve fino a 1024 byte e decodifica
            if message.startswith("ERROR:"):   # Gestisce messaggi di errore dal server
                error_msg = message.split(":", 1)[1]  # Estrae il messaggio di errore
                dpg.set_value("error_text", error_msg)  # Visualizza l'errore nell'interfaccia
                return                  # Termina il thread di ricezione
            elif message.startswith("SUCCESS:"):  # Gestisce messaggi di successo (login/registrazione)
                global username         # Accede alla variabile username globale
                username = message.split(":", 1)[1]  # Estrae il nome utente confermato
                dpg.hide_item("auth_window")  # Nasconde la finestra di autenticazione
                create_chat_selection_window()  # Crea la finestra di selezione chat
                dpg.show_item("chat_selection_window")  # Mostra la finestra di selezione chat
            elif message.startswith("CHATLIST:"):  # Gestisce la ricezione dell'elenco chat
                # Formato: CHATLIST:chat1,chat2,chat3:true/false
                parts = message.split(":", 2)  # Divide il messaggio in parti
                chat_list = parts[1].split(",")  # Crea una lista delle chat disponibili

                # Controlla se l'ultimo elemento contiene info sulla possibilità di creare chat
                if len(parts) > 2:      # Se ci sono più di 2 parti nel messaggio
                    chat_creation_allowed = parts[2].lower() == "true"  # Imposta il flag di creazione chat

                update_chat_list(chat_list)  # Aggiorna la lista delle chat nell'interfaccia
            elif dpg.does_item_exist("chat_content"):  # Se esiste il contenitore della chat
                dpg.add_text(message, parent="chat_content", wrap=460)  # Aggiunge il messaggio ricevuto
                dpg.set_y_scroll("chat_scroll", 9999)  # Auto-scroll verso il basso
        except Exception as e:          # Gestisce eventuali errori di ricezione
            print(f"Errore durante la ricezione: {e}")  # Stampa l'errore sulla console
            if dpg.does_item_exist("chat_content"):  # Se esiste il contenitore della chat
                dpg.add_text("[ERRORE] Connessione persa", parent="chat_content", color=(255, 0, 0))  # Mostra errore
            break                       # Interrompe il ciclo di ricezione


# === INVIO MESSAGGIO ===
def submit_message(sender, app_data, user_data):  # Funzione per inviare messaggi
    global username, client_socket, current_chat  # Accede alle variabili globali
    message = dpg.get_value("msg_input").strip()  # Ottiene il testo dal campo di input e rimuove spazi
    if message:                         # Verifica che ci sia un messaggio da inviare
        if message.startswith("/"):     # Controlla se è un comando (inizia con /)
            # Gestione comandi
            if message == "/online":    # Comando per vedere gli utenti online
                try:
                    client_socket.send(message.encode("utf-8"))  # Invia il comando al server
                except:
                    dpg.add_text("[ERRORE] Connessione persa", parent="chat_content", color=(255, 0, 0))  # Mostra errore
            else:
                dpg.add_text("[SISTEMA] Comando non riconosciuto", parent="chat_content", color=(255, 255, 0))  # Comando sconosciuto
        else:
            full_msg = f"{username}: {message}"  # Formatta il messaggio con il nome utente
            try:
                client_socket.send(full_msg.encode("utf-8"))  # Invia il messaggio al server
                # Aggiungi il messaggio anche alla chat locale
                dpg.add_text(full_msg, parent="chat_content", wrap=460)  # Mostra il messaggio inviato
                dpg.set_y_scroll("chat_scroll", 9999)  # Auto-scroll verso il basso
            except:
                dpg.add_text("[ERRORE] Connessione persa", parent="chat_content", color=(255, 0, 0))  # Mostra errore
        dpg.set_value("msg_input", "")  # Pulisce il campo di input


# === LOGIN ===
def login():                           # Funzione per effettuare il login
    global username, client_socket, receive_thread  # Accede alle variabili globali
    username = dpg.get_value("username_input")  # Ottiene il nome utente inserito
    password = dpg.get_value("password_input")  # Ottiene la password inserita

    if username.strip() == "" or password.strip() == "":  # Verifica credenziali non vuote
        dpg.set_value("error_text", "Inserisci username e password validi.")  # Mostra errore
        return                         # Interrompe la funzione

    try:
        # Ricrea il socket ogni volta
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Crea un nuovo socket TCP/IP
        client_socket.connect((HOST, PORT))  # Si connette al server specificato

        # Avvia il thread per ricevere messaggi
        receive_thread = threading.Thread(target=receive_messages, daemon=True)  # Crea un thread daemon
        receive_thread.start()         # Avvia il thread di ricezione

        # Invia le credenziali
        client_socket.send(f"LOGIN:{username}:{password}".encode("utf-8"))  # Invia credenziali al server
    except Exception as e:             # Gestisce errori di connessione
        dpg.set_value("error_text", f"Connessione al server fallita: {e}")  # Mostra errore
        return                         # Interrompe la funzione


# === REGISTRAZIONE ===
def register():                        # Funzione per registrare un nuovo utente
    global username, client_socket, receive_thread  # Accede alle variabili globali
    username = dpg.get_value("username_input")  # Ottiene il nome utente inserito
    password = dpg.get_value("password_input")  # Ottiene la password inserita

    if username.strip() == "" or password.strip() == "":  # Verifica credenziali non vuote
        dpg.set_value("error_text", "Inserisci username e password validi.")  # Mostra errore
        return                          # Interrompe la funzione

    try:
        # Ricrea il socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Crea un nuovo socket TCP/IP
        client_socket.connect((HOST, PORT))  # Si connette al server specificato

        # Avvia il thread per ricevere messaggi
        receive_thread = threading.Thread(target=receive_messages, daemon=True)  # Crea un thread daemon
        receive_thread.start()          # Avvia il thread di ricezione

        # Invia le credenziali di registrazione
        client_socket.send(f"REGISTER:{username}:{password}".encode("utf-8"))  # Invia al server
    except Exception as e:              # Gestisce errori di connessione
        dpg.set_value("error_text", f"Connessione al server fallita: {e}")  # Mostra errore
        return                          # Interrompe la funzione


# === CREA FINESTRA SELEZIONE CHAT ===
def create_chat_selection_window():     # Funzione per creare la finestra di selezione chat
    with dpg.window(label=f"Selezione Chat - {username}", tag="chat_selection_window", width=400, height=350,
                    show=False):        # Crea una finestra con un titolo personalizzato
        dpg.add_text(f"Benvenuto, {username}!", color=(0, 150, 255))  # Aggiunge testo di benvenuto
        dpg.add_text("Seleziona una chat tra quelle disponibili:")  # Aggiunge testo informativo
        dpg.add_separator()            # Aggiunge una linea separatrice

        # Contenitore per la lista delle chat disponibili
        with dpg.group(tag="available_chats_list"):  # Crea un gruppo per contenere la lista
            # Qui verranno inserite dinamicamente le chat disponibili
            pass                        # Placeholder, le chat verranno aggiunte dinamicamente

        dpg.add_separator()            # Aggiunge una linea separatrice
        # Creazione nuova chat
        with dpg.group(tag="create_chat_group", horizontal=True):  # Gruppo orizzontale per creazione chat
            dpg.add_input_text(tag="new_chat_name", hint="Nome della nuova chat", width=250)  # Campo nome
            dpg.add_button(label="Crea", callback=create_new_chat, width=120)  # Pulsante per creare

        dpg.add_text("", tag="creation_status", color=(200, 200, 0))  # Testo per lo stato di creazione

        dpg.add_separator()            # Aggiunge una linea separatrice
        dpg.add_button(label="Disconnetti", callback=disconnect, width=380)  # Pulsante disconnessione

        # Messaggio di errore
        dpg.add_text("", tag="chat_selection_error", color=(255, 0, 0))  # Testo per messaggi di errore

        # Richiedi la lista aggiornata delle chat
        request_chat_list()            # Chiama la funzione per richiedere la lista di chat


# === FUNZIONE PER CREARE UNA NUOVA CHAT ===
def create_new_chat(sender=None, app_data=None, user_data=None):  # Funzione per creare una nuova chat
    chat_name = dpg.get_value("new_chat_name").strip()  # Ottiene e ripulisce il nome della chat
    if not chat_name:                  # Verifica che il nome non sia vuoto
        dpg.set_value("chat_selection_error", "Inserisci un nome valido per la chat")  # Mostra errore
        return                         # Interrompe la funzione

    try:
        client_socket.send(f"/createchat:{chat_name}".encode("utf-8"))  # Invia comando di creazione
        # Aggiorniamo la lista (la conferma arriverà dal server)
        request_chat_list()            # Richiede la lista aggiornata
    except:
        dpg.set_value("chat_selection_error", "Errore nella creazione della chat")  # Mostra errore


# === FUNZIONE PER ENTRARE IN UNA CHAT ===
def join_chat(chat_name):              # Funzione per entrare in una chat specifica
    global current_chat                # Accede alla variabile chat corrente globale
    current_chat = chat_name          # Aggiorna la chat corrente

    try:
        client_socket.send(f"/joinchat:{chat_name}".encode("utf-8"))  # Invia comando per unirsi

        # Nascondi la finestra di selezione
        dpg.hide_item("chat_selection_window")  # Nasconde finestra selezione

        # Crea la finestra della chat
        create_chat_window(chat_name)  # Crea la finestra della chat
        dpg.show_item("chat_window")   # Mostra la finestra della chat
    except Exception as e:             # Gestisce errori
        dpg.set_value("chat_selection_error", f"Errore nell'accesso alla chat: {e}")  # Mostra errore


# === AGGIORNA LISTA CHAT ===
def update_chat_list(chat_list):       # Funzione per aggiornare la lista delle chat disponibili
    # Pulisci la lista attuale
    if dpg.does_item_exist("available_chats_list"):  # Verifica che il contenitore esista
        dpg.delete_item("available_chats_list", children_only=True)  # Rimuove solo i figli

        # Aggiungi le chat dalla lista ricevuta
        for chat in chat_list:         # Itera attraverso la lista di chat
            if chat.strip():           # Ignora le stringhe vuote
                dpg.add_button(label=f"Entra in: {chat}", callback=lambda s, a, u: join_chat(u),
                               user_data=chat, parent="available_chats_list", width=380)  # Crea un pulsante per ogni chat


# === RICHIEDI LISTA CHAT ===
def request_chat_list():              # Funzione per richiedere la lista delle chat al server
    try:
        client_socket.send("/listchats".encode("utf-8"))  # Invia comando per ottenere la lista
    except:
        dpg.set_value("chat_selection_error", "Impossibile ottenere la lista delle chat")  # Mostra errore


# === CREA LA FINESTRA CHAT ===
def create_chat_window(chat_name):     # Funzione per creare la finestra della chat
    window_title = f"Chat: {chat_name} - {username}"  # Crea il titolo della finestra

    with dpg.window(label=window_title, tag="chat_window", width=520, height=600, show=False):  # Crea finestra
        # Header con informazioni utente e pulsanti
        with dpg.group(horizontal=True):  # Gruppo orizzontale per l'header
            dpg.add_text(f"Chat: {chat_name}", color=(0, 150, 255))  # Testo con nome chat
            dpg.add_spacer(width=140)  # Spazio per separare elementi
            dpg.add_button(label="Esci dalla Chat", callback=exit_chat, width=120)  # Pulsante uscita
            dpg.add_button(label="Disconnetti", callback=disconnect, width=100)  # Pulsante disconnessione

        # Informazioni sui comandi
        dpg.add_text("Comandi disponibili:")  # Testo informativo
        dpg.add_text("/online - Visualizza gli utenti online", color=(200, 200, 0))  # Descrizione comando
        dpg.add_separator()  # Linea separatrice
        dpg.add_spacing()    # Spazio aggiuntivo

        with dpg.child_window(tag="chat_scroll", width=500, height=380):  # Finestra scrollabile per messaggi
            with dpg.group(tag="chat_content"):  # Gruppo per contenere i messaggi
                dpg.add_text(f"Connesso alla chat '{chat_name}'. Inizia a chattare!", color=(0, 200, 0))  # Messaggio iniziale

        with dpg.group(horizontal=True):  # Gruppo orizzontale per l'input
            dpg.add_input_text(tag="msg_input", hint="Scrivi un messaggio...", width=400,
                               on_enter=True, callback=submit_message)  # Campo di input messaggi
            dpg.add_button(label="Invia", callback=submit_message)  # Pulsante di invio


# === GUI SETUP ===
dpg.create_context()                   # Inizializza il contesto di Dear PyGui

with dpg.window(label="Accesso", tag="auth_window", width=400, height=300, no_close=True):  # Finestra di login
    dpg.add_text("Inserisci le tue credenziali:")  # Testo informativo
    dpg.add_input_text(tag="username_input", label="Username", hint="Il tuo username", width=300)  # Campo username
    dpg.add_input_text(tag="password_input", label="Password", hint="La tua password", password=True, width=300)  # Campo password

    with dpg.group(horizontal=True):   # Gruppo orizzontale per i pulsanti
        dpg.add_button(label="Login", callback=login, width=150)  # Pulsante login
        dpg.add_button(label="Registrati", callback=register, width=150)  # Pulsante registrazione

    dpg.add_text("", tag="error_text", color=(255, 0, 0))  # Testo per errori
    dpg.add_separator()               # Linea separatrice
    dpg.add_text("Benvenuto nel servizio di chat! Registrati o effettua il login per iniziare.", wrap=380)  # Messaggio di benvenuto

dpg.create_viewport(title="Chat Client", width=540, height=640)  # Crea la finestra principale dell'applicazione
dpg.setup_dearpygui()                 # Configura la libreria grafica
dpg.show_viewport()                   # Mostra la finestra dell'applicazione
dpg.start_dearpygui()                 # Avvia il loop principale dell'interfaccia grafica
dpg.destroy_context()                 # Pulisce il contesto alla chiusura dell'applicazione