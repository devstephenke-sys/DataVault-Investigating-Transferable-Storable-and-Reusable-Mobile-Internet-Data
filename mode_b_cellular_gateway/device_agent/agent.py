"""
DataVault Device Agent
Linux gateway agent for cellular modem and Wi-Fi hotspot management
"""
import asyncio
import subprocess
import json
import logging
from datetime import datetime
from typing import Optional, Dict
import httpx

# Configuration
DATAVAULT_BACKEND_URL = "http://localhost:8000"
DEVICE_ID = "DV-001-ABCD"
HEARTBEAT_INTERVAL = 60  # seconds

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NetworkManager:
    """Manages network interfaces and routing"""

    @staticmethod
    async def get_interface_status(interface: str) -> Dict:
        """Get status of a network interface"""
        try:
            result = subprocess.run(
                ['ip', 'link', 'show', interface],
                capture_output=True,
                text=True
            )
            return {
                'interface': interface,
                'status': result.stdout,
                'active': 'UP' in result.stdout
            }
        except Exception as e:
            logger.error(f"Error getting interface status: {e}")
            return {'interface': interface, 'error': str(e)}

    @staticmethod
    async def configure_firewall():
        """Configure nftables firewall"""
        try:
            # Basic NAT and forwarding rules
            rules = [
                "# Clear existing rules",
                "nft flush ruleset",
                "",
                "# Create tables",
                "nft add table nat",
                "nft add table filter",
                "",
                "# NAT for masquerading",
                "nft add chain nat postrouting { type nat hook postrouting priority 100 \\; }",
                "nft add rule nat postrouting oifname \"wwan0\" masquerade",
                "",
                "# Allow forwarding",
                "nft add chain filter forward { type filter hook forward priority 0 \\; }",
                "nft add rule filter forward iifname \"wlan0\" oifname \"wwan0\" accept",
                "nft add rule filter forward iifname \"wwan0\" oifname \"wlan0\" accept state related,established"
            ]

            for rule in rules:
                if rule and not rule.startswith('#'):
                    subprocess.run(rule, shell=True, check=True)

            logger.info("Firewall configured successfully")
            return True
        except Exception as e:
            logger.error(f"Error configuring firewall: {e}")
            return False

class ModemManager:
    """Manages cellular modem"""

    @staticmethod
    async def get_modem_status() -> Dict:
        """Get cellular modem status"""
        try:
            # Use ModemManager CLI (mmcli)
            result = subprocess.run(
                ['mmcli', '-m', '--output-json'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {'error': 'Modem not available'}
        except Exception as e:
            logger.error(f"Error getting modem status: {e}")
            return {'error': str(e)}

    @staticmethod
    async def connect_modem(apn: str = "default") -> bool:
        """Connect cellular modem to network"""
        try:
            # Use ModemManager to connect
            result = subprocess.run(
                ['mmcli', '-m', '--simple-connect', f'apn={apn}'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("Modem connected successfully")
                return True
            else:
                logger.error(f"Modem connection failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error connecting modem: {e}")
            return False

    @staticmethod
    async def get_signal_strength() -> Dict:
        """Get cellular signal strength"""
        try:
            result = subprocess.run(
                ['mmcli', '-m', '--signal-get'],
                capture_output=True,
                text=True
            )

            # Parse signal information
            signal_info = {}
            for line in result.stdout.split('\n'):
                if 'rssi' in line.lower():
                    signal_info['rssi'] = line.split(':')[1].strip()
                elif 'rsrp' in line.lower():
                    signal_info['rsrp'] = line.split(':')[1].strip()

            return signal_info
        except Exception as e:
            logger.error(f"Error getting signal strength: {e}")
            return {'error': str(e)}

class HotspotManager:
    """Manages Wi-Fi hotspot"""

    @staticmethod
    async def start_hotspot(ssid: str = "DataVault", password: str = "datavault123"):
        """Start Wi-Fi hotspot"""
        try:
            # Configure hostapd
            config = f"""
interface=wlan0
driver=nl80211
ssid={ssid}
hw_mode=g
channel=6
wmm=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
rsn_pairwise=CCMP
"""

            with open('/tmp/hostapd.conf', 'w') as f:
                f.write(config)

            # Start hostapd
            subprocess.run(['hostapd', '-B', '/tmp/hostapd.conf'], check=True)

            # Start dnsmasq for DHCP
            subprocess.run([
                'dnsmasq',
                '--interface=wlan0',
                '--dhcp-range=192.168.10.2,192.168.10.100,12h',
                '--dhcp-option=3,192.168.10.1'
            ], check=True)

            logger.info(f"Hotspot started: {ssid}")
            return True
        except Exception as e:
            logger.error(f"Error starting hotspot: {e}")
            return False

    @staticmethod
    async def stop_hotspot():
        """Stop Wi-Fi hotspot"""
        try:
            subprocess.run(['killall', 'hostapd'], check=True)
            subprocess.run(['killall', 'dnsmasq'], check=True)
            logger.info("Hotspot stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping hotspot: {e}")
            return False

class EntitlementManager:
    """Manages entitlements and token storage"""

    def __init__(self, backend_url: str, device_id: str):
        self.backend_url = backend_url
        self.device_id = device_id
        self.current_entitlement = None

    async def validate_entitlement(self, entitlement_id: str, token: str) -> Dict:
        """Validate entitlement with backend"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.backend_url}/api/v1/entitlement/validate",
                    json={
                        "entitlement_id": entitlement_id,
                        "device_id": self.device_id,
                        "token": token
                    },
                    timeout=10.0
                )
                return response.json()
            except Exception as e:
                logger.error(f"Error validating entitlement: {e}")
                return {'valid': False, 'error': str(e)}

    async def report_usage(self, entitlement_id: str, volume_consumed: int, session_id: str):
        """Report usage to backend"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.backend_url}/api/v1/entitlement/report-usage",
                    json={
                        "entitlement_id": entitlement_id,
                        "device_id": self.device_id,
                        "volume_consumed": volume_consumed,
                        "session_id": session_id,
                        "reported_at": datetime.utcnow().isoformat()
                    },
                    timeout=10.0
                )
                return response.json()
            except Exception as e:
                logger.error(f"Error reporting usage: {e}")
                return {'error': str(e)}

class DeviceAgent:
    """Main device agent"""

    def __init__(self):
        self.network_manager = NetworkManager()
        self.modem_manager = ModemManager()
        self.hotspot_manager = HotspotManager()
        self.entitlement_manager = EntitlementManager(DATAVAULT_BACKEND_URL, DEVICE_ID)
        self.running = False

    async def send_heartbeat(self):
        """Send heartbeat to backend"""
        async with httpx.AsyncClient() as client:
            try:
                # Get system stats
                cpu_usage = 50.0  # Mock value
                memory_usage = 60.0  # Mock value
                disk_usage = 40.0  # Mock value
                uptime = 3600  # Mock value

                response = await client.post(
                    f"{DATAVAULT_BACKEND_URL}/api/v1/devices/{DEVICE_ID}/heartbeat",
                    json={
                        'cpu_usage': cpu_usage,
                        'memory_usage': memory_usage,
                        'disk_usage': disk_usage,
                        'uptime_seconds': uptime
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    logger.debug("Heartbeat sent successfully")
                else:
                    logger.warning(f"Heartbeat failed: {response.status_code}")
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")

    async def monitor_traffic(self):
        """Monitor network traffic and enforce quota"""
        # This would use nftables to count bytes
        # For prototype, we just log
        logger.info("Traffic monitoring active")

    async def run(self):
        """Main agent loop"""
        self.running = True
        logger.info("Device agent starting")

        while self.running:
            try:
                # Send heartbeat
                await self.send_heartbeat()

                # Monitor traffic
                await self.monitor_traffic()

                # Wait for next interval
                await asyncio.sleep(HEARTBEAT_INTERVAL)

            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def initialize(self):
        """Initialize the device"""
        logger.info("Initializing device agent")

        # Check modem status
        modem_status = await self.modem_manager.get_modem_status()
        logger.info(f"Modem status: {modem_status}")

        # Connect modem
        await self.modem_manager.connect_modem()

        # Configure firewall
        await self.network_manager.configure_firewall()

        # Start hotspot
        await self.hotspot_manager.start_hotspot()

        logger.info("Device agent initialized")

    async def shutdown(self):
        """Shutdown the device agent"""
        self.running = False
        await self.hotspot_manager.stop_hotspot()
        logger.info("Device agent shut down")

async def main():
    """Main entry point"""
    agent = DeviceAgent()

    try:
        await agent.initialize()
        await agent.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
