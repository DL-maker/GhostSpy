import platform  # Import module to detect the operating system
import subprocess  # Import module to run system commands
import re  # Import module for regular expression matching

def get_connection_info():  # Define function to gather Wi-Fi connection info
    system = platform.system()  # Get the current OS (Windows or Linux)

    result = {  # Initialize default Wi-Fi info dictionary
        "protocol_used": "Wi-Fi",  # Set default protocol to Wi-Fi
        "wifi_standard": None,  # Placeholder for Wi-Fi standard (e.g., 802.11ac)
        "network_protocols": ["DHCP", "ARP", "TCP/IP"],  # List standard protocols
        "security_protocol": None,  # Placeholder for security protocol (e.g., WPA2)
        "channel_used": None  # Placeholder for frequency band (2.4/5 GHz)
    }

    if system == "Windows":  # Check if the OS is Windows
        try:  # Attempt to execute command to get Wi-Fi details
            output = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], encoding='utf-8')  # Run netsh command
            result = output  # Store raw output (string) for debugging/logging
        except subprocess.CalledProcessError:  # Handle command execution errors
            pass  # Silently ignore errors


    elif system == "Linux":  # Check if the OS is Linux
        try:  # Attempt to execute iwconfig for Wi-Fi details
            output = subprocess.check_output(['iwconfig'], encoding='utf-8', stderr=subprocess.DEVNULL)  # Run iwconfig command

            match_standard = re.search(r"IEEE (\d+\.\d+\w*)", output)  # Extract Wi-Fi standard (e.g., 802.11ac)
            if match_standard:  # If a standard is found
                result["wifi_standard"] = match_standard.group(1)  # Update wifi_standard

            try:  # Attempt to get security protocol via nmcli
                nmcli_output = subprocess.check_output(['nmcli', '-t', '-f', 'active,ssid,security', 'dev', 'wifi'], encoding='utf-8')  # Run nmcli command
                for line in nmcli_output.splitlines():  # Process nmcli output lines
                    if line.startswith("yes"):  # Look for active connections
                        parts = line.split(":")  # Split line into parts
                        if len(parts) >= 3:  # Ensure enough parts for security
                            result["security_protocol"] = parts[2]  # Update security_protocol
                        break  # Exit loop after first active connection
            except:  # Handle nmcli command errors
                pass  # Silently ignore errors

            try:  # Attempt to get channel info via iwlist
                scan_output = subprocess.check_output(['iwlist', 'scanning'], encoding='utf-8', stderr=subprocess.DEVNULL)  # Run iwlist scanning
                match_channel = re.search(r"Channel:(\d+)", scan_output)  # Extract channel number
                if match_channel:  # If a channel is found
                    channel = int(match_channel.group(1))  # Convert channel to integer
                    if channel <= 14:  # Check if channel is in 2.4 GHz range
                        result["channel_used"] = "2.4 GHz"  # Set 2.4 GHz band
                    else:  # Channel is in 5 GHz range
                        result["channel_used"] = "5 GHz"  # Set 5 GHz band
            except:  # Handle iwlist command errors
                pass  # Silently ignore errors

        except subprocess.CalledProcessError:  # Handle iwconfig command errors
            pass  # Silently ignore errors

    return result  # Return the Wi-Fi info (dictionary or string on Windows)

import re  # Re-import re module (redundant, already imported)

def parse_text_to_dict(text):  # Define function to parse text into a dictionary
    text = text.strip().replace('{', '').replace('}', '').replace(',', '')  # Clean text by removing braces and commas
    lines = [line.strip() for line in text.split('\n') if line.strip()]  # Split into non-empty lines
    
    result = {}  # Initialize empty dictionary for parsed data
    current_dict = result  # Track current dictionary being populated
    stack = [result]  # Stack to handle nested dictionaries
    
    pair_pattern = re.compile(r'^\s*"?([^":]+)"?\s*:\s*([^,\n]+)$')  # Regex for key-value pairs (e.g., "key: value")
    dict_pattern = re.compile(r'^\s*"?([^":]+)"?\s*:\s*$')  # Regex for dictionary keys (e.g., "key:")
    
    for line in lines:  # Process each line
        dict_match = dict_pattern.match(line)  # Check if line starts a new dictionary
        if dict_match:  # If a new dictionary is detected
            key = dict_match.group(1).strip()  # Extract the key
            current_dict[key] = {}  # Create new dictionary for the key
            stack.append(current_dict[key])  # Add to stack
            current_dict = current_dict[key]  # Update current dictionary
            continue  # Move to next line
        
        pair_match = pair_pattern.match(line)  # Check if line is a key-value pair
        if pair_match:  # If a key-value pair is detected
            key = pair_match.group(1).strip()  # Extract the key
            value = pair_match.group(2).strip()  # Extract the value
            current_dict[key] = value  # Add key-value to current dictionary
            continue  # Move to next line
        
        if not line.strip():  # Handle empty lines (end of nested dictionary)
            if len(stack) > 1:  # Check if there are nested dictionaries
                stack.pop()  # Remove last dictionary from stack
                current_dict = stack[-1]  # Revert to previous dictionary
    
    return result  # Return the parsed dictionary



system = platform.system()  # Get the current OS
if system == "Windows":  # If OS is Windows
    conn_info = get_connection_info()  # Get raw Wi-Fi info (string)
    conn_info = parse_text_to_dict(conn_info)  # Parse string to dictionary
elif system == "Linux":  # If OS is Linux
    conn_info = get_connection_info()  # Get Wi-Fi info (dictionary) 