# pysonde
Fetches real-time ionospheric data from the DIAS Ionostream API and provides amateur radio band recommendations based on MUF (Maximum Usable Frequency), foF2 (Critical frequency-NVIS), and fmin values for DX planning and propagation forecasting!

## How It Works
- Queries DIAS Ionostream API for ionogram scaled auto-observations (SAO)
- Finds latest valid measurement with good MUF+foF2
- Calculates band status:

    🟢 OPEN: Band center < 85% MUF (DX propagation)
  
    🟢 NVIS: Band center < 130% foF2 (near-vertical skywave)
  
    🟡 MARGINAL: Band center < 95% MUF
  
    🔴 ABSORBED: fmin > band low frequency (D-layer absorption)
  
    🔴 CLOSED: Above MUF

### Installation
```bash
git clone https://github.com/nov3mb3r/pysonde.git
cd pysonde
chmod +x pysonde.py
pip install requests
python3 pysonde.py
```

## Quick Start
```bash
# Get the latest data from Athens, Greece station
python3 pysonde.py

# Try different stations
python3 pysonde.py -s EB040      # Ebre, Spain
python3 pysonde.py -s SO148      # Sopron, Hungary

# Time-specific data
python3 pysonde.py -lb 42m       # Closest to 42 minutes ago
python3 pysonde.py -lb 6h        # Closest to 6 hours ago
```

## Troubleshooting
"No data for station":
- Try larger lookback: ./pysonde.py -lb 1d
- Try different station: ./pysonde.py -s EB040

"No valid data":
- Ionosonde temporarily offline
- Nighttime - some parameters unavailable

# Acknowledgements
**Heartfelt thanks to the National Observatory of Athens** for their commitment to open science and public access to space weather data. pysonde uses real-time ionospheric data from **DIAS (Digital Ionogram Archive Service)**. The DIAS team has created a pan-European network of digital ionosondes delivering real-time ionospheric specification essential to the amateur radio service for propagation forecasting. By making this critical HF data freely accessible to researchers, operators, and radio enthusiasts worldwide can plan DX windows and emergency communications with unprecedented accuracy.

**DISCLAIMER:** 

- This tool fetches and displays ionospheric data from DIAS public API for non commercial use. 
- Users must comply with **DIAS Terms of Use** at https://dias.space.noa.gr/dias/ui/pages/rules.
