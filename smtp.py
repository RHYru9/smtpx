import subprocess
import argparse
import time

def send_command(proc, command):
    """Send a command to the openssl process and get the response."""
    try:
        proc.stdin.write(command + "\r\n")
        proc.stdin.flush()
        return proc.stdout.read(1024)
    except BrokenPipeError:
        print(f"[ERROR] Broken pipe error with command: {command}")
        return None

def enumerate_users(host, port, wordlist, mode):
    """Enumerate users using VRFY, EXPN, or RCPT mode."""
    print(f"Connecting to {host}:{port} ...")

    # Open the openssl s_client subprocess
    proc = subprocess.Popen(
        ["openssl", "s_client", "-connect", f"{host}:{port}", "-starttls", "smtp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for the initial SMTP banner
    time.sleep(2)
    banner = proc.stdout.read(1024)
    if not banner:
        print("[ERROR] Failed to connect or read the banner.")
        return
    print(banner)

    response = send_command(proc, "HELO example.com")
    print(response)

    if mode == "RCPT":
        # Send MAIL FROM command before using RCPT TO
        response = send_command(proc, "MAIL FROM:<test@example.com>")
        if not response or "250" not in response:
            print("[ERROR] Failed to set MAIL FROM.")
            return
        print(response)

    print(f"Start enumerating users with {mode} mode ...")

    with open(wordlist, 'r') as file:
        for user in file:
            user = user.strip()
            if mode == "VRFY":
                command = f"VRFY {user}"
            elif mode == "EXPN":
                command = f"EXPN {user}"
            elif mode == "RCPT":
                command = f"RCPT TO:<{user}>"
            else:
                print(f"[ERROR] Unsupported mode: {mode}")
                break
            
            response = send_command(proc, command)
            if response:
                if "250" in response:
                    print(f"[SUCC] {user} - {response.strip()}")
                else:
                    print(f"[----] {user} - {response.strip()}")
            else:
                print(f"[----] {user} - No response")

    send_command(proc, "QUIT")
    proc.terminate()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SMTP User Enumeration Tool')
    parser.add_argument('-w', '--wordlist', required=True, help='Path to the wordlist')
    parser.add_argument('-H', '--host', required=True, help='SMTP server hostname')
    parser.add_argument('-p', '--port', type=int, default=25, help='SMTP server port')
    parser.add_argument('-e', '--enum', choices=['VRFY', 'EXPN', 'RCPT'], required=True, help='Enumeration mode')
    args = parser.parse_args()

    enumerate_users(args.host, args.port, args.wordlist, args.enum)
