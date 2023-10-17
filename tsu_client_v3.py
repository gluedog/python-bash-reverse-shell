# Tsu Client
import socket
import time
import sys
import select

bash = "/data/data/com.termux/files/usr/bin/bash"
host = '127.0.0.1'
port = 1337


# Colours:
C_GREEN_BOLD = "\033[1;32;40m"
C_RED_BOLD   = "\033[1;91;40m"

C_RED = '\033[91m'
C_GREEN = '\033[32m'
C_YELLOW = '\033[33m'
C_LYELLOW = '\033[37m'
C_GRAY = '\033[90m'
C_NEWDEX = '\033[35m'
C_WITHDRAW = '\033[36m'

C_END = '\033[0m'

########################

# The banner:
shell_display_01 = C_GRAY+"overmind:"+C_END+C_YELLOW
shell_display_02 = C_END+" "+C_RED+"# "+C_END

control_c = b'\x03'

import readline

def zxbd_input():
    try:
        userinput = input()
    except EOFError:
        return ""
    return userinput

#def refresh(current_commander):
    #readline.add_history(current_commander)

def main():
    global host, port
    global shell_display_01, shell_display_02
    global control_c

    # Create a TCP/IP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect to server
    print('Connecting to {}:{}...'.format(host,port))
    s.connect((host, port))
    s.settimeout(2)

    while True:
        try:
            data = s.recv(10000) # buffer size is 10 kilo bytes
            print(data.decode(), end="")
            if not data or data == b'\r\n': # empty string means connection was closed by client
                print("exiting... dead connection.")
                break

        except TimeoutError:
            print("no more data from server...\n"+shell_display_01+shell_display_02, end="")
            time.sleep(0.2)

        try: # get message from user
            rawmsg = zxbd_input()
            bytecode_msg = rawmsg.encode()

        except KeyboardInterrupt:
            s.sendall(control_c + b'\n') # pass through the keyboard interrupt
            time.sleep(0.4)
            continue

        if bytecode_msg == b"1exit":
            print("exiting overmind shell...")
            sys.exit()

        # send message to server. pressing enter and writing nothing will just keep on reading from the socket buffer
        if (bytecode_msg != b""):
            #if rawmsg != " ":
                #refresh(rawmsg) # Refresh the commander
            s.sendall(bytecode_msg + b'\n')
            time.sleep(0.4)

if __name__ == '__main__':
    main()

