"""Phone model detection from User-Agent strings."""
from user_agents import parse
import re
from typing import Dict, Optional

def parse_phone_model(ua: str) -> Dict[str, Optional[str]]:
    ua = parse(ua or "")

    return {
        "os_family": ua.os.family or None,
        "browser_family": ua.browser.family or None,
        "device_family": ua.device.family or None,
        "device_brand": ua.device.brand or None,
        "device_model": ua.device.model or None
    }

def summarize_ua(ua):
    """
    Turn ua-parser / user_agents object into a short, human-readable string.
    Example output: "Android · Chrome · Samsung SM-G973F"
    """
    ua = parse(ua or "")
    os_family      = ua.os.family
    browser_family = ua.browser.family
    device_family  = getattr(ua.device, "family", None)
    device_brand   = getattr(ua.device, "brand", None)
    device_model   = getattr(ua.device, "model", None)

    # Values we consider "default" / not useful
    boring = {None, "", "Other", "Generic Smartphone", "Generic Tablet", "Generic Feature Phone"}

    parts = []

    # OS
    if os_family not in boring:
        parts.append(os_family)

    # Browser
    if browser_family not in boring:
        parts.append(browser_family)

    # Device
    device_bits = []
    if device_brand not in boring:
        device_bits.append(device_brand)
    # Only add model if it's not just a repeat of brand
    if device_model not in boring and device_model != device_brand:
        device_bits.append(device_model)
    # Fallback to device_family if we have nothing else
    if not device_bits and device_family not in boring:
        device_bits.append(device_family)

    if device_bits:
        parts.append(" ".join(device_bits))

    return " ".join(parts)

if __name__ == "__main__":
    samples = [
    "Mozilla/5.0 (Linux; Android 11; Pixel 4 XL Build/RQ2A.210405.005) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/29.0 Chrome/136.0.0.0 Mobile Safari/537.36"
    ]

    for s in samples:
        print(s)
        print(summarize_ua(s))
        print()