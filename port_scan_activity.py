import psutil
import socket
from datetime import datetime
import time

# Dictionnaire des ports à surveiller avec leurs services associés
SERVICE_DICT = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 69: "TFTP",
    80: "HTTP", 443: "HTTPS", 110: "POP3", 143: "IMAP", 3306: "MySQL",
    3389: "RDP", 8080: "HTTP Proxy", 8888: "HTTP Alternative", 3307: "MySQL Cluster",
    8000: "HTTP (Python Simple Server)", 5500: "Flask / HTTP API", 5432: "PostgreSQL",
    6379: "Redis", 9200: "Elasticsearch", 9300: "Elasticsearch (transport)",
    27017: "MongoDB", 161: "SNMP", 162: "SNMP Trap", 514: "Syslog", 520: "RIP",
    631: "CUPS", 3128: "Squid Proxy", 4444: "Blaster Worm", 5555: "ADB",
    5900: "VNC", 6000: "X11", 6660: "IRC", 6667: "IRC", 1080: "SOCKS Proxy",
    1433: "MSSQL", 1434: "MSSQL (Resolution)", 1521: "Oracle", 2049: "NFS",
    3690: "SVN", 5060: "SIP", 8081: "HTTP Proxy", 9090: "Webmin", 9999: "Remote Admin",
    10000: "Webmin", 20000: "Webmin", 10051: "Zabbix", 12345: "NetBus Trojan",
    31337: "Back Orifice", 44444: "Blaster Worm", 55555: "Netcat", 6666: "Localhost",
    1234: "C&C", 4321: "DDoS Botnet", 8009: "Tomcat AJP", 8888: "HTTP (alt)"
}

# Ensemble des connexions déjà enregistrées pour éviter les doublons
seen_connections = set()

# Fonction pour enregistrer une connexion détectée
def log_connection(ip, port, laddr, raddr, pid, proc_name):
    service = SERVICE_DICT.get(port, "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = (f"[{timestamp}] Service: {service} | "
                f"{laddr.ip}:{laddr.port} -> {raddr.ip}:{raddr.port} | "
                f"PID: {pid} ({proc_name})\n")
    print(log_line.strip())
    with open("port_activity.log", "a") as log_file:
        log_file.write(log_line)

# Fonction principale de surveillance des ports
def monitor_ports():
    while True:
        # Parcours de toutes les connexions réseau de type IP (INET)
        for conn in psutil.net_connections(kind="inet"):
            if conn.status != psutil.CONN_ESTABLISHED:
                continue  # On ne garde que les connexions établies
            if not conn.raddr:
                continue  # Certaines connexions n'ont pas d'adresse distante

            lport = conn.laddr.port
            rport = conn.raddr.port

            # Vérifie si le port local ou distant est dans la liste surveillée
            if lport in SERVICE_DICT or rport in SERVICE_DICT:
                conn_id = (conn.pid, conn.laddr.ip, lport, conn.raddr.ip, rport)
                if conn_id not in seen_connections:
                    seen_connections.add(conn_id)
                    try:
                        proc = psutil.Process(conn.pid)  # Récupère le nom du processus
                        log_connection(conn.raddr.ip, rport, conn.laddr, conn.raddr, conn.pid, proc.name())
                    except Exception:
                        log_connection(conn.raddr.ip, rport, conn.laddr, conn.raddr, conn.pid, "unknown")

        time.sleep(5)  # Pause entre chaque balayage (5 secondes)

# Point d’entrée du script
if __name__ == "__main__":
    print("▶ Surveillance des ports réseau définis dans SERVICE_DICT...")
    monitor_ports()
