# Applicazione di Chat Python Socket

Un'applicazione di chat client-server costruita in Python che permette a più utenti di comunicare in diverse stanze di chat. L'applicazione presenta un'interfaccia grafica per i client costruita con DearPyGui.

# Applicazione di Chat Python Socket
Un'applicazione di chat client-server costruita in Python che permette a più utenti di comunicare in diverse stanze di chat. L'applicazione presenta un'interfaccia grafica per i client costruita con DearPyGui.


## Funzionalità

- **Autenticazione Utente**: Sistema di registrazione e login con hash delle password per la sicurezza
- **Multiple Stanze di Chat**: Gli utenti possono creare e unirsi a diverse stanze di chat
- **Messaggistica in Tempo Reale**: Consegna istantanea dei messaggi tra gli utenti
- **Sistema di Comandi**: Comandi speciali come `/online` per vedere chi è connesso
- **GUI Moderna**: Interfaccia grafica facile da usare costruita con DearPyGui
- **Multipiattaforma**: Funziona su Windows, macOS e Linux

## Requisiti

- Python 3.6+
- Libreria DearPyGui
- Libreria Socket (inclusa nella libreria standard di Python)
- Libreria Threading (inclusa nella libreria standard di Python)
- Libreria JSON (inclusa nella libreria standard di Python)

## Installazione

1. Clona questo repository:
   ```
   git clone https://github.com/tuousername/python-socket-chat.git
   cd python-socket-chat
   ```

2. Installa le dipendenze richieste:
   ```
   pip install dearpygui
   ```

## Utilizzo

### Avvio del server

1. Avvia prima il server:
   ```
   python server.py
   ```
   Il server inizierà ad ascoltare le connessioni sulla porta 12345.

2. Di default, il server si collega a 0.0.0.0, che accetta connessioni da qualsiasi interfaccia di rete.

### Avvio del client

1. Apri il file client.py e aggiorna la variabile HOST con l'indirizzo IP del tuo server:
   ```python
   # Cambia questo con l'indirizzo IP del tuo server
   HOST = '192.168.78.15'  # Sostituisci con l'IP del tuo server
   ```

2. Esegui il client:
   ```
   python client.py
   ```

3. Registra un nuovo account o accedi con credenziali esistenti.

4. Seleziona una stanza di chat da unire o creane una nuova.

### Comandi del Client

Mentre sei in una chat, puoi usare questi comandi:
- `/online`: Visualizza tutti gli utenti attualmente online
- `/disconnect`: Disconnettiti dal server
- Altre funzioni standard sono disponibili attraverso i pulsanti dell'interfaccia grafica

## Struttura dell'Applicazione

- **server.py**: Il componente server che gestisce connessioni, autenticazione e instradamento dei messaggi
- **client.py**: L'applicazione client con GUI che consente agli utenti di interagire con il sistema di chat
- **users.json**: Memorizza le credenziali degli utenti (creato automaticamente dal server)
- **chats.json**: Memorizza informazioni sulle stanze di chat disponibili (creato automaticamente dal server)

## Limitazioni del Server

- Il server consente un massimo di 5 stanze di chat in qualsiasi momento
- Quando viene raggiunto il limite, le stanze di chat vuote possono essere sostituite con nuove

## Note sulla Sicurezza

- Le password vengono sottoposte a hash utilizzando SHA-256 prima di essere memorizzate
- L'applicazione è progettata per l'uso in rete locale e non implementa la crittografia per i messaggi trasmessi
- Per la distribuzione su Internet, sarebbero raccomandate misure di sicurezza aggiuntive

## Miglioramenti Futuri

- Crittografia end-to-end per i messaggi
- Messaggistica privata tra utenti
- Funzionalità di condivisione file
- Profili utente personalizzabili
- Persistenza della cronologia dei messaggi


## Ringraziamenti

- Costruito con [DearPyGui](https://github.com/hoffstadt/DearPyGui)

## Funzionalità

- **Autenticazione Utente**: Sistema di registrazione e login con hash delle password per la sicurezza
- **Multiple Stanze di Chat**: Gli utenti possono creare e unirsi a diverse stanze di chat
- **Messaggistica in Tempo Reale**: Consegna istantanea dei messaggi tra gli utenti
- **Sistema di Comandi**: Comandi speciali come `/online` per vedere chi è connesso
- **GUI Moderna**: Interfaccia grafica facile da usare costruita con DearPyGui
- **Multipiattaforma**: Funziona su Windows, macOS e Linux

## Requisiti

- Python 3.6+
- Libreria DearPyGui
- Libreria Socket (inclusa nella libreria standard di Python)
- Libreria Threading (inclusa nella libreria standard di Python)
- Libreria JSON (inclusa nella libreria standard di Python)

## Installazione

1. Clona questo repository:
   ```
   git clone https://github.com/tuousername/python-socket-chat.git
   cd python-socket-chat
   ```

2. Installa le dipendenze richieste:
   ```
   pip install dearpygui
   ```

## Utilizzo

### Avvio del server

1. Avvia prima il server:
   ```
   python server.py
   ```
   Il server inizierà ad ascoltare le connessioni sulla porta 12345.

2. Di default, il server si collega a 0.0.0.0, che accetta connessioni da qualsiasi interfaccia di rete.

### Avvio del client

1. Apri il file client.py e aggiorna la variabile HOST con l'indirizzo IP del tuo server:
   ```python
   # Cambia questo con l'indirizzo IP del tuo server
   HOST = '192.168.78.15'  # Sostituisci con l'IP del tuo server
   ```

2. Esegui il client:
   ```
   python client.py
   ```

3. Registra un nuovo account o accedi con credenziali esistenti.

4. Seleziona una stanza di chat da unire o creane una nuova.

### Comandi del Client

Mentre sei in una chat, puoi usare questi comandi:
- `/online`: Visualizza tutti gli utenti attualmente online
- `/disconnect`: Disconnettiti dal server
- Altre funzioni standard sono disponibili attraverso i pulsanti dell'interfaccia grafica

## Struttura dell'Applicazione

- **server.py**: Il componente server che gestisce connessioni, autenticazione e instradamento dei messaggi
- **client.py**: L'applicazione client con GUI che consente agli utenti di interagire con il sistema di chat
- **users.json**: Memorizza le credenziali degli utenti (creato automaticamente dal server)
- **chats.json**: Memorizza informazioni sulle stanze di chat disponibili (creato automaticamente dal server)

## Limitazioni del Server

- Il server consente un massimo di 5 stanze di chat in qualsiasi momento
- Quando viene raggiunto il limite, le stanze di chat vuote possono essere sostituite con nuove

## Note sulla Sicurezza

- Le password vengono sottoposte a hash utilizzando SHA-256 prima di essere memorizzate
- L'applicazione è progettata per l'uso in rete locale e non implementa la crittografia per i messaggi trasmessi
- Per la distribuzione su Internet, sarebbero raccomandate misure di sicurezza aggiuntive

## Miglioramenti Futuri

- Messaggistica privata tra utenti
- Funzionalità di condivisione file
- Profili utente personalizzabili
- Persistenza della cronologia dei messaggi

## Ringraziamenti

- Costruito con [DearPyGui](https://github.com/hoffstadt/DearPyGui)
- Ispirato ai classici sistemi di chat IRC
