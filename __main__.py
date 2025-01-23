import os
import Search_windows_interface
if os.name == 'nt':
    Search_windows_interface.list_network_interfaces()
else:
    print('Linux')