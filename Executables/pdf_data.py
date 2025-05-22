from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import platform
import requests
import socket
import subprocess
from collections import Counter
import psutil
import os
import re
from datetime import datetime


# Définir le chemin absolu du répertoire courant
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# GESTION MODULES EXTERNES
try:
    import Networkdata
    config = Networkdata.get_network_configuration()
    if not isinstance(config, dict):
        raise ValueError("Configuration réseau invalide")
except Exception:
    config = {}


try:
    import wifi_info
    system = platform.system()
    conn_info = wifi_info.get_connection_info()
    if system == "Windows":
        conn_info = wifi_info.parse_text_to_dict(conn_info)
except Exception:
    conn_info = {"WiFi SSID": "Inconnu", "Signal": "Inconnu"}


# Données config réseau par défaut
list_of_network_data = []
if config:
    for value in config.values():
        list_of_network_data.append(value)



dhcp = list_of_network_data[0] if len(list_of_network_data) > 0 else "Non disponible"
dns = list_of_network_data[1] if len(list_of_network_data) > 1 else "Non disponible"
gateway = list_of_network_data[2] if len(list_of_network_data) > 2 else "Non disponible"
mask = list_of_network_data[3] if len(list_of_network_data) > 3 else "Non disponible"


def parse_traffic_types_with_count(log_path):
    traffic_counter = Counter()
    log_path = os.path.join(CURRENT_DIR, log_path)
    if not os.path.exists(log_path):
        print(f"Fichier de log introuvable: {log_path}")
        return traffic_counter
    try:
        with open(log_path, "r", encoding="utf-8") as file:
            for line in file:
                if "Service:" in line:
                    try:
                        service_part = line.split("Service:")[1].split("|")[0].strip()
                        traffic_counter[service_part] += 1
                    except IndexError:
                        continue
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {log_path}: {str(e)}")
    return traffic_counter


counts = parse_traffic_types_with_count("port_activity.log")
protocols = list(counts.keys()) if counts else ["Aucun"]
proprotocols = list(counts.values()) if counts else [1]


def get_recent_connections():
    try:
        ip_addresses = set()
        for conn in psutil.net_connections(kind='inet'):
            if conn.raddr and conn.status in ('ESTABLISHED', 'CLOSE_WAIT', 'TIME_WAIT'):
                ip_addresses.add(conn.raddr.ip)
        return list(ip_addresses)[:5]
    except Exception as e:
        print(f"Erreur lors de la récupération des connexions récentes: {str(e)}")
        return ["Non disponible"]


def get_open_ports():
    try:
        return sorted(set(conn.laddr.port for conn in psutil.net_connections(kind='inet') if conn.status == 'LISTEN'))
    except Exception as e:
        print(f"Erreur lors de la récupération des ports ouverts: {str(e)}")
        return []


def get_exposed_ports():
    try:
        ports = set()
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == psutil.CONN_LISTEN:
                ip = conn.laddr.ip
                if ip not in ('127.0.0.1', '::1'):
                    ports.add(conn.laddr.port)
        return sorted(ports)
    except Exception as e:
        print(f"Erreur lors de la récupération des ports exposés: {str(e)}")
        return []


def is_local_partition(partition):
    try:
        if platform.system() == 'Windows':
            return partition.fstype != 'Network'
        return partition.fstype not in ['cifs', 'nfs', 'fuse', 'smbfs']
    except Exception:
        return True


def get_total_local_disk_space():
    try:
        total = 0
        for p in psutil.disk_partitions():
            try:
                if is_local_partition(p):
                    total += psutil.disk_usage(p.mountpoint).total
            except (PermissionError, FileNotFoundError):
                continue
        return total / (1024**3)
    except Exception as e:
        print(f"Erreur lors du calcul de l'espace disque: {str(e)}")
        return 0


def get_system_info():
    try:
        os_info = f"{platform.system()} {platform.release()}"
        cpu_info = "Unknown"
        
        if platform.system() == "Windows":
            try:
                cpu_info = subprocess.check_output("wmic cpu get name", shell=True, stderr=subprocess.DEVNULL).decode().strip().split("\n")[1].strip()
            except:
                pass
        else:
            try:
                cpu_info = subprocess.check_output("lscpu | grep 'Model name' | cut -d: -f2", shell=True, stderr=subprocess.DEVNULL).decode().strip()
            except:
                pass

        ram = f"{psutil.virtual_memory().total / (1024**3):.0f} GB"
        disk = f"{get_total_local_disk_space():.0f} GB"
        hostname = socket.gethostname()
        return os_info, cpu_info, ram, disk, hostname
    except Exception as e:
        print(f"Erreur lors de la récupération des informations système: {str(e)}")
        return "Unknown", "Unknown", "Unknown", "Unknown", "Unknown"


os_info, cpu_info, ram, disk, hostname = get_system_info()


def get_location_values():
    try:
        timeout = 5  # timeout en secondes
        data = requests.get("https://ipinfo.io/json", timeout=timeout).json()
        return [data.get(k, "Non disponible") for k in ["ip", "city", "region", "country", "loc", "org", "timezone"]]
    except Exception as e:
        print(f"Erreur lors de la récupération des informations de localisation: {str(e)}")
        return ["Non disponible"] * 7


ip, city, region, country, loc, isp, timezone = get_location_values()


data = {
    "network_activity": {
        "connection_history": get_recent_connections(),
        "open_ports": get_open_ports(),
        "traffic_type": protocols,
        "exposed_ports": get_exposed_ports(),
    },
    "connection_information": conn_info,
    "host_characteristics": {
        "os": os_info, "cpu": cpu_info, "ram": ram, "disk": disk, "hostname": hostname
    },
    "localization_and_environment": {
        "Public IP": ip, "City": city, "Region": region, "Country": country,
        "Location (lat,long)": loc, "ISP": isp, "Timezone": timezone
    },
    "network_configuration": {
        "dhcp_server_ip": dhcp, "dns_server_ip": dns,
        "default_gateway(s)": gateway, "subnet_mask": mask
    }
}


from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.shapes import Drawing, _DrawingEditorMixin
from reportlab.lib.colors import PCMYKColor


class PieChart(_DrawingEditorMixin, Drawing):
    def __init__(self, width=400, height=200, *args, **kw):
        Drawing.__init__(self, width, height, *args, **kw)
        self._add(self, Pie(), name='pie')
        self._add(self, Legend(), name='legend')
        self.pie.data = proprotocols
        self.pie.labels = protocols
        self.pie.width = 150
        self.pie.height = 150
        self.pie.x = 25
        self.pie.y = 25
        self.legend.x = 200
        self.legend.y = 100
        self.legend.boxAnchor = 'c'
        self.legend.colorNamePairs = [
            (PCMYKColor(100,0,90,50), f"{protocols[i]} ({proprotocols[i]})")
            for i in range(min(len(protocols), len(proprotocols)))
        ]


def get_five_min_traffic(log_file="internet_usage.log"):
    five_min_traffic = {}
    log_file = os.path.join(CURRENT_DIR, log_file)
    try:
        if not os.path.exists(log_file):
            print(f"Fichier de log introuvable: {log_file}")
            return []
        
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                match = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Total: ([\d.]+) MB", line)
                if match:
                    timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                    total_mb = float(match.group(2))
                    minute = (timestamp.minute // 5) * 5
                    time_key = timestamp.replace(minute=minute, second=0).strftime("%Y%m%d%H%M")
                    five_min_traffic[time_key] = five_min_traffic.get(time_key, 0) + total_mb
        return [(int(k), round(v, 2)) for k, v in sorted(five_min_traffic.items())]
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {log_file}: {str(e)}")
        return []


def datetime_formatter(x):
    try:
        return datetime.strptime(str(int(x))[:12], "%Y%m%d%H%M").strftime("%H:%M")
    except ValueError:
        return "N/A"


from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.axes import XValueAxis, YValueAxis
from reportlab.graphics.widgets.markers import makeMarker


class LineChart(_DrawingEditorMixin, Drawing):
    def __init__(self, width=300, height=150, *args, **kw):
        Drawing.__init__(self, width, height, *args, **kw)
        self._add(self, LinePlot(), name='chart')
        self.chart.x = 30
        self.chart.y = 30
        self.chart.height = 90
        self.chart.width = 210
        traffic_data = get_five_min_traffic()
        self.chart.data = [traffic_data] if traffic_data else [[(0, 0)]]
        self.chart.lines[0].strokeColor = PCMYKColor(0, 100, 100, 40)
        self.chart.lines.symbol = makeMarker('FilledCircle')
        self.chart.xValueAxis = XValueAxis()
        self.chart.xValueAxis.labelTextFormat = datetime_formatter
        self.chart.yValueAxis = YValueAxis()
        self.chart.yValueAxis.valueMin = 0
        self.chart.yValueAxis.valueMax = 100 if not traffic_data else max(v for _, v in traffic_data) + 10
        self.chart.yValueAxis.valueStep = 20


def add_section(content, title, data, style, is_dict=False):
    content.append(Paragraph(f"<b>{title}</b>", style))
    if is_dict:
        for key, value in data.items():
            val = ("\n".join(f"{k}: {v}" for k, v in value.items()) if isinstance(value, dict)
                   else ", ".join(map(str, value)) if isinstance(value, (list, set))
                   else str(value))
            content.append(Paragraph(f"<b>{key}:</b> {val}", style))
    else:
        content.append(Paragraph(f"<b>{title}:</b> {data}", style))
    content.append(Spacer(1, 12))


def create_pdf_with_data(file_name, data):
    try:
        # Utiliser un chemin absolu pour le fichier PDF
        if not os.path.isabs(file_name):
            file_name = os.path.join(CURRENT_DIR, file_name)
            
        doc = SimpleDocTemplate(file_name, pagesize=A4)
        content = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Normal_Left', alignment=TA_LEFT))
        content.append(Paragraph("Network Information Report", styles['Title']))
        content.append(Spacer(1, 12))

        pie = PieChart()
        content.append(pie)
        content.append(Spacer(1, 12))
        
        line = LineChart()
        content.append(line)
        content.append(Spacer(1, 12))

        # Ajouter chaque section du rapport
        add_section(content, "Caractéristiques de l'hôte", data["host_characteristics"], styles['Normal_Left'], is_dict=True)
        add_section(content, "Activité réseau", data["network_activity"], styles['Normal_Left'], is_dict=True)
        add_section(content, "Informations de connexion", data["connection_information"], styles['Normal_Left'], is_dict=True)
        add_section(content, "Localisation et environnement", data["localization_and_environment"], styles['Normal_Left'], is_dict=True)
        add_section(content, "Configuration réseau", data["network_configuration"], styles['Normal_Left'], is_dict=True)

        doc.build(content)
        print(f"PDF généré avec succès: {file_name}")
        return True
    except Exception as e:
        print(f"Erreur lors de la génération du PDF: {str(e)}")
        return False

# Main function to generate PDF when run directly
if __name__ == "__main__":
    output_file = "data.pdf"
    print(f"Generating PDF report: {output_file}")
    if create_pdf_with_data(output_file, data):
        print(f"PDF report successfully generated: {os.path.abspath(output_file)}")
    else:
        print("Failed to generate PDF report") 