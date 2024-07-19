use std::{
    collections::HashMap,
    io::{self, Read, Write},
    net::{TcpListener, TcpStream},
    str,
    sync::{Arc, Mutex},
    thread::{self, sleep},
    time::Duration,
};

const DEFAULT_HOST: &str = "127.0.0.1";
const DEFAULT_PORT: u16 = 5300;
const DEFAULT_BUF_SIZE: usize = 1024;

#[derive(Debug)]
enum ConnectionError {
    BadFormat,
    NameRefused,
    NameAlreadyTaken,
}

fn new_client_accept(
    listener: TcpListener,
    connections: Arc<Mutex<HashMap<String, Arc<Mutex<TcpStream>>>>>,
) {
    for stream in listener.incoming() {
        match stream {
            Ok(mut stream) => {
                println!("{stream:?} has connected");
                stream
                    .set_write_timeout(Some(Duration::from_secs(2)))
                    .unwrap();
                stream
                    .write_all("CIAO! Digita il tuo Nome seguito dal tasto Invio!".as_bytes())
                    .unwrap();
                let connections_clone = Arc::clone(&connections);
                thread::spawn(move || client_handler(stream, connections_clone));
            }
            Err(e) => {
                eprintln!("couldn't get client: {e:?}");
            }
        }
    }
}

fn client_handler(
    mut stream: TcpStream,
    connections: Arc<Mutex<HashMap<String, Arc<Mutex<TcpStream>>>>>,
) {
    let mut buffer = [0; DEFAULT_BUF_SIZE];
    let len = match stream.read(&mut buffer[..]) {
        Ok(usize) => usize,
        Err(e) => {
            eprintln!("{:?}, {e}", ConnectionError::BadFormat);
            return;
        }
    };
    if len > 0 && len < DEFAULT_BUF_SIZE {
        let valid_length = buffer.iter().position(|&x| x == 0).unwrap_or(len);
        let name = &buffer[0..valid_length];
        let name = str::from_utf8(name).unwrap();
        if connections.lock().unwrap().contains_key(&name.to_string()) {
            eprintln!("{:?}", ConnectionError::NameAlreadyTaken);
            return;
        }
        stream
            .write_all(format!("Benvenuto {name}").as_bytes())
            .unwrap();
        let message = format!("{name} si è unito alla chat");
        broadcast(message, Arc::clone(&connections));
        stream
            .set_read_timeout(Some(Duration::from_millis(10)))
            .unwrap();
        let mut map = connections.lock().unwrap();
        let astream = Arc::new(Mutex::new(stream));
        map.insert(name.to_string(), Arc::clone(&astream));
        drop(map);
        loop {
            let mut buffer = [0; DEFAULT_BUF_SIZE];
            let mut strm = astream.lock().unwrap();
            let len = match strm.read(&mut buffer[..]) {
                Ok(len) => len,
                Err(ref e) if e.kind() == io::ErrorKind::TimedOut => {
                    drop(strm); // Release the lock to update messages
                    sleep(Duration::from_millis(100));
                    continue;
                }
                Err(_) => {
                    eprintln!("{:?}", ConnectionError::BadFormat); //Could also mean somebodi left
                    drop(strm); // Release the lock
                    let msg = format!("{name} left the chat");
                    println!("{msg}");
                    connections.lock().unwrap().remove(name);
                    broadcast(msg, Arc::clone(&connections));
                    break;
                }
            };
            drop(strm);
            if len > 0 && len < DEFAULT_BUF_SIZE {
                let valid_length = buffer.iter().position(|&x| x == 0).unwrap_or(len);
                let scritte = &buffer[0..valid_length];
                let scritte = str::from_utf8(scritte).unwrap();
                let message = format!("{name}: {scritte}");
                broadcast(message, Arc::clone(&connections));
            } else {
                let msg = format!("{name} left the chat");
                println!("{msg}");
                connections.lock().unwrap().remove(name);
                broadcast(msg, Arc::clone(&connections));
                break;
            }
        }
    } else {
        eprintln!("{:?}", ConnectionError::NameRefused);
    }
}

fn broadcast(msg: String, connections: Arc<Mutex<HashMap<String, Arc<Mutex<TcpStream>>>>>) {
    let guard = connections.lock().unwrap();
    for el in guard.values() {
        let mut cn = el.lock().unwrap();
        cn.write_all(msg.as_bytes()).unwrap();
    }
}

fn main() {
    let host = get_host();
    let port = get_port();
    let listener = server_bind(&host[..], port);
    let map = Arc::new(Mutex::new(HashMap::new()));

    println!("Server is running on {:?}", listener.local_addr().unwrap());

    new_client_accept(listener, map);
}

fn server_bind(host: &str, port: u16) -> TcpListener {
    TcpListener::bind(format!("{host}:{port}")).unwrap_or_else(|err| {
        eprintln!("Failed to bind to {host}:{port} due to: {err}");
        eprintln!("Attempting to bind to default address {DEFAULT_HOST}:{DEFAULT_PORT}");

        TcpListener::bind(format!("{DEFAULT_HOST}:{DEFAULT_PORT}")).unwrap_or_else(|default_err| {
            panic!("Failed to bind to default address {DEFAULT_HOST}:{DEFAULT_PORT} due to: {default_err}");
        })
    })
}

fn get_host() -> String {
    println!("Please input host.");

    let mut host = String::new();

    io::stdin().read_line(&mut host).unwrap_or_else(|err| {
        eprint!("Failed to read due to: {err}");
        host = DEFAULT_HOST.to_string();
        1
    });

    let host = if host.trim().is_empty() {
        DEFAULT_HOST
    } else {
        host.trim()
    };

    println!("Selected Host is: {host}");

    host.to_string()
}

fn get_port() -> u16 {
    println!("Please input port.");

    let mut port = String::new();
    io::stdin().read_line(&mut port).unwrap_or_else(|err| {
        eprint!("Failed to read port due to: {err}");
        port = DEFAULT_PORT.to_string();
        1
    });

    let port: u16 = port.trim().parse().unwrap_or_else(|err| {
        eprint!("Failed to parse port due to: {err}");
        DEFAULT_PORT
    });

    println!("Selected Port is: {port}");

    port
}
