from flask import Flask, request, redirect, render_template
import requests
import os
from ipaddress import ip_network, ip_address

app = Flask(__name__)


# API keys for IP geolocation services (replace with your actual keys)
IP_API_KEY = os.environ.get("IP_API_KEY", "YOUR_IP_API_KEY")
IPINFO_TOKEN = os.environ.get("IPINFO_TOKEN", "YOUR_IPINFO_TOKEN")

# List of known VPN provider ASN prefixes (can be extensive and needs updating)
KNOWN_VPN_ASNS = [
    "AS13335",  # Cloudflare
    "AS14061",  # DigitalOcean
    "AS20473",  # The Constant Company, LLC
    "AS13335",  #cloudlflare asn
    "AS15169",  # Google LLC
    "AS16509",  # Amazon.com, Inc.
    "AS32934",  # Facebook, Inc.
    "AS36351",  # SoftLayer Technologies Inc.
    "AS395282",  # OVH SAS
    "AS395561",  # Linode, LLC
    "AS40676",  # Amazon Technologies Inc.
    "AS45102",  # Tencent Cloud Computing (Beijing) Co., Ltd.
    "AS4808",  # China Unicom
    "AS4837",  # China Telecom (Group) Corporation
    "AS55836",  # Alibaba (China) Technology Co., Ltd.
    "AS56040",  # Alibaba Cloud Computing Ltd. (Aliyun)
    "AS58073",  # Tencent Building, Kejizhongyi Avenue
    "AS60781",  # Microsoft Azure
    "AS63949",  # Oracle Corporation
    "AS6939",  # Hurricane Electric, Inc.
    "AS8075",  # Microsoft Corporation

    # Add more ASNs of known VPN providers, hosting providers, etc.
]

# List of known VPN IP address ranges (very difficult to maintain)
KNOWN_VPN_RANGES = [
    ip_network("130.41.227.171/32"),
    ip_network("103.2.160.0/20"),
    ip_network("192.168.1.0/24"),  # Example private range
    ip_network("172.16.0.0/12"),   # Example private range
    ip_network("127.0.0.0/8"),    # Example loopback range
    ip_network("10.0.0.0/8"),      # Example private range
    # Add more ranges as needed
]

def is_likely_vpn(ip_address_str):
    """Attempts to detect if the IP address is likely associated with a VPN."""
    try:
        # Convert the IP address string to an ip_address object
        ip_address_obj = ip_address(ip_address_str)

        # 1. Check against known VPN ASN (Autonomous System Number)
        try:
            response = requests.get(f"https://ipapi.co/{ip_address_str}/asn/", timeout=2)
            if response.status_code == 200:
                asn = response.text.strip()
                if asn in KNOWN_VPN_ASNS:
                    print(f"Likely VPN: ASN {asn} found in known VPN ASNs.")
                    return True
        except requests.exceptions.RequestException as e:
            print(f"Error checking ASN: {e}")

        # 2. Check against known VPN IP ranges (very limited effectiveness)
        for vpn_range in KNOWN_VPN_RANGES:
            if ip_address_obj in vpn_range:
                print(f"Likely VPN: IP {ip_address_obj} in known VPN range {vpn_range}.")
                return True

        # 3. Use IP geolocation services to look for VPN indicators
        try:
            # Using ipinfo.io (requires a token)
            if IPINFO_TOKEN != "YOUR_IPINFO_TOKEN":
                response = requests.get(f"https://ipinfo.io/{ip_address_str}/json?token={IPINFO_TOKEN}", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    if "privacy" in data and data["privacy"].get("vpn", False):
                        print(f"Likely VPN: ipinfo.io reports VPN usage.")
                        return True
                    if "company" in data and any(keyword in data["company"].get("name", "").lower() for keyword in ["vpn", "hosting", "cloud"]):
                        print(f"Likely VPN: Company name suggests hosting/VPN.")
                        return True

            # Using ipapi.co (no token required for basic usage, but rate limits apply)
            elif IP_API_KEY != "YOUR_IP_API_KEY":
                response = requests.get(f"https://ipapi.co/{ip_address_str}/json/", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("security", {}).get("is_vpn", False):
                        print(f"Likely VPN: ipapi.co reports VPN usage.")
                        return True
                    if data.get("org", "").lower() in ["amazon web services", "google cloud", "microsoft azure", "digitalocean", "linode"]:
                        print(f"Likely VPN: Organization suggests hosting/VPN.")
                        return True

        except requests.exceptions.RequestException as e:
            print(f"Error checking geolocation services: {e}")
        except Exception as e:
            print(f"Error parsing geolocation data: {e}")

    except ValueError as e:
        print(f"Invalid IP address: {ip_address_str}. Error: {e}")

    return False

@app.route('/')
def index():
    # Get the real IP address from the X-Forwarded-For header
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    # If there are multiple IPs in the header, take the first one (the client's IP)
    user_ip = user_ip.split(',')[0].strip()
    print(f"User IP: {user_ip}")

    if is_likely_vpn(user_ip):
        print("VPN usage suspected. Redirecting...")
        return redirect("/vpn-detected")
    else:
        print("No VPN suspected. Serving normal content.")
        return render_template("normal_content.html", user_ip=user_ip)

@app.route('/vpn-detected')
def vpn_detected():
    return render_template("vpn_detected.html")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)