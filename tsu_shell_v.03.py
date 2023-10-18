import socket
import subprocess
from threading import Thread
import sys
import select
import termios
import tty
import pty
import os
import time
from datetime import datetime
import signal
# Python full-fledged reverse shell

bash = "/data/data/com.termux/files/usr/bin/bash"
shell_logfile = "/mnt/runtime/write/emulated/0/Work/reverse_shells/log_tsu_shell"

banned_commands = ["tsu", "rm -rf /", "exit", "fg"]

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

control_c = b'\x03'

# The banner:
shell_display_01 = C_GRAY+"overmind:"+C_END+C_YELLOW
shell_display_02 = C_END+" "+C_RED+"# "+C_END

class xzbdLogger:
    global bash
    global shell_logfile

    """Log File"""
    def __init__(self):
        # Create log
        msg = ("New log started "+"*"*50+"\n") ; self.xzbdPrint(msg)
        super(xzbdLogger, self).__init__()

    def xzbdPrint(self, message):
        with open(shell_logfile, "a") as xzdb_f:
            xzdb_f.write(message+"\n")

    def log(self, text, log_datetime=False):
        if (log_datetime):
            now = datetime.now()
            zdatetime = "["+now.strftime("%d/%m/%Y %H:%M")+"] "
        else:
            zdatetime = ""

        try:
            msg = (zdatetime+str(text))
            self.xzbdPrint(msg)

        except Exception:
            msg = "EXCEPTION IN LOGGING FUNCTION"
            print(msg); print(sys.exc_info()); self.xzbdPrint(msg) ; self.xzbdPrint(sys.exc_info()) 

log = xzbdLogger()

def handle_exception(e):
    pass

def printlog_date(msg):
    print(msg); log.log(msg, log_datetime=True)

def printlog(msg):
    print(msg); log.log(msg, log_datetime=False)

def handle_client(conn):
    global log
    global bash
    global shell_display_01
    global shell_display_02
    global control_c

    while True:
        try:
            conn.sendall(b"init: ")
            data = conn.recv(4096)
            # Client authentication here:
            pw = str(data.decode("utf-8")).rstrip() # remove newline characters at end of message
            if pw == "tsu":
                break

            if not data or data == b'\r\n': # empty string means connection was closed by client
                break

        except Exception:
            m="AUTH EXCEPTION:"; printlog_date(m) ; printlog_date(sys.exc_info())
            conn.close()
            return

    # Commands are sent here:
    m="Client Authenticated."; printlog_date(m)

    # This is one way to run subprocess in an "interactive" mode:
    fxzbd_store_out = open(".xzbdout", "wb")
    fxzbd_store_err = open(".xzbderr", "wb")
    fxzbd_read_out  = open(".xzbdout", "r")
    fxzbd_read_err  = open(".xzbderr", "r")

    proc = subprocess.Popen([bash, '-il'], stdin=subprocess.PIPE, stdout=fxzbd_store_out, stderr=fxzbd_store_err)
    # Print the user the output 
    #conn.sendall(bytes(str(fxzbd_read_out.read()),'utf-8'))
    conn.sendall(bytes(shell_display_01+shell_display_02,'utf-8'))

    while True:
        try:
            # Get his next input, which will be the command that is now.
            print("before data")
            data = conn.recv(4096)
            print("Raw data: ",data)
            if not data or data == b'\r\n': # empty string means connection was closed by client
                break

        except Exception:
            m="DATA RECV EXCEPTION:"; printlog_date(m); printlog_date(sys.exc_info())
            time.sleep(5)

        try:
            cmd = str(data.decode("utf-8")).rstrip() # remove newline characters at end of message
            m = "Received command from client:"+ str(cmd);printlog_date(m)
            for command in banned_commands:
                if cmd == command:
                    conn.sendall(bytes("error: banned command\n", 'utf-8'))
                    cmd = ""
                    continue
            # Check for the special "end" CTRL+C command:
            if cmd == "qq":
                cmd = b'\x03'
                proc.stdin.write(cmd)
            else:
                proc.stdin.write(bytes(cmd+"\n", 'utf-8'))

            proc.stdin.flush()
            print("stdin flush with ["+str(cmd)+"]")
            time.sleep(0.2) # Seems like if we don't sleep, we don't get the output.

            # This part might be useless:
            try:
                proc.stdout.flush()
                print("stdout flush")
            except Exception as e:
                print("Error while flushing stdout:", e)

            try:
                proc.stderr.flush()
                print("stderr flush")
            except Exception as e:
                print("Error while flushing stderr:", e)

            zprog_output = fxzbd_read_out.read()
            conn.sendall(bytes(zprog_output, 'utf-8'))

            err = fxzbd_read_err.read()
            errxnzbd = "STDERR: \n["+str(str(err).split("\n")[1:])+"]\n"
            # Do some shenanigans with text splitting so we can get a perfect display
            stderr_splitlist = str(err).split("\n")[1:] # Split all the output of stderr by newlines

            # Get the length so we know when the last line comes (the one with the terminal display with the "#")
            stderr_split_len = str(len(stderr_splitlist))
            print("len stderr_splitlist: "+stderr_split_len)

            counter_stderr_splitlist = 1
            # The shell "#" thing is part of the stderr string apparently.
            for line in stderr_splitlist:
                # If it's the last line from stderr (which is the terminal display with the "#") don't print the ending newline:
                if ( counter_stderr_splitlist == int(stderr_split_len) ): # Last line, the one with our bash display
                    # Get our customized shell display:
                    encoded_str = line.encode()
                    # Strip the colours of the original bash shell and only get the text:
                    try:
                        middle_shelltext = (str(encoded_str).split(";32m"))[1].split("\\x1b[")[0] # We only take the part without colours from the original shell display string.
                    except IndexError:
                        middle_shelltext = ""
                    # Send our customized shell display to the user before his command:
                    conn.sendall( bytes(shell_display_01+middle_shelltext+shell_display_02,'utf-8') )
                else:
                    conn.sendall(bytes(line+"\n", 'utf-8')) # The shell "#" thing is part of the stderr string apparently.

                counter_stderr_splitlist+=1

            #conn.sendall(bytes(shell_display, 'utf-8'))

        except KeyboardInterrupt:
            sys.exit()

        except Exception:
            m="COMMAND EXECUTION EXCEPTION:";printlog_date(m); printlog_date(sys.exc_info())
            time.sleep(5)
            continue


    proc.kill()
    proc.communicate()
    conn.close()
    m = "Client Disconnected"; printlog_date(m)

def child_murderer(signum, frame):
    """Reap child processes to avoid zombies."""
    while True:
        try:
            child_pid, status = os.waitpid(-1, os.WNOHANG)
            if child_pid == 0:
                break
        except ChildProcessError:
            break

# Set up the signal handler for SIGCHLD
signal.signal(signal.SIGCHLD, child_murderer)


def delete_temp_files():
    files_to_delete = ['.xzbderr', '.xzbdout']
    for file in files_to_delete:
        try:
            os.remove(file)
            printlog_date(f"Deleted {file}")
        except FileNotFoundError:
            pass
        except Exception as e:
            printlog_date(f"Error deleting {file}: {e}")

        # Touch (create empty) the file after deletion
        with open(file, 'a') as f:
            pass
        printlog_date(f"Created empty {file}")

def main():
    last_connection_time = time.time()

    with socket.socket() as s:
        s.settimeout(5)
        s.bind(("0.0.0.0", 1337))
        s.listen()
        while True:
            try:
                conn, addr = s.accept()
                last_connection_time = time.time()  # Update the last connection timestamp
                
                pid = os.fork()
                
                if pid == 0:  # Child
                    s.close()  # Close the listening socket in child.
                    handle_client(conn)
                    conn.close()
                    os._exit(0)

                else:  # Parent
                    conn.close()

            except socket.timeout:
                # Check if it has been more than 1 hour since the last connection
                if time.time() - last_connection_time > 3600:  # 3600 seconds = 1 hour
                    delete_temp_files() # Check the output files periodically so they don't get too big.
                continue

if __name__ == '__main__':
    main()
