import json
data = {
    "data": {
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
}

# JSON file
with open('data.json', 'w') as f:
    json.dump(data, f, indent=6) 