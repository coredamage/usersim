# Copyright 2017 Carnegie Mellon University. See LICENSE.md file for terms.

import socket
import threading

import api
import usersim


TCP_IP = 'localhost'
TCP_PORT = 5005

def run_test():
    telnet_config = {'type': 'telnet',
                     'config': {'host': TCP_IP,
                                'username': 'admin',
                                'password': 'password',
                                'commandlist': ['printstuff', 'do other stuff', 'do this thing'],
                                'port': TCP_PORT}}

    sim = usersim.UserSim(True)

    task_id = api.validate_config(telnet_config)

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)

    conn, addr = s.accept()
    print('Connection Address: ' + str(addr))
    while True:
        data = conn.recv(20)
        if not data:
            break
        print('received data: ' + str(data))
        conn.send(data)

    conn.close()

if __name__ == '__main__':
    run_test()
