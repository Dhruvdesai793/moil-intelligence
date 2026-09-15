"""Reproduce the public-domain USGS measured laboratory reference, not a synthetic curve."""

import hashlib
import json
from pathlib import Path
import httpx

URL = "https://pubs.usgs.gov/of/2003/ofr-03-395/ASCII/M/pyrolusite_hs138.5705.asc"


def parse_spectrum(text):
    wavelengths, reflectance = [], []
    for line in text.splitlines()[16:]:
        columns = line.split()
        if len(columns) != 3 or "*" in line:
            continue
        wavelength, value, _ = map(float, columns)
        if 0.4 <= wavelength <= 2.5 and 0 <= value <= 1:
            wavelengths.append(round(wavelength * 1000, 4))
            reflectance.append(value)
    if len(wavelengths) < 100:
        raise ValueError("USGS spectrum is missing or not in the expected format.")
    return wavelengths, reflectance


if __name__ == "__main__":
    response = httpx.get(URL, timeout=60, follow_redirects=True)
    response.raise_for_status()
    wavelengths, reflectance = parse_spectrum(response.text)
    document = {
        "name": "Pyrolusite HS138.3B / USGS splib05a",
        "source": "USGS measured laboratory spectrum",
        "source_url": URL,
        "is_stub": False,
        "status": "measured_reference",
        "message": "Clark et al. 2003, USGS Open-File Report 03-395; sample from Villa Grove, Colorado.",
        "wavelengths_nm": wavelengths,
        "reflectance": reflectance,
        "sha256_original": hashlib.sha256(response.content).hexdigest(),
    }
    path = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "resources"
        / "pyrolusite_hs138.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n")
    print(f"Stored {len(wavelengths)} measured samples: {path.name}")
