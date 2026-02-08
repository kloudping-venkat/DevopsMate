"""
Hostname subcommand - show resolved hostname.
Similar to Datadog's hostname command.
"""

import socket
import platform


def cmd_hostname(args) -> None:
    """Show resolved hostname."""
    hostname = socket.gethostname()
    fqdn = socket.getfqdn()
    
    try:
        # Try to get canonical hostname
        canonical = socket.gethostbyaddr(socket.gethostname())[0]
    except:
        canonical = hostname
    
    print("=== Hostname Information ===")
    print(f"Hostname: {hostname}")
    print(f"FQDN: {fqdn}")
    print(f"Canonical: {canonical}")
    print(f"Platform: {platform.system()} {platform.release()}")
    
    if args.verbose:
        try:
            # Get IP addresses
            ip_addrs = socket.gethostbyname_ex(hostname)[2]
            print(f"\nIP Addresses:")
            for ip in ip_addrs:
                print(f"  - {ip}")
        except:
            pass
