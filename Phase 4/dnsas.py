from scapy.all import ARP, Ether, srp, sniff, DNS, DNSQR, IP

def scan_network(network):

    
    arp_request = ARP(pdst=network)
    
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
   
    arp_request_broadcast = broadcast / arp_request

    
    answered_list = srp(arp_request_broadcast, timeout=3, verbose=0)[0]


    clients = []
    for sent, received in answered_list:
        clients.append({'ip': received.psrc, 'mac': received.hwsrc})
    
    return clients

def process_packet(packet, clients_ips):
   
    if packet.haslayer(DNS) and packet.haslayer(DNSQR):
        dns_layer = packet.getlayer(DNS)
        
        type_dns = "Requête" if dns_layer.qr == 0 else "Réponse"
        dns_query = packet.getlayer(DNSQR)
        try:
            qname = dns_query.qname.decode("utf-8")
        except AttributeError:
            qname = dns_query.qname

        
        src_ip = packet[IP].src if packet.haslayer(IP) else "N/A"
        src_mac = packet[Ether].src if packet.haslayer(Ether) else "N/A"

        
        if src_ip in clients_ips:
            print(f"{type_dns} DNS de {src_ip} ({src_mac}) : {qname}")

def start_dns_sniffing(clients_ips):
 
    print("Sniffing du trafic DNS en cours... (Appuyez sur CTRL-C pour arrêter)")
   
    sniff(filter="(udp port 53 or tcp port 53)", 
          prn=lambda packet: process_packet(packet, clients_ips), 
          store=False, 
          promisc=True)

def main():
  
    network = input("Entrez le réseau cible (ex: 192.168.1.0/24) : ")
    clients = scan_network(network)
    
   
    print("\nAdresse IP\t\tAdresse MAC")
    print("-----------------------------------------------")
    for client in clients:
        print(f"{client['ip']}\t\t{client['mac']}")

    
    clients_ips = [client['ip'] for client in clients]

    
    choix = input("\nVoulez-vous démarrer le sniffing des requêtes DNS pour les hôtes scannés ? (o/n) : ")
    if choix.lower() in ['o', 'oui', 'y', 'yes']:
        start_dns_sniffing(clients_ips)
    else:
        print("Sniffing du trafic DNS annulé.")

if __name__ == '__main__':
    main()
