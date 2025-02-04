import os
import signal
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import time
import tkinter as tkt

DEFAULT_PORT = 5300
DEFAULT_TIMEOUT = 2
DEFAULT_BUFF = 1024
HOST=''
PORT=''

"""La funzione crea una finestra momentanea per inserire i dati della socket"""
def start_chat():
    global HOST, PORT
    finestra = tkt.Tk()
    finestra.title("WhatsChat")
    finestra.configure(bg='lightblue')

    def confirm_values():
        global HOST, PORT
        HOST = entry_host.get()
        PORT = entry_port.get()
        finestra.destroy()  # Chiude la finestra dopo aver confermato i valori

    label_host = tkt.Label(finestra, text="Inserire l'ip del Server host:", bg='lightblue', font=('Arial', 12))
    label_host.pack(pady=5)
    entry_host = tkt.Entry(finestra, font=('Arial', 12))
    entry_host.pack(pady=5)

    label_port = tkt.Label(finestra, text="Inserire la porta: (Default %i)" % DEFAULT_PORT, bg='lightblue', font=('Arial', 12))
    label_port.pack(pady=5)
    entry_port = tkt.Entry(finestra, font=('Arial', 12))
    entry_port.pack(pady=5)

    button_conferma = tkt.Button(finestra, text="Conferma", command=confirm_values, bg='blue', fg='white', font=('Arial', 12))
    button_conferma.pack(pady=10)

    finestra.mainloop()

    return HOST, PORT

"""La funzione fa avvenire la connesione tra client e server"""
def connect_with_timeout():
    global connection_successful
    connection_successful = False
    try:
        client_socket.connect(ADDR)
        connection_successful = True
    except Exception as e:
        print("Errore durante la connessione:", e)

"""La funzione che segue ha il compito di gestire la ricezione dei messaggi."""
def receive():
    while True:
        try:
            #quando viene chiamata la funzione receive, si mette in ascolto dei messaggi che
            #arrivano sul socket
            try:
                message = client_socket.recv(BUFSIZ)
            except Exception:
                message = bytes("{quit}", "utf8")
            #print(message.decode("utf8"))
            if message == bytes("{quit}", "utf8") or message == bytes("", "utf8"):
                print("La connessione con il server e' stata interrotta")
                os._exit(1)
            msg=message.decode("utf8")
            #visualizziamo l'elenco dei messaggi sullo schermo
            #e facciamo in modo che il cursore sia visibile al termine degli stessi
            msg_list.insert(tkt.END, msg)
            # Nel caso di errore e' probabile che il client abbia abbandonato la chat.
        except OSError or RuntimeError:  
            break

"""La funzione che segue gestisce l'invio dei messaggi."""
def send(event=None):
    # gli eventi vengono passati dai binders.
    msg = my_msg.get()
    # libera la casella di input.
    my_msg.set("")
    # invia il messaggio sul socket
    try:
        client_socket.send(bytes(msg, "utf8"))
    except Exception:
        msg = "{quit}"
    if msg == "{quit}":
        client_socket.close()
        frame.quit()

"""La funzione che segue viene invocata quando viene chiusa la finestra della chat."""
def on_closing(event=None):
    close()

def close(signum=None, frame=None):
    print("Uscendo dalla chat...")
    try:
        my_msg.set("{quit}")
        send()
    except NameError:
        os._exit(0)

#gestione del Cntrl + C
signal.signal(signal.SIGINT, close)

HOST, PORT = start_chat()

frame = tkt.Tk()
frame.title("WhatsChat")
frame.configure(bg='lightblue')

#creiamo il Frame per contenere i messaggi
messages_frame = tkt.Frame(frame, bg='lightblue')
#creiamo una variabile di tipo stringa per i messaggi da inviare.
my_msg = tkt.StringVar()
#creiamo una scrollbar per navigare tra i messaggi precedenti.
scrollbar = tkt.Scrollbar(messages_frame)

# La parte seguente contiene i messaggi.
msg_list = tkt.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set, font=('Arial', 12))
scrollbar.pack(side=tkt.RIGHT, fill=tkt.Y)
msg_list.pack(side=tkt.LEFT, fill=tkt.BOTH, pady=10)
msg_list.pack()
messages_frame.pack(pady=10)

#Creiamo il campo di input e lo associamo alla variabile stringa
entry_field = tkt.Entry(frame, textvariable=my_msg, font=('Arial', 12), bg='white', fg='black')
# leghiamo la funzione send al tasto Return
entry_field.bind("<Return>", send)

entry_field.pack(pady=5)
#creiamo il tasto invio e lo associamo alla funzione send
send_button = tkt.Button(frame, text="Invio", command=send, bg='blue', fg='white', font=('Arial', 12))
#integriamo il tasto nel pacchetto
send_button.pack(pady=5)

frame.protocol("WM_DELETE_WINDOW", on_closing)

#----Connessione al Server----

if HOST != '':
    if not PORT:
        PORT = DEFAULT_PORT
    else:
        PORT = int(PORT)

    BUFSIZ = DEFAULT_BUFF
    ADDR = (HOST, PORT)

    client_socket = socket(AF_INET, SOCK_STREAM)
    # Connessione con timeout
    connection_successful = False
    connection_thread = Thread(target=connect_with_timeout)
    connection_thread.start()
    connection_thread.join(timeout=DEFAULT_TIMEOUT)  # Attendi 2 secondi per la connessione
    if not connection_successful:
        print("Connessione non riuscita")
        os._exit(1)

    receive_thread = Thread(target=receive)
    receive_thread.start()
    # Avvia l'esecuzione della Finestra Chat.
    tkt.mainloop()
else:
    print("ip host non inserito")
os._exit(0)
