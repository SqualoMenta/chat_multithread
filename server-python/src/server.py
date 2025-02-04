import os
import signal
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import time

DEFAULT_PORT = 5300
MAX_CLIENTS = 5
DEFAULT_BUFF = 1024

""" La funzione che segue accetta le connessioni  dei client in entrata."""
def new_client_accept():
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s si è collegato." % client_address)
        client.send(bytes("CIAO! Digita il tuo Nome seguito dal tasto Invio!", "utf8"))
        addresses[client] = client_address
        Thread(target=client_handler, args=(client,)).start()

"""La funzione seguente gestisce la connessione di un singolo client."""
def client_handler(socket_client):
    try:
        message = socket_client.recv(BUFSIZ)
    except Exception:
            print("la connessione con %s:%s si e' interrotta" % addresses[socket_client])
            message = bytes("{quit}", "utf8")
    if message != bytes("{quit}", "utf8") and message != bytes("", "utf8"):
        name = message.decode("utf8")
        benvenuto = 'Benvenuto %s! Se vuoi lasciare la Chat, scrivi {quit} per uscire.' % name
        socket_client.send(bytes(benvenuto, "utf8"))
        msg = "%s si è unito all chat!" % name
        #a ogni client e' segnalato l'ingresso di un nuovo client
        broadcast(bytes(msg, "utf8"))
        clients[socket_client] = name
        
        #si mette in ascolto del thread del singolo client e ne gestisce l'invio dei messaggi o l'uscita dalla Chat
        while True:
            try:
                msg = socket_client.recv(BUFSIZ)
            except Exception:
                print("la connessione con %s:%s si e' interrotta" % addresses[socket_client])
                msg = bytes("{quit}", "utf8")
            #print(msg.decode("utf8"))
            if msg != bytes("{quit}", "utf8") and msg != bytes("", "utf8"):
                broadcast(msg, name + ": ")
            else:
                socket_client.close()
                del clients[socket_client]
                print("%s:%s si è scollegato." % addresses[socket_client])
                del addresses[socket_client]
                broadcast(bytes("%s ha abbandonato la Chat." % name, "utf8"))
                break
    else:
        #la prima cosa mandata dal client e' un {quit}
        socket_client.close()
        print("%s:%s si è scollegato." % addresses[socket_client])
        del addresses[socket_client]

""" La funzione, che segue, invia un messaggio in broadcast a tutti i client."""
def broadcast(msg, prefisso=""):
    for user in clients.copy():
        try:
            user.send(bytes(prefisso, "utf8")+msg)
        except BrokenPipeError:
            print("la connessione con %s:%s si e' interrotta" % addresses[user])
            user.close()
            del clients[user]

def close_server(signum, frame):
    #in caso di chiusura del server si invia un messaggio di disconnessione a tutti i client
    broadcast(bytes("{quit}", "utf8"))
    for client in clients:
        client.close()
        del clients[client]
    print("Terminazione del server...")
    os._exit(0)

#gestione Cntrl + c
signal.signal(signal.SIGINT, close_server)

clients = {}
addresses = {}

HOST = ''

port_input = input("Inserisci la porta del server (Default %i): " % DEFAULT_PORT)
if port_input:
    PORT = int(port_input)
else:
    PORT = DEFAULT_PORT

BUFSIZ = DEFAULT_BUFF
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)

SERVER.listen(MAX_CLIENTS)
print("In attesa di connessioni...")
ACCEPT_THREAD = Thread(target=new_client_accept)
ACCEPT_THREAD.start()
ACCEPT_THREAD.join()
SERVER.close()
