use std::{io, net::TcpListener};

const DEFAULT_HOST: &str = "127.0.0.1";
const DEFAULT_PORT: u16 = 5300;

fn main() {
    let host = get_host();
    let port = get_port();
    let listener = server_bind(&host[..], port);

    println!("Server is running on {:?}", listener.local_addr().unwrap());
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
