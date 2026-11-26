from .runtime import subprocess


def start_server():
    subprocess.run(["sudo", "systemctl", "start", "mariadb"])

def stop_server():
    subprocess.run(["sudo", "systemctl", "stop", "mariadb"])
