import os
import Search_windows_interface
if os.name == 'nt':
    interfaces = Search_windows_interface.list_network_interfaces()
    chosen_interface = Search_windows_interface.choose_network_interface(interfaces)
    print(f"Interface réseau choisie : {chosen_interface}")
else:
    print('Linux')