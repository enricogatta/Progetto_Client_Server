import socket
import threading
import dearpygui.dearpygui as dpg

# Sostituisci con l'indirizzo IP del computer che esegue il server
# Ad esempio: HOST = '192.168.1.X'
HOST = '127.0.0.1'  # Usa questo per test locali, cambia con l'IP del server per connessioni remote
PORT = 12345

username = ""
# Dichiarazione globale per poterla ricreare quando necessario
client_socket = None
receive_thread = None
current_chat = ""  # Per tenere traccia della chat corrente
chat_creation_allowed = True  # Flag per controllare se è possibile creare nuove chat


# === FUNZIONE DISCONNESSIONE ===
def disconnect(sender=None, app_data=None, user_data=None):
    global client_socket

    try:
        client_socket.send("/disconnect".encode("utf-8"))
    except:
        pass

    # Chiudi la connessione
    try:
        client_socket.close()
    except:
        pass

    # Chiudi le finestre aperte
    if dpg.does_item_exist("chat_window"):
        dpg.delete_item("chat_window")

    if dpg.does_item_exist("chat_selection_window"):
        dpg.delete_item("chat_selection_window")

    # Resetta l'errore e mostra la finestra di autenticazione
    dpg.set_value("error_text", "")
    dpg.show_item("auth_window")


# === FUNZIONE RICEZIONE MESSAGGI ===
def receive_messages():
    global client_socket, chat_creation_allowed
    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            if message.startswith("ERROR:"):
                error_msg = message.split(":", 1)[1]
                dpg.set_value("error_text", error_msg)
                return
            elif message.startswith("SUCCESS:"):
                global username
                username = message.split(":", 1)[1]
                dpg.hide_item("auth_window")
                create_chat_selection_window()
                dpg.show_item("chat_selection_window")
            elif message.startswith("CHATLIST:"):
                # Formato: CHATLIST:chat1,chat2,chat3:true/false
                parts = message.split(":", 2)
                chat_list = parts[1].split(",")

                # Controlla se l'ultimo elemento contiene info sulla possibilità di creare chat
                if len(parts) > 2:
                    chat_creation_allowed = parts[2].lower() == "true"

                update_chat_list(chat_list)
            elif dpg.does_item_exist("chat_content"):
                dpg.add_text(message, parent="chat_content", wrap=460)
                dpg.set_y_scroll("chat_scroll", 9999)
        except Exception as e:
            print(f"Errore durante la ricezione: {e}")
            if dpg.does_item_exist("chat_content"):
                dpg.add_text("[ERRORE] Connessione persa", parent="chat_content", color=(255, 0, 0))
            break


# === INVIO MESSAGGIO ===
def submit_message(sender, app_data, user_data):
    global username, client_socket, current_chat
    message = dpg.get_value("msg_input").strip()
    if message:
        if message.startswith("/"):
            # Gestione comandi
            if message == "/online":
                try:
                    client_socket.send(message.encode("utf-8"))
                except:
                    dpg.add_text("[ERRORE] Connessione persa", parent="chat_content", color=(255, 0, 0))
            elif message == "/back":
                # Torna alla selezione chat
                if dpg.does_item_exist("chat_window"):
                    dpg.delete_item("chat_window")
                create_chat_selection_window()
                dpg.show_item("chat_selection_window")
                # Informa il server che stiamo uscendo dalla chat corrente
                try:
                    client_socket.send(f"/leavechat:{current_chat}".encode("utf-8"))
                except:
                    pass
            else:
                dpg.add_text("[SISTEMA] Comando non riconosciuto", parent="chat_content", color=(255, 255, 0))
        else:
            full_msg = f"{username}: {message}"
            try:
                client_socket.send(full_msg.encode("utf-8"))
                # Aggiungi il messaggio anche alla chat locale
                dpg.add_text(full_msg, parent="chat_content", wrap=460)
                dpg.set_y_scroll("chat_scroll", 9999)
            except:
                dpg.add_text("[ERRORE] Connessione persa", parent="chat_content", color=(255, 0, 0))
        dpg.set_value("msg_input", "")


# === LOGIN ===
def login():
    global username, client_socket, receive_thread
    username = dpg.get_value("username_input")
    password = dpg.get_value("password_input")

    if username.strip() == "" or password.strip() == "":
        dpg.set_value("error_text", "Inserisci username e password validi.")
        return

    try:
        # Ricrea il socket ogni volta
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        # Avvia il thread per ricevere messaggi
        receive_thread = threading.Thread(target=receive_messages, daemon=True)
        receive_thread.start()

        # Invia le credenziali
        client_socket.send(f"LOGIN:{username}:{password}".encode("utf-8"))
    except Exception as e:
        dpg.set_value("error_text", f"Connessione al server fallita: {e}")
        return


# === REGISTRAZIONE ===
def register():
    global username, client_socket, receive_thread
    username = dpg.get_value("username_input")
    password = dpg.get_value("password_input")

    if username.strip() == "" or password.strip() == "":
        dpg.set_value("error_text", "Inserisci username e password validi.")
        return

    try:
        # Ricrea il socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        # Avvia il thread per ricevere messaggi
        receive_thread = threading.Thread(target=receive_messages, daemon=True)
        receive_thread.start()

        # Invia le credenziali di registrazione
        client_socket.send(f"REGISTER:{username}:{password}".encode("utf-8"))
    except Exception as e:
        dpg.set_value("error_text", f"Connessione al server fallita: {e}")
        return


# === CREA FINESTRA SELEZIONE CHAT ===
def create_chat_selection_window():
    with dpg.window(label=f"Selezione Chat - {username}", tag="chat_selection_window", width=400, height=350,
                    show=False):
        dpg.add_text(f"Benvenuto, {username}!", color=(0, 150, 255))
        dpg.add_text("Seleziona una chat tra quelle disponibili:")
        dpg.add_separator()

        # Contenitore per la lista delle chat disponibili
        with dpg.group(tag="available_chats_list"):
            # Qui verranno inserite dinamicamente le chat disponibili
            pass

        dpg.add_separator()
        # Creazione nuova chat
        with dpg.group(tag="create_chat_group", horizontal=True):
            dpg.add_input_text(tag="new_chat_name", hint="Nome della nuova chat", width=250)
            dpg.add_button(label="Crea", callback=create_new_chat, width=120)

        dpg.add_text("", tag="creation_status", color=(200, 200, 0))

        dpg.add_separator()
        dpg.add_button(label="Disconnetti", callback=disconnect, width=380)

        # Messaggio di errore
        dpg.add_text("", tag="chat_selection_error", color=(255, 0, 0))

        # Richiedi la lista aggiornata delle chat
        request_chat_list()


# === FUNZIONE PER CREARE UNA NUOVA CHAT ===
def create_new_chat(sender=None, app_data=None, user_data=None):
    global chat_creation_allowed

    if not chat_creation_allowed:
        dpg.set_value("chat_selection_error", "Numero massimo di chat (5) raggiunto")
        return

    chat_name = dpg.get_value("new_chat_name").strip()
    if not chat_name:
        dpg.set_value("chat_selection_error", "Inserisci un nome valido per la chat")
        return

    try:
        client_socket.send(f"/createchat:{chat_name}".encode("utf-8"))
        # Aggiorniamo la lista (la conferma arriverà dal server)
        request_chat_list()
    except:
        dpg.set_value("chat_selection_error", "Errore nella creazione della chat")


# === FUNZIONE PER ENTRARE IN UNA CHAT ===
def join_chat(chat_name):
    global current_chat
    current_chat = chat_name

    try:
        client_socket.send(f"/joinchat:{chat_name}".encode("utf-8"))

        # Nascondi la finestra di selezione
        dpg.hide_item("chat_selection_window")

        # Crea la finestra della chat
        create_chat_window(chat_name)
        dpg.show_item("chat_window")
    except Exception as e:
        dpg.set_value("chat_selection_error", f"Errore nell'accesso alla chat: {e}")


# === AGGIORNA LISTA CHAT ===
def update_chat_list(chat_list):
    global chat_creation_allowed

    # Pulisci la lista attuale
    if dpg.does_item_exist("available_chats_list"):
        dpg.delete_item("available_chats_list", children_only=True)

        # Aggiungi le chat dalla lista ricevuta
        for chat in chat_list:
            if chat.strip():  # Ignora le stringhe vuote
                dpg.add_button(label=f"Entra in: {chat}", callback=lambda s, a, u: join_chat(u),
                               user_data=chat, parent="available_chats_list", width=380)

    # Aggiorna lo stato della creazione chat
    if dpg.does_item_exist("creation_status"):
        if chat_creation_allowed:
            dpg.set_value("creation_status", "Puoi creare una nuova chat (massimo 5 chat totali)")
            if not dpg.is_item_shown("create_chat_group"):
                dpg.show_item("create_chat_group")
        else:
            dpg.set_value("creation_status", "Numero massimo di chat (5) raggiunto")
            if dpg.is_item_shown("create_chat_group"):
                dpg.hide_item("create_chat_group")


# === RICHIEDI LISTA CHAT ===
def request_chat_list():
    try:
        client_socket.send("/listchats".encode("utf-8"))
    except:
        dpg.set_value("chat_selection_error", "Impossibile ottenere la lista delle chat")


# === CREA LA FINESTRA CHAT ===
def create_chat_window(chat_name):
    window_title = f"Chat: {chat_name} - {username}"

    with dpg.window(label=window_title, tag="chat_window", width=520, height=600, show=False):
        # Header con informazioni utente e pulsanti
        with dpg.group(horizontal=True):
            dpg.add_text(f"Chat: {chat_name}", color=(0, 150, 255))
            dpg.add_spacer(width=120)
            dpg.add_button(label="Torna alle chat", callback=lambda: submit_message(None, None, "/back"), width=120)
            dpg.add_button(label="Disconnetti", callback=disconnect, width=100)

        # Informazioni sui comandi
        dpg.add_text("Comandi disponibili:")
        dpg.add_text("/online - Visualizza gli utenti online", color=(200, 200, 0))
        dpg.add_text("/back - Torna alla selezione chat", color=(200, 200, 0))
        dpg.add_separator()
        dpg.add_spacing()

        with dpg.child_window(tag="chat_scroll", width=500, height=380):
            with dpg.group(tag="chat_content"):
                dpg.add_text(f"Connesso alla chat '{chat_name}'. Inizia a chattare!", color=(0, 200, 0))

        with dpg.group(horizontal=True):
            dpg.add_input_text(tag="msg_input", hint="Scrivi un messaggio...", width=400,
                               on_enter=True, callback=submit_message)
            dpg.add_button(label="Invia", callback=submit_message)


# === GUI SETUP ===
dpg.create_context()

with dpg.window(label="Accesso", tag="auth_window", width=400, height=300, no_close=True):
    dpg.add_text("Inserisci le tue credenziali:")
    dpg.add_input_text(tag="username_input", label="Username", hint="Il tuo username", width=300)
    dpg.add_input_text(tag="password_input", label="Password", hint="La tua password", password=True, width=300)

    with dpg.group(horizontal=True):
        dpg.add_button(label="Login", callback=login, width=150)
        dpg.add_button(label="Registrati", callback=register, width=150)

    dpg.add_text("", tag="error_text", color=(255, 0, 0))
    dpg.add_separator()
    dpg.add_text("Benvenuto nel servizio di chat! Registrati o effettua il login per iniziare.", wrap=380)

dpg.create_viewport(title="Chat Client", width=540, height=640)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()