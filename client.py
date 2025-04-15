import socket
import threading
import dearpygui.dearpygui as dpg

HOST = '127.0.0.1'
PORT = 12345

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
username = ""

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
def connect_to_server():
    global username
    username = dpg.get_value("username_input")

    if username.strip() == "":

        return

    try:
        client_socket.connect((HOST, PORT))
        client_socket.send(f"NUOVO_UTENTE:{username}".encode("utf-8"))
    except:

        return

    dpg.hide_item("login_window")
    create_chat_window()
    dpg.show_item("chat_window")

    # Avvia il thread per ricevere messaggi
    receive_thread = threading.Thread(target=receive_messages, daemon=True)
    receive_thread.start()

# === CREA LA FINESTRA CHAT ===
def create_chat_window():
    with dpg.window(label="Chat di Gruppo", tag="chat_window", width=520, height=600, show=False):

        dpg.add_separator()
        dpg.add_spacing()

        with dpg.child_window(tag="chat_scroll", width=500, height=420):
            with dpg.group(tag="chat_content"):
                dpg.add_text("Connesso al server. Inizia a chattare!")

        with dpg.group(horizontal=True):
            dpg.add_input_text(tag="msg_input", hint="Scrivi un messaggio...", width=400,
                               on_enter=True, callback=submit_message)
            dpg.add_button(label="Invia", callback=submit_message)

# === GUI SETUP ===
dpg.create_context()

with dpg.window(label="Login", tag="login_window", width=300, height=200, no_close=True):
    dpg.add_text("Inserisci il tuo nome:")
    dpg.add_input_text(tag="username_input", hint="Il tuo nome")
    dpg.add_button(label="Connetti", callback=connect_to_server)
    dpg.add_text("", tag="error_text", color=(255, 0, 0))

dpg.create_viewport(title="Chat Client", width=540, height=640)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()