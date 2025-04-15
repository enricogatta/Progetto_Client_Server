import socket
import threading
import dearpygui.dearpygui as dpg

HOST = '127.0.0.1'
PORT = 12345

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
username = ""
# Dichiarazione globale per poterla ricreare quando necessario
client_socket = None
receive_thread = None

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
    # Chiudi la finestra chat e torna al login
    if dpg.does_item_exist("chat_window"):
        dpg.delete_item("chat_window")
    # Resetta l'errore e mostra la finestra di autenticazione
    dpg.set_value("error_text", "")
    dpg.show_item("auth_window")


# === FUNZIONE RICEZIONE MESSAGGI ===
def receive_messages():
    global client_socket
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
                create_chat_window()
                dpg.show_item("chat_window")
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
    global username,client_socket
    message = dpg.get_value("msg_input").strip()

    if message:
        if message.startswith("/"):
            # Gestione comandi
            if message == "/online":
                try:
                    client_socket.send(message.encode("utf-8"))
                except:
                    dpg.add_text("[ERRORE] Connessione persa", parent="chat_content", color=(255, 0, 0))
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


# === CREA LA FINESTRA CHAT ===
def create_chat_window():
    with dpg.window(label=f"Chat di Gruppo - {username}", tag="chat_window", width=520, height=600, show=False):
        # Header con informazioni utente e pulsante disconnessione
        with dpg.group(horizontal=True):
            dpg.add_text(f"Benvenuto, {username}!", color=(0, 150, 255))
            dpg.add_spacer(width=150)
            dpg.add_button(label="Disconnetti", callback=disconnect, width=120)

        # Informazioni sui comandi
        dpg.add_text("Comandi disponibili:")
        dpg.add_text("/online - Visualizza gli utenti online", color=(200, 200, 0))
        dpg.add_separator()
        dpg.add_spacing()

        with dpg.child_window(tag="chat_scroll", width=500,
                              height=380):  # Ridotto leggermente per dare spazio all'header
            with dpg.group(tag="chat_content"):
                dpg.add_text("Connesso al server. Inizia a chattare!", color=(0, 200, 0))

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