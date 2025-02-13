from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Example data
data = {
    "network_activity": {
        "dns_queries": ["example.com", "service.com"],
        "connection_history": ["192.168.1.2", "203.0.113.6"],
        "open_ports": [80, 443, 21],
        "transport_protocol": ["TCP", "UDP"],
        "traffic_type": ["HTTPS", "HTTP", "FTP", "SSH"],
        "exposed_ports": [22, 3306],
        "data_volume": {
            "downloaded": "2GB",
            "uploaded": "500MB"
        }
    },
    "connection_information": {
        "protocol_used": "Wi-Fi",
        "wifi_standard": ["802.11a", "802.11b", "802.11g", "802.11n", "802.11ac", "802.11ax"],
        "network_protocols": ["DHCP", "ARP", "TCP/IP"],
        "security_protocol": ["WPA2", "WPA3"],
        "channel_used": "5 GHz"
    },
    "application_characteristics": {
        "active_apps_services": ["web browser", "online game", "streaming service"],
        "software_versions": {
            "os": "Windows 10 1909",
            "browser": "Chrome 92",
            "app": "Game 1.2.3"
        },
        "vpn_usage": False,
        "proxy_usage": False
    },
    "localization_and_environment": {
        "approximate_position": {
            "latitude": 48.8566,
            "longitude": 2.3522
        },
        "neighboring_devices": ["device2", "device3"]
    },
    "network_configuration": {
        "dhcp_server_ip": "192.168.1.1",
        "dns_server_ip": "8.8.8.8",
        "default_gateway(s)": ["192.168.1.1", "192.168.20.1"],
        "subnet_mask": "255.255.255.0"
    }
}



# Pie chart code → une couleur pour chaque masque - nombre de demande pour graph circulaire
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
        self.pie.data= [56, 12, 28, 4]
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
        self.legend.colorNamePairs    = [(PCMYKColor(100,0,90,50,alpha=100), ('255.255.0.0', '56')), (PCMYKColor(100,60,0,50,alpha=100), ('255.255.255.0', '12')), (PCMYKColor(0,100,100,40,alpha=100), ('255.255.255.252', '28')), (PCMYKColor(66,13,0,22,alpha=100), ('255.255.255.255', '4'))]
        self.width                    = 400
        self.legend.x                 = 300
        self.pie.width                = 150
        self.pie.height               = 150
        self.pie.y                    = 25
        self.pie.x                    = 25


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
    doc = SimpleDocTemplate(file_name, pagesize=letter)
    content = []
    styles = getSampleStyleSheet()

    # Title Section
    content.append(Paragraph("Device and Network Report", styles['Title']))
    content.append(Spacer(1, 12))

    # Graphe circulaire
    pie_chart = PieChart()
    content.append(pie_chart)
    content.append(Spacer(1, 12))

    # Add Sections
    add_section(content, "Network Activity", data['network_activity'], styles['Normal'], is_dict=True)
    add_section(content, "Connection_information", data['connection_information'], styles['Normal'], is_dict=True)
    add_section(content, "Application Characteristics", data['application_characteristics'], styles['Normal'], is_dict=True)
    add_section(content, "Localization and Environment", data['localization_and_environment'], styles['Normal'], is_dict=True)
    add_section(content, "Network Configuration", data['network_configuration'], styles['Normal'], is_dict=True)

    # Créer le document
    doc.build(content)

# Generate the PDF
create_pdf_with_data("data.pdf", data)
