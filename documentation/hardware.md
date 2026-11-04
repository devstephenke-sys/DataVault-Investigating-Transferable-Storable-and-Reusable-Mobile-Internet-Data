# DataVault Hardware Requirements

## Overview

This document specifies the hardware requirements for the DataVault physical device (Mode B: Real Cellular Gateway).

## Minimum Requirements

### Processor
- **Architecture:** ARM Cortex-A53 or x86-64
- **Cores:** 2 cores minimum
- **Clock Speed:** 1.2 GHz minimum
- **Examples:** Raspberry Pi 4 (2GB), Intel NUC

### Memory
- **RAM:** 2GB minimum
- **Type:** DDR4 or LPDDR4
- **Recommendation:** 4GB for better performance

### Storage
- **Type:** eMMC or microSD
- **Capacity:** 16GB minimum
- **Recommendation:** 64GB or more for logs and data

### Cellular Modem
- **Standard:** 4G LTE (Cat 4 or higher)
- **Frequency Bands:** 3GPP Band 1, 3, 5, 8, 20, 28, 40 (Kenya)
- **SIM Support:** Standard SIM slot
- **Examples:**
  - Quectel EC25-AF
  - Sierra Wireless EM7565
  - Fibocom L850-GL

### Wi-Fi
- **Standard:** 802.11ac (Wi-Fi 5)
- **Frequency:** 2.4 GHz and 5 GHz dual-band
- **Antennas:** 2x2 MIMO
- **Examples:** Raspberry Pi 4 built-in Wi-Fi, Intel AX200

### Power
- **Input:** 5V DC
- **Current:** 2A minimum
- **Connector:** USB-C or barrel jack
- **Recommendation:** Battery backup for portability

## Recommended Requirements

### Processor
- **Architecture:** ARM Cortex-A72 or x86-64
- **Cores:** 4 cores
- **Clock Speed:** 1.5 GHz or higher
- **Examples:** Raspberry Pi 5 (4GB), Intel Core i3

### Memory
- **RAM:** 4GB or more
- **Type:** DDR4 or LPDDR4

### Storage
- **Type:** NVMe SSD or eMMC
- **Capacity:** 64GB or more
- **Speed:** 500 MB/s read/write

### Cellular Modem
- **Standard:** 4G LTE Advanced Pro or 5G NR
- **SIM Support:** eSIM (GSMA SGP.22 compliant)
- **Examples:**
  - Quectel RM500Q-GL (5G)
  - Sierra Wireless EM9191 (5G)
  - Fibocom FM650-GL (5G)

### Wi-Fi
- **Standard:** 802.11ax (Wi-Fi 6)
- **Frequency:** 2.4 GHz, 5 GHz, 6 GHz tri-band
- **Antennas:** 4x4 MIMO
- **Examples:** Intel AX210, MediaTek MT7921

### Power
- **Input:** USB-C Power Delivery (PD)
- **Current:** 3A
- **Battery:** 10,000 mAh Li-ion for portability
- **Charging:** USB-C PD charging

### Security
- **Secure Element:** TPM 2.0 or secure element
- **Boot Security:** Secure boot, dm-verity
- **Encryption:** Hardware-accelerated AES

## Specific Hardware Recommendations

### Option 1: Raspberry Pi 5 (Cost-Effective)
- **CPU:** Broadcom BCM2712, Cortex-A76, 2.4 GHz quad-core
- **RAM:** 4GB or 8GB
- **Storage:** 64GB microSD or NVMe via HAT
- **Wi-Fi:** 802.11ac (built-in)
- **Cellular:** Quectel EC25-AF USB modem
- **Power:** USB-C 5V/5A
- **Cost:** ~$80 (board) + $40 (modem) + $30 (storage) = ~$150

### Option 2: Mini PC (Performance)
- **CPU:** Intel N100 or Core i3
- **RAM:** 8GB DDR4
- **Storage:** 256GB NVMe SSD
- **Wi-Fi:** Intel AX210 (Wi-Fi 6)
- **Cellular:** Sierra Wireless EM7565 M.2 modem
- **Power:** 12V DC adapter
- **Cost:** ~$200 (mini PC) + $60 (modem) = ~$260

### Option 3: Custom Embedded (Production)
- **CPU:** MediaTek MT7622A or similar
- **RAM:** 2GB DDR3
- **Storage:** 16GB eMMC
- **Wi-Fi:** MediaTek MT7915 (Wi-Fi 6)
- **Cellular:** Quectel RM500Q-GL (5G)
- **Power:** 12V DC
- **Cost:** ~$100 (BOM at scale)

## Peripheral Requirements

### Antennas
- **Cellular:** LTE/5G external antenna (SMA connectors)
- **Wi-Fi:** 2.4 GHz and 5 GHz antennas
- **Gain:** 3-5 dBi
- **Mounting:** Magnetic or pole mount

### Enclosure
- **Material:** ABS plastic or aluminum
- **IP Rating:** IP54 (dust and splash resistant)
- **Mounting:** Desktop or wall mount
- **Cooling:** Passive cooling or low-noise fan
- **Indicators:** Power, Wi-Fi, Cellular, Status LEDs

### SIM Card
- **Form Factor:** Standard SIM (for initial testing)
- **Form Factor:** eSIM (for production)
- **Support:** Multi-profile eSIM for multiple operators

### Cables
- **Cellular Antenna:** SMA to SMA, 1m
- **Wi-Fi Antenna:** U.FL to RP-SMA pigtail
- **Power:** USB-C cable, 2m

## Software Compatibility

### Operating Systems
- **OpenWrt 23.05+** (recommended for router-like functionality)
- **Ubuntu Server 22.04 LTS** (easier development)
- **Debian 12** (stable option)

### Required Kernel Modules
- `qmi_wwan` - Qualcomm MSM Interface (WWAN)
- `usbnet` - USB network devices
- `cdc_ether` - CDC Ethernet
- `hostapd` - Wi-Fi access point
- `nf_tables` - Netfilter tables (firewall)
- `bridge` - Network bridging

### Required Packages
- **ModemManager** - Cellular modem management
- **NetworkManager** - Network connection management
- **hostapd** - Wi-Fi access point daemon
- **dnsmasq** - DHCP and DNS server
- **iptables-nftables** - Firewall
- **python3** - Device agent runtime
- **python3-pip** - Python package manager

## Environmental Requirements

### Operating Temperature
- **Range:** 0°C to 40°C (32°F to 104°F)
- **Storage:** -20°C to 60°C (-4°F to 140°F)

### Humidity
- **Operating:** 10% to 90% non-condensing
- **Storage:** 5% to 95% non-condensing

### Altitude
- **Maximum:** 3,000 meters (9,843 feet)

### Power Supply
- **Voltage:** 100-240V AC input (for power adapter)
- **Frequency:** 50/60 Hz
- **Input:** 5V DC (for device)

## Regulatory Compliance

### Kenya
- **Type Approval:** Required by Communications Authority of Kenya (CA)
- **EMC Compliance:** IEC 61000-6-3
- **Safety:** IEC 60950-1
- **RF Exposure:** IEC 62311

### International
- **CE Marking:** European Union
- **FCC Part 15:** United States
- **IC RSS-210:** Canada

## Supply Chain

### Component Sourcing
- **Raspberry Pi:** Official distributors (RS Components, Element14)
- **Cellular Modems:** Mouser, Digi-Key, Alibaba
- **Wi-Fi Modules:** Intel, MediaTek distributors
- **Enclosures:** Custom fabrication or off-the-shelf

### Lead Times
- **Raspberry Pi:** 1-2 weeks
- **Cellular Modems:** 2-4 weeks
- **Custom PCB:** 4-8 weeks
- **Enclosure Tooling:** 8-12 weeks

### Minimum Order Quantities
- **Off-the-shelf:** 1 unit
- **Custom Enclosure:** 100-500 units
- **Custom PCB:** 100-1000 units

## Bill of Materials (BOM) - Raspberry Pi 5 Configuration

| Item | Description | Quantity | Unit Cost (USD) | Total (USD) |
|------|-------------|----------|-----------------|-------------|
| Raspberry Pi 5 | 4GB RAM | 1 | $60 | $60 |
| microSD Card | 64GB Class 10 | 1 | $10 | $10 |
| Quectel EC25-AF | 4G LTE USB Modem | 1 | $40 | $40 |
| LTE Antenna | SMA Male, 3 dBi | 1 | $8 | $8 |
| Wi-Fi Antenna | RP-SMA, 2.4/5 GHz | 2 | $5 | $10 |
| Enclosure | ABS plastic, IP54 | 1 | $15 | $15 |
| Power Supply | USB-C 5V/5A | 1 | $12 | $12 |
| Cables | USB-C, SMA pigtail | 1 set | $10 | $10 |
| SIM Card | Standard SIM | 1 | $2 | $2 |
| **Total** | | | | **$157** |

## Development Hardware

### For Development and Testing
- Development laptop (Windows/Linux/Mac)
- Test SIM cards (multiple operators for testing)
- USB-to-Serial adapter (for modem debugging)
- Network analyzer (for troubleshooting)
- Power meter (for power consumption testing)

### For Production Testing
- RF test equipment (signal generator, spectrum analyzer)
- Environmental chamber (temperature/humidity testing)
- EMI testing chamber (EMC compliance)
- Drop testing equipment

## Future Upgrades

### 5G Support
- Replace 4G modem with 5G modem
- Update antenna to support 5G bands
- Ensure power supply can handle higher power consumption

### Wi-Fi 7 Support
- Upgrade to Wi-Fi 7 module when available
- Update antenna for 6 GHz band
- Ensure CPU can handle higher throughput

### Edge Computing
- Add AI accelerator (e.g., Google Coral)
- Enable local data processing
- Implement edge caching

## Cost Scaling

### Prototype (1-10 units)
- Hardware cost: $150-200 per unit
- Assembly cost: $50 per unit
- Total: $200-250 per unit

### Pilot (100-500 units)
- Hardware cost: $120-150 per unit
- Assembly cost: $20 per unit
- Tooling amortization: $10 per unit
- Total: $150-180 per unit

### Production (1000+ units)
- Hardware cost: $80-100 per unit
- Assembly cost: $10 per unit
- Tooling amortization: $5 per unit
- Total: $95-115 per unit
