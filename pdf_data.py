from reportlab.lib.pagesizes import A4
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

#line chart code → moyenne de trafique
from reportlab.lib.colors import purple, PCMYKColor, black, pink, green, blue
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.legends import LineLegend
from reportlab.graphics.shapes import Drawing, _DrawingEditorMixin
from reportlab.lib.validators import Auto
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.pdfbase.pdfmetrics import stringWidth, EmbeddedType1Face, registerTypeFace, Font, registerFont
from reportlab.graphics.charts.axes import XValueAxis, YValueAxis, AdjYValueAxis, NormalDateXValueAxis

class LineChart(_DrawingEditorMixin,Drawing):
    def __init__(self,width=258,height=150,*args,**kw):
        Drawing.__init__(self,width,height,*args,**kw)

        # font
        fontName = 'Helvetica'
        fontSize = 7

        # chart
        self._add(self,LinePlot(),name='chart',validate=None,desc=None)
        self.chart.y              = 15
        self.chart.x              = 30
        self.chart.width          = 210
        self.chart.height         = 90

        # line styles
        self.chart.lines.strokeWidth   = 0
        self.chart.lines.symbol        = makeMarker('FilledSquare')

        # x axis
        self.chart.xValueAxis = NormalDateXValueAxis()
        self.chart.xValueAxis.labels.fontName          = fontName
        self.chart.xValueAxis.labels.fontSize          = fontSize-1
        self.chart.xValueAxis.forceEndDate             = 1
        self.chart.xValueAxis.forceFirstDate           = 1
        self.chart.xValueAxis.labels.boxAnchor         = 'autox'
        self.chart.xValueAxis.xLabelFormat             = '{d}' # les jours

        self.chart.xValueAxis.maximumTicks             = 20 # max de "tiques" -> | sur l'axe x 
        self.chart.xValueAxis.minimumTickSpacing       = 1
        self.chart.xValueAxis.niceMonth                = 1

        self.chart.xValueAxis.strokeWidth              = 1
        self.chart.xValueAxis.loLLen                   = 5
        self.chart.xValueAxis.hiLLen                   = 5
        self.chart.xValueAxis.gridEnd                  = self.width
        self.chart.xValueAxis.gridStart                = self.chart.x-10

        # y axis
        #self.chart.yValueAxis = AdjYValueAxis()
        self.chart.yValueAxis.visibleGrid           = 1
        self.chart.yValueAxis.visibleAxis           = 0
        self.chart.yValueAxis.labels.fontName       = fontName
        self.chart.yValueAxis.labels.fontSize       = fontSize -1
        self.chart.yValueAxis.labelTextFormat       = '%d' # chiffre sur l'axe y
        self.chart.yValueAxis.valueStep             = 1 #step pour aller de 1 en 1

        self.chart.yValueAxis.strokeWidth           = 0.25
        self.chart.yValueAxis.visible               = 1
        self.chart.yValueAxis.labels.rightPadding   = 5

        #self.chart.yValueAxis.maximumTicks         = 6
        self.chart.yValueAxis.rangeRound            ='both'
        self.chart.yValueAxis.tickLeft              = 7.5
        self.chart.yValueAxis.minimumTickSpacing    = 0.5
        self.chart.yValueAxis.maximumTicks          = 8
        self.chart.yValueAxis.forceZero             = 0
        self.chart.yValueAxis.avoidBoundFrac        = 0.1

        # legend
        self._add(self,LineLegend(),name='legend',validate=None,desc=None)
        self.legend.fontName         = fontName
        self.legend.fontSize         = fontSize
        self.legend.alignment        ='right'
        self.legend.dx               = 5

        # sample data
        self.chart.data = [[(19010706, 3.3), (19010807, 4.29), (19010908, 3.2), (19011009, 3.29), (19011110, 3.0), (19011211, 3.7), (19020112, 3.9), (19020213, 3.37), (19020314, 3.951), (19020415, 3.1), (19020516, 3.62), (19020617, 3.46), (19020718, 3.9)]]

        self.chart.lines[0].strokeColor = PCMYKColor(0,100,100,40,alpha=100)
        self.chart.lines[1].strokeColor = PCMYKColor(100,0,90,50,alpha=100)
        self.chart.xValueAxis.strokeColor             = PCMYKColor(100,60,0,50,alpha=100)
        self.legend.colorNamePairs = [(PCMYKColor(0,100,100,40,alpha=100), 'Moyenne de trafique')]
        self.chart.lines.symbol.x           = 0
        self.chart.lines.symbol.strokeWidth = 0
        self.chart.lines.symbol.arrowBarbDx = 5
        self.chart.lines.symbol.strokeColor = PCMYKColor(0,0,0,0,alpha=100)
        self.chart.lines.symbol.fillColor   = None
        self.chart.lines.symbol.arrowHeight = 5
        self.legend.dxTextSpace    = 7
        self.legend.boxAnchor      = 'nw'
        self.legend.subCols.dx     = 0
        self.legend.subCols.dy     = -2
        self.legend.subCols.rpad   = 0
        self.legend.columnMaximum  = 1
        self.legend.deltax         = 1
        self.legend.deltay         = 0
        self.legend.dy             = 5
        self.legend.y              = 135
        self.legend.x              = 120
        self.chart.lines.symbol.kind        = 'FilledCross'
        self.chart.lines.symbol.size        = 5
        self.chart.lines.symbol.angle       = 45



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

    # Diagramme à bâtons
    bar_chart = BarChart()
    content.append(bar_chart)
    content.append(Spacer(1, 12))

    add_section(content, "Connection_information", data['connection_information'], styles['Normal'], is_dict=True)

    # Graphique linéaire
    line_chart = LineChart()
    content.append(line_chart)
    content.append(Spacer(1, 12))

    add_section(content, "Application Characteristics", data['application_characteristics'], styles['Normal'], is_dict=True)
    add_section(content, "Localization and Environment", data['localization_and_environment'], styles['Normal'], is_dict=True)
    add_section(content, "Network Configuration", data['network_configuration'], styles['Normal'], is_dict=True)

    # Créer le document
    doc.build(content)

# Generate the PDF
create_pdf_with_data("data.pdf", data)