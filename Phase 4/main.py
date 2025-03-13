import os
import Search_windows_interface
import Search_linux_interface
import Scanner_final_puch
def choose_network_interface(interfaces):
    """
    Permet à l'utilisateur de choisir une interface réseau parmi celles disponibles.
    """
    print("\nInterfaces réseau disponibles :")
    for idx, iface in enumerate(interfaces, start=1):
        print(f"{idx}. {iface}")
    choice = int(input("\nEntrez le numéro de l'interface réseau à utiliser : "))
    if 1 <= choice <= len(interfaces):
        
        return interfaces[choice - 1]
    else:
       print("Veuillez entrer un numéro valide.")

if os.name == 'nt':
    liste = Search_windows_interface.list_network_interfaces()
    print(choose_network_interface(liste))
  

    
else:

    liste = Search_linux_interface.list_network_interfaces()
    active_interface = choose_network_interface(liste)
    print(f"Votre interface active: {active_interface}")
    
    """
    >> >  METTRE LES FONCTIONNALITER DE SNIFFING IMPORTER ICI <<<
    """

Scanner_final_puch.analyser_reseau(Scanner_final_puch.get_network_address())