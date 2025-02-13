import pandas as pd

data = {
    "dns_queries": [["example.com", "service.com"]],
    "connection_history": [["192.168.1.2", "203.0.113.6"]],
    "open_ports": [[80, 443, 21]],
    "transport_protocols": [["TCP", "UDP"]],
    "traffic_types": [["HTTPS", "HTTP", "FTP", "SSH"]],
    "exposed_ports": [[22, 3306]],
    "downloaded_data": ["2GB"],
    "uploaded_data": ["500MB"],
    "connection_protocol": ["Wi-Fi"],
    "wifi_standards": [["802.11a", "802.11b", "802.11g", "802.11n", "802.11ac", "802.11ax"]],
    "network_protocols": [["DHCP", "ARP", "TCP/IP"]],
    "security_protocols": [["WPA2", "WPA3"]],
    "channel_used": ["5 GHz"],
    "active_apps_services": [["web browser", "online game", "streaming service"]],
    "os_version": ["Windows 10 1909"],
    "browser_version": ["Chrome 92"],
    "app_version": ["Game 1.2.3"],
    "vpn_usage": [False],
    "proxy_usage": [False],
    "latitude": [48.8566],
    "longitude": [2.3522],
    "neighboring_devices": [["device2", "device3"]],
    "dhcp_server_ip": ["192.168.1.1"],
    "dns_server_ip": ["8.8.8.8"],
    "default_gateways": ["192.168.1.1"],
    "subnet_mask": ["255.255.255.0"]
}

df = pd.DataFrame(data)

df.to_csv("data.csv", index=False)