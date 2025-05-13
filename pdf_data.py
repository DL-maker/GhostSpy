from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import platform
import requests
import socket
import subprocess
from collections import Counter
import psutil
import Networkdata
import os
import wifi_info
import re
from datetime import datetime


def parse_traffic_types_with_count(log_path):
    traffic_counter = Counter()

    if not os.path.exists(log_path):
        return traffic_counter

    with open(log_path, "r", encoding="utf-8") as file:
        for line in file:
            if "Service:" in line:
                try:
                    service_part = line.split("Service:")[1].split("|")[0].strip()
                    traffic_counter[service_part] += 1
                except IndexError:
                    continue

    return traffic_counter


counts = parse_traffic_types_with_count("port_activity.log")
protocols = list(counts.keys())
proprotocols = list(counts.values())

def get_recent_connections():
    ip_addresses = set()

    for conn in psutil.net_connections(kind='inet'):
        
        if conn.raddr and conn.status in ('ESTABLISHED', 'CLOSE_WAIT', 'TIME_WAIT'):
            ip_addresses.add(conn.raddr.ip)  

    return ip_addresses

last_con = list(get_recent_connections())
last_con = last_con[:5]
def get_open_ports():
    # On initialise un ensemble (set) pour stocker les ports ouverts
    open_ports = set()
    
    # On récupère toutes les connexions réseau qui sont de type 'inet' (connexions Internet)
    # On spécifie 'kind="inet"' pour obtenir les connexions TCP/IP
    for conn in psutil.net_connections(kind='inet'):
        # On ne garde que les connexions qui ont le statut 'LISTEN' (écoutent sur un port)
        if conn.status == 'LISTEN':
            # Si le port est en mode 'LISTEN', on l'ajoute à l'ensemble open_ports
            open_ports.add(conn.laddr.port)  # conn.laddr.port contient le numéro du port
    
    # On retourne l'ensemble des ports ouverts
    return open_ports
open_portss = get_open_ports()
def get_exposed_ports():
    ports = set()
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == psutil.CONN_LISTEN:
            laddr = conn.laddr
            ip = laddr.ip
            port = laddr.port
            
            if ip != '127.0.0.1' and ip != '::1':
                ports.add(port)
    return sorted(ports)

exposed_ports = get_exposed_ports()


def is_local_partition(partition):
    if platform.system() == 'Windows':
        return partition.fstype != 'Network'
    else:  # Linux
        return partition.fstype not in ['cifs', 'nfs', 'fuse', 'smbfs']

def get_total_local_disk_space():
    total = 0
    for partition in psutil.disk_partitions():
        if is_local_partition(partition):
            usage = psutil.disk_usage(partition.mountpoint)
            total += usage.total
    return total / (1024**3)  # en gb

def get_system_info():
    # info OS
    os_info = f"{platform.system()} {platform.release()}"

    # CPU
    if platform.system() == "Windows":
        try:
            cpu_info = subprocess.check_output("wmic cpu get name", shell=True).decode().strip().split("\n")[1].strip()
        except:
            cpu_info = "Unknown"
    else:  # Linux
        try:
            cpu_info = subprocess.check_output("lscpu | grep 'Model name' | cut -d: -f2", shell=True).decode().strip()
        except:
            cpu_info = "Unknown"

    # RAM
    ram = psutil.virtual_memory().total / (1024**3)
    ram = f"{ram:.0f} GB"

    
    disk = get_total_local_disk_space()
    disk = f"{disk:.0f} GB"

    
    hostname = socket.gethostname()


    
    software_versions = (  os_info,
         cpu_info,
         ram,
        disk,
        hostname
    )

    return software_versions


system_info = get_system_info()
os_info = system_info[0]
cpu_info = system_info[1] 
ram = system_info[2] 
disk = system_info[3] 
hostname = system_info[4] 

config = Networkdata.get_network_configuration() 
list_of_network_data = []

for value in config.values():    
    list_of_network_data.append(value)
dhcp = list_of_network_data[0]
dns = list_of_network_data[1]
gateway = list_of_network_data[2]
mask = list_of_network_data[3] 
def get_location_values():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()

        return [
            data.get("ip"),
            data.get("city"),
            data.get("region"),
            data.get("country"),
            data.get("loc"),
            data.get("org"),
            data.get("timezone")
        ]
    except Exception as e:
        return [str(e)]

location_data = get_location_values()
ip, city, region, country, loc, isp, timezone = location_data

system = wifi_info.platform.system()
if system == "Windows":
    conn_info = wifi_info.get_connection_info()
    conn_info = wifi_info.parse_text_to_dict(conn_info)
elif system == "Linux":
    conn_info = wifi_info.get_connection_info()



data = {
    "network_activity": {
        "connection_history": last_con,
        "open_ports": open_portss,
        "traffic_type": protocols,
        "exposed_ports": exposed_ports,
        
    },
    "connection_information": {},
    "host_characteristics": {
            "os":  os_info,
            "cpu": cpu_info,
            "ram": ram,
            "disk": disk,
            "hostname": hostname
        
    },
    "localization_and_environment": {
            "Public IP": ip,
            "City": city,
            "Region": region,
            "Country":country,
            "Location (lat,long)":loc,
            "ISP":isp,
            "Timezone":timezone,
            
        
    },
    "network_configuration": {
        "dhcp_server_ip": dhcp,
        "dns_server_ip": dns,
        "default_gateway(s)": gateway,
        "subnet_mask": mask
    }
}
data["connection_information"] = conn_info


# Pie chart code → une couleur pour chaque masque et son nombre de demande
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.piecharts import Pie
from reportlab.pdfbase.pdfmetrics import stringWidth, EmbeddedType1Face, registerTypeFace, Font, registerFont
from reportlab.graphics.shapes import Drawing, _DrawingEditorMixin
from reportlab.lib.colors import Color, PCMYKColor, white

class PieChart(_DrawingEditorMixin,Drawing):
    def __init__(self,width=400,height=200,*args,**kw):
        Drawing.__init__(self,width,height,*args,**kw)
        fontSize    = 8
        fontName    = 'Helvetica'

        #pie
        self._add(self,Pie(),name='pie',validate=None,desc=None)
        self.pie.strokeWidth            = 1
        self.pie.slices.strokeColor     = PCMYKColor(0,0,0,0)
        self.pie.slices.strokeWidth     = 1

        #legend
        self._add(self,Legend(),name='legend',validate=None,desc=None)
        self.legend.columnMaximum       = 99
        self.legend.alignment           = 'right'
        self.legend.dx                  = 6
        self.legend.dy                  = 6
        self.legend.dxTextSpace         = 5
        self.legend.deltay              = 10
        self.legend.strokeWidth         = 0
        self.legend.subCols[0].minWidth = 10
        self.legend.subCols[0].align    = 'left'
        self.legend.subCols[1].minWidth = 25
        self.legend.subCols[1].align    = 'right'

        #data
        colors= [PCMYKColor(100,67,0,23,alpha=100), PCMYKColor(70,46,0,16,alpha=100), PCMYKColor(50,33,0,11,alpha=100), PCMYKColor(30,20,0,7,alpha=100), PCMYKColor(20,13,0,4,alpha=100), PCMYKColor(10,7,0,3,alpha=100), PCMYKColor(0,0,0,100,alpha=100), PCMYKColor(0,0,0,70,alpha=100), PCMYKColor(0,0,0,50,alpha=100), PCMYKColor(0,0,0,30,alpha=100), PCMYKColor(0,0,0,20,alpha=100), PCMYKColor(0,0,0,10,alpha=100)]

        self.pie.data= proprotocols
        for i in range(len(self.pie.data)): self.pie.slices[i].fillColor = colors[i]
        self.height                  = 200
        self.legend.boxAnchor        = 'c'
        self.legend.y                = 100
        self.pie.strokeColor         = PCMYKColor(0,0,0,0,alpha=100)
        self.pie.slices[1].fillColor         = PCMYKColor(100,60,0,50,alpha=100)
        self.pie.slices[2].fillColor         = PCMYKColor(0,100,100,40,alpha=100)
        self.pie.slices[3].fillColor         = PCMYKColor(66,13,0,22,alpha=100)
        self.pie.slices[0].fillColor         = PCMYKColor(100,0,90,50,alpha=100)

        #infos écrites dans la légende ↓
        self.legend.colorNamePairs = [(c, (protocols[i] if i < len(protocols) else "Unknown", str(proprotocols[i]) if i < len(proprotocols) else "0")) for i, c in enumerate([PCMYKColor(100,0,90,50,alpha=100), PCMYKColor(100,60,0,50,alpha=100), PCMYKColor(0,100,100,40,alpha=100), PCMYKColor(66,13,0,22,alpha=100)])][:len(proprotocols)]
        self.width                    = 400
        self.legend.x                 = 300
        self.pie.width                = 150
        self.pie.height               = 150
        self.pie.y                    = 25
        self.pie.x                    = 25


# bar chart code → nombre de demande par port
from reportlab.lib.colors import PCMYKColor, Color, CMYKColor, black
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.shapes import Drawing, _DrawingEditorMixin, String, Line
from reportlab.lib.validators import Auto
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth, EmbeddedType1Face, registerTypeFace, Font, registerFont
from reportlab.lib.formatters import DecimalFormatter
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.textlabels import Label

class BarChart(_DrawingEditorMixin, Drawing):
    def __init__(self, width=403, height=163, *args, **kw):
        Drawing.__init__(self, width, height, *args, **kw)
        fontName = 'Helvetica'
        fontSize = 5
        bFontName = 'Times-Bold'
        bFontSize = 7
        colorsList = [PCMYKColor(0, 73, 69, 56)]

        # Diagramme à bâtons
        self._add(self, VerticalBarChart(), name='chart', validate=None, desc=None)
        self.chart.height = 70
        self.chart.fillColor = None
        self.chart.data = [[7, 8, 9, 7, 6, 8], [4, 1, 13, 10, 8, 10], [5, 9, 5, 4, 3, 4]]
        self.chart.bars.strokeWidth = 0.5
        self.chart.bars.strokeColor = PCMYKColor(0, 0, 0, 100)
        for i, color in enumerate(colorsList):
            self.chart.bars[i].fillColor = color

        self.chart.valueAxis.labels.fontName = fontName
        self.chart.valueAxis.labels.fontSize = fontSize
        self.chart.valueAxis.strokeDashArray = (5, 0)
        self.chart.valueAxis.visibleGrid = False
        self.chart.valueAxis.visibleTicks = False
        self.chart.valueAxis.tickLeft = 0
        self.chart.valueAxis.tickRight = 11
        self.chart.valueAxis.strokeWidth = 0.25
        self.chart.valueAxis.avoidBoundFrac = 0
        self.chart.valueAxis.rangeRound = 'both'
        self.chart.valueAxis.gridStart = 13
        self.chart.valueAxis.gridEnd = 342
        self.chart.valueAxis.forceZero = True
        self.chart.valueAxis.labels.boxAnchor = 'e'
        self.chart.valueAxis.labels.dx = -1

        self.chart.categoryAxis.strokeDashArray = (5, 0)
        self.chart.categoryAxis.visibleGrid = False
        self.chart.categoryAxis.visibleTicks = False
        self.chart.categoryAxis.strokeWidth = 0.25
        self.chart.categoryAxis.tickUp = 5
        self.chart.categoryAxis.tickDown = 0
        self.chart.categoryAxis.labelAxisMode = 'low'
        self.chart.categoryAxis.labels.textAnchor = 'end'
        self.chart.categoryAxis.labels.fillColor = black
        self.chart.categoryAxis.labels.angle = 0
        self.chart.categoryAxis.labels.fontName = bFontName
        self.chart.categoryAxis.labels.fontSize = bFontSize
        self.chart.categoryAxis.labels.boxAnchor = 'e'
        self.chart.categoryAxis.labels.dx = 7
        self.chart.categoryAxis.labels.dy = -5

        # Legend
        self._add(self, Legend(), name='legend', validate=None, desc=None)
        self.legend.deltay = 8
        self.legend.fontName = fontName
        self.legend.fontSize = fontSize
        self.legend.strokeWidth = 0.5
        self.legend.strokeColor = PCMYKColor(0,0,0,100)
        self.legend.autoXPadding = 0
        self.legend.dy = 5
        self.legend.variColumn = True
        self.legend.subCols.minWidth = self.chart.width/2
        self.legend.colorNamePairs = Auto(obj=self.chart)

        # Nom des légendes
        self.chart.bars[0].name = 'SSH'
        self.chart.bars[1].name = 'FTP'
        self.chart.bars[2].name = 'Telnet'

        self.width = 400
        self.height = 200
        self.legend.dx = 8
        self.legend.dxTextSpace = 5
        self.legend.deltax = 0
        self.legend.alignment = 'right'
        self.legend.columnMaximum = 3
        self.chart.y = 80
        self.chart.barWidth = 2
        self.chart.groupSpacing = 5
        self.chart.width = 250
        self.chart.barSpacing = 0.5
        self.chart.x = 20
        self.legend.y = 45
        self.legend.boxAnchor = 'sw'
        self.legend.x = 20
        self.chart.bars[0].fillColor = PCMYKColor(100,60,0,50,alpha=100)
        self.chart.bars[1].fillColor = PCMYKColor(23,51,0,4,alpha=100)
        self.chart.bars[2].fillColor = PCMYKColor(100,0,90,50,alpha=100)


def get_five_min_traffic(log_file="internet_usage.log"):
    five_min_traffic = {}
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                
                match = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Total: ([\d.]+) MB", line)
                if match:
                    timestamp = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                    total_mb = float(match.group(2))
                    
                    minute = (timestamp.minute // 5) * 5
                    time_key = timestamp.replace(minute=minute, second=0).strftime("%Y%m%d%H%M")
                    five_min_traffic[time_key] = five_min_traffic.get(time_key, 0) + total_mb
        
        data = [(int(k), round(v, 2)) for k, v in sorted(five_min_traffic.items())]
        return data
    except FileNotFoundError:
        return []  
    
def datetime_formatter(x):
    try:
        time_str = str(int(x))[:12]
        return datetime.strptime(time_str, "%Y%m%d%H%M").strftime("%H:%M")
    except ValueError:
        return "N/A"
#line chart code → moyenne de trafique
from reportlab.lib.colors import PCMYKColor
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.legends import LineLegend
from reportlab.graphics.shapes import Drawing, _DrawingEditorMixin
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.graphics.charts.axes import XValueAxis, YValueAxis
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
class LineChart(_DrawingEditorMixin, Drawing):
    def __init__(self, width=258, height=150, *args, **kw):
        Drawing.__init__(self, width, height, *args, **kw)

        
        fontName = 'Helvetica'
        fontSize = 7

        
        self._add(self, LinePlot(), name='chart', validate=None, desc=None)
        self.chart.y = 15
        self.chart.x = 30
        self.chart.width = 210
        self.chart.height = 90

        
        self.chart.lines.strokeWidth = 0
        self.chart.lines.symbol = makeMarker('FilledSquare')

        
        self.chart.xValueAxis = XValueAxis()
        self.chart.xValueAxis.labels.fontName = fontName
        self.chart.xValueAxis.labels.fontSize = fontSize - 1
        self.chart.xValueAxis.labelTextFormat = datetime_formatter
        self.chart.xValueAxis.maximumTicks = 10  # До 10 меток для читаемости
        self.chart.xValueAxis.minimumTickSpacing = 1
        self.chart.xValueAxis.strokeWidth = 1
        self.chart.xValueAxis.loLLen = 5
        self.chart.xValueAxis.hiLLen = 5
        self.chart.xValueAxis.gridEnd = self.width
        self.chart.xValueAxis.gridStart = self.chart.x - 10

        
        self.chart.yValueAxis = YValueAxis()
        self.chart.yValueAxis.labels.fontName = fontName
        self.chart.yValueAxis.labels.fontSize = fontSize - 1
        self.chart.yValueAxis.labelTextFormat = '%d'  
        self.chart.yValueAxis.valueMin = 0
        self.chart.yValueAxis.valueMax = 100 
        self.chart.yValueAxis.valueStep = 20  
        self.chart.yValueAxis.visibleGrid = 1 
        self.chart.yValueAxis.strokeWidth = 0.25  
        self.chart.yValueAxis.labels.rightPadding = 5 
        self.chart.yValueAxis.strokeColor = PCMYKColor(100, 60, 0, 50, alpha=100)  
        self.chart.yValueAxis.gridStrokeColor = PCMYKColor(0, 0, 0, 10, alpha=50)  
        self.chart.yValueAxis.gridStrokeWidth = 0.1 
        # Настройка легенды
        # Настройка легенды
      
        self.chart.data = [get_five_min_traffic()]  # data provenat des logs

        # les colors et styles
        self.chart.lines[0].strokeColor = PCMYKColor(0, 100, 100, 40, alpha=100)
        self.chart.xValueAxis.strokeColor = PCMYKColor(100, 60, 0, 50, alpha=100)
        self.chart.lines.symbol.x = 0
        self.chart.lines.symbol.strokeWidth = 0
        self.chart.lines.symbol.arrowBarbDx = 5
        self.chart.lines.symbol.strokeColor = PCMYKColor(0, 0, 0, 0, alpha=100)
        self.chart.lines.symbol.fillColor = None
        self.chart.lines.symbol.arrowHeight = 5
        # self.legend.dxTextSpace = 7
        # self.legend.boxAnchor = 'nw'
        # self.legend.subCols.dx = 0
        # self.legend.subCols.dy = -2
        # self.legend.subCols.rpad = 0
        # self.legend.columnMaximum = 1
        # self.legend.deltax = 1
        # self.legend.deltay = 0
        # self.legend.dy = 5
        # self.legend.y = 135
        # self.legend.x = 120
        self.chart.lines.symbol.kind = 'FilledCross'
        self.chart.lines.symbol.size = 5
        self.chart.lines.symbol.angle = 45
# Helper function to create sections
def add_section(content, title, data, style, is_dict=False):
    content.append(Paragraph(f"<b>{title}</b>", style))
    if is_dict:
        for key, value in data.items():
            # Convert items in the list to strings before joining
            content.append(Paragraph(f"<b>{key}:</b> {', '.join(map(str, value)) if isinstance(value, list) else value}", style))
    else:
        content.append(Paragraph(f"<b>{title}:</b> {data}", style))
    content.append(Spacer(1, 12))

# Create the PDF document
def create_pdf_with_data(file_name, data):
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    content = []
    styles = getSampleStyleSheet()

    # Title Section
    content.append(Paragraph("Network Information Report", styles['Title']))
    content.append(Spacer(1, 12))

    # Graphique circulaire
    pie_chart = PieChart()
    content.append(pie_chart)
    content.append(Spacer(1, 12))

    # Add Sections
    add_section(content, "Network Activity", data['network_activity'], styles['Normal'], is_dict=True)

    # # Diagramme à bâtons
    # bar_chart = BarChart()
    # content.append(bar_chart)
    # content.append(Spacer(1, 12))

    add_section(content, "Connection_information", data['connection_information'], styles['Normal'], is_dict=True)
    
    # Graphique linéaire
    line_chart = LineChart()
    content.append(line_chart)
    content.append(Spacer(1, 12))

    content.append(Paragraph("Data usage in mb/5min"))
    content.append(Spacer(1, 12))
    
    add_section(content, "Host Characteristics", data['host_characteristics'], styles['Normal'], is_dict=True)
    add_section(content, "Localization and Environment", data['localization_and_environment'], styles['Normal'], is_dict=True)
    add_section(content, "Network Configuration", data['network_configuration'], styles['Normal'], is_dict=True)

    # Créer le document
    doc.build(content)

# Generate the PDF
create_pdf_with_data("data.pdf", data)