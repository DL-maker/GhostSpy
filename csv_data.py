import pandas as pd
data = {
    "Client": ["Client1"],
    "MAC Address": ["AA:BB:CC:DD:EE:FF"],
    "Local IP": ["192.168.1.1"],
    "Public IP": ["203.0.113.5"],
    "Hostname": ["device1"],
    "Protocol": ["Wi-Fi"],
    "Wi-Fi Standard": ["802.11ac"],
    "Network Protocols": ["DHCP, ARP, TCP/IP"],
    "Security Protocol": ["WPA2"],
    "Channel": ["5 GHz"],
    "DNS Queries": ["example.com"],
    "Open Ports": ["80, 443"],
    "Data Volume (Download/Upload)": ["2GB/500MB"],
    "VPN Usage": ["No"],
    "Proxy Usage": ["Yes"]
}
df = pd.DataFrame(data)

df.to_csv("data.csv", index=False)