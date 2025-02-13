from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Example data
data = {
    "connection_information": {
        "protocol_used": "Wi-Fi",
        "wifi_standard": ["802.11a", "802.11b", "802.11g", "802.11n", "802.11ac", "802.11ax"],
        "network_protocols": ["DHCP", "ARP", "TCP/IP"],
        "security_protocol": ["WPA2", "WPA3"],
        "channel_used": "5 GHz"
    },
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
def create_pdf_with_data(file_name):
    doc = SimpleDocTemplate(file_name, pagesize=letter)
    content = []
    styles = getSampleStyleSheet()

    # Title Section
    content.append(Paragraph("Device and Network Report", styles['Title']))
    content.append(Spacer(1, 12))

    # Add Sections
    add_section(content, "Connection Information", data['connection_information'], styles['Normal'], is_dict=True)
    add_section(content, "Network Activity", data['network_activity'], styles['Normal'], is_dict=True)
    add_section(content, "Application Characteristics", data['application_characteristics'], styles['Normal'], is_dict=True)
    add_section(content, "Localization and Environment", data['localization_and_environment'], styles['Normal'], is_dict=True)
    add_section(content, "Network Configuration", data['network_configuration'], styles['Normal'], is_dict=True)

    # Build the document
    doc.build(content)

# Generate the PDF
create_pdf_with_data("data.pdf")

