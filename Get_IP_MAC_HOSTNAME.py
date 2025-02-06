import ipaddress
import scapy.all as scapy
import socket


def analyser_reseau(ip_avec_masque):
    try:
        # Analyser l'adresse IP avec le masque
        reseau = ipaddress.IPv4Network(ip_avec_masque, strict=False)
        print(f"\n[INFO] Réseau détecté: {reseau}\n")

        # Obtenir la plage d'adresses IP
        ips = [str(ip) for ip in reseau.hosts()]

        # Requête ARP
        requete_arp = scapy.ARP(pdst=ips)
        diffusion = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        requete_arp_diffusion = diffusion / requete_arp

        # Temps d'attente minimal
        reponses = scapy.srp(requete_arp_diffusion, timeout=0.5, verbose=False)[0]

        # Affichage de l'entête
        print(f"Appareils trouvés dans le réseau {reseau}:")
        print("-" * 80)
        print(f"{'IP':<20} {'MAC':<20} {'Nom d\'hôte':<30}")
        print("-" * 80)

        # Compteur pour le nombre total d'hôtes
        compteur_hotes = 0

        # Affichage des résultats
        for envoye, recu in reponses:
            try:
                # Tente de résoudre le nom d'hôte
                nom_hote = socket.gethostbyaddr(recu.psrc)[0]
            except (socket.herror, socket.gaierror):
                # Si le nom d'hôte n'est pas trouvé, afficher une valeur par défaut
                nom_hote = "Inconnu"

            # Affichage des informations sur chaque hôte
            print(f"{recu.psrc:<20} {recu.hwsrc:<20} {nom_hote:<30}")
            compteur_hotes += 1

        # Affichage du nombre total d'hôtes
        print("-" * 80)
        print(f"[INFO] Nombre total d'hôtes trouvés: {compteur_hotes}")

    except Exception as e:
        print(f"[ERREUR] {e}")


if __name__ == "__main__":
    # Utilisation d'une IP avec un masque /20
    analyser_reseau("10.100.15.195/20")