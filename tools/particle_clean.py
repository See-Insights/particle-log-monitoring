#!/usr/bin/env python3

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: particle_clean.py <product_id> [--color] [--verbose]", file=sys.stderr)
    sys.exit(1)

PRODUCT_ID = sys.argv[1]
USE_COLOR = "--color" in sys.argv
VERBOSE = "--verbose" in sys.argv

BASE = Path.home() / "ParticleLogs"
INVENTORY = BASE / "inventory" / "devices.csv"

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

SLOW_CONNECT_WARN = 60
SLOW_CONNECT_CRIT = 180

def color(text, c):
    if not USE_COLOR:
        return text
    return f"{c}{text}{RESET}"

device_map = {}

try:
    with INVENTORY.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("product_id") == PRODUCT_ID:
                device_map[row.get("device_id", "")] = row.get("device_name", "")
except FileNotFoundError:
    print(f"ERROR: inventory file not found: {INVENTORY}", file=sys.stderr)
    sys.exit(1)

def local_ts(iso_ts):
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""

def parse_data(data):
    if data is None or data == "":
        return ""

    try:
        parsed = json.loads(data)

        # Normal case:
        # '{"version":"14.0.0","alert":0}'
        if isinstance(parsed, dict):
            return parsed

        # Double-encoded case:
        # "\"{\\\"version\\\":\\\"14.0.0\\\"}\""
        if isinstance(parsed, str):
            try:
                nested = json.loads(parsed)
                if isinstance(nested, dict):
                    return nested
            except Exception:
                pass

            return parsed

    except Exception:
        pass

    return data

def num_value(value, default=0):
    try:
        return float(value)
    except Exception:
        return default

def fmt_num(value, decimals=1):
    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return str(value)

def is_report_event(name):
    return name.startswith("Ubidots-")

def is_interesting_report(parsed):
    alerts = num_value(parsed.get("alerts", 0))
    connecttime = num_value(parsed.get("connecttime", 0))
    resets = num_value(parsed.get("resets", 0))
    battery = num_value(parsed.get("battery", 100))

    return (
        alerts > 0
        or resets > 0
        or battery < 50
        or connecttime >= SLOW_CONNECT_WARN
    )

def format_report(parsed, nested_device=""):
    fields = []

    if nested_device:
        fields.append(f"payload={nested_device}")

    mapping = [
        ("occupancy", "occ"),
        ("hourly", "hourly"),
        ("daily", "daily"),
        ("dailyoccupancy", "daily"),
        ("battery", "batt"),
        ("key1", "pwr"),
        ("temp", "temp"),
        ("alerts", "alerts"),
        ("resets", "resets"),
        ("node", "node"),
        ("rssi", "rssi"),
        ("snr", "snr"),
        ("hops", "hops"),
        ("msg", "msg"),
        ("success", "success"),
        ("connecttime", "conn"),
    ]

    for key, label in mapping:
        if key not in parsed:
            continue

        value = parsed[key]

        if key == "battery":
            out = f"{label}={fmt_num(value)}"
            if num_value(value) < 30:
                out = color(out, RED)
            elif num_value(value) < 50:
                out = color(out, YELLOW)
            fields.append(out)

        elif key == "temp":
            fields.append(f"{label}={fmt_num(value)}")

        elif key == "alerts":
            out = f"{label}={int(num_value(value))}"
            if num_value(value) > 0:
                out = color(out, RED)
            fields.append(out)

        elif key == "connecttime":
            out = f"{label}={int(num_value(value))}"
            if num_value(value) >= SLOW_CONNECT_CRIT:
                out = color(out, RED)
            elif num_value(value) >= SLOW_CONNECT_WARN:
                out = color(out, YELLOW)
            fields.append(out)

        else:
            fields.append(f"{label}={value}")

    return " ".join(fields)

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    if not line.startswith("{"):
        continue

    try:
        event = json.loads(line)
    except Exception:
        print(f"UNPARSED | {line}")
        continue

    name = event.get("name", "")
    coreid = event.get("coreid", "")
    product_id = str(event.get("productID", ""))
    published = event.get("published_at", "")
    data = event.get("data", "")

    if product_id and product_id != PRODUCT_ID:
        continue

    device_name = device_map.get(coreid, coreid)
    ts = local_ts(published)
    parsed_data = parse_data(data)

    # Always suppress webhook transport noise
    if name.startswith("hook-sent/"):
        continue
    if "/hook-response/" in name:
        continue

    # Suppress routine update bookkeeping unless verbose or actionable
    if name.startswith("particle/device/updates/"):
        update_key = name.split("/")[-1]
        if VERBOSE or data == "true" and update_key in ("pending", "forced"):
            print(f"{ts} | {device_name} | {color(f'update_{update_key}={data}', YELLOW)}")
        continue

    # Suppress routine online/offline unless verbose
    if name == "spark/status":
        if VERBOSE:
            if data == "online":
                print(f"{ts} | {device_name} | {color('ONLINE', GREEN)}")
            elif data == "offline":
                print(f"{ts} | {device_name} | {color('OFFLINE', YELLOW)}")
            else:
                print(f"{ts} | {device_name} | status={data}")

        # Always keep OTA status
        elif data == "auto-update":
            print(f"{ts} | {device_name} | {color('AUTO_UPDATE', CYAN)}")

        continue

    # Always keep reset cause
    if name == "spark/device/last_reset":
        reset_value = data or "<empty>"
        if reset_value in ("power_management", "update"):
            print(f"{ts} | {device_name} | {color('RESET', CYAN)} {color(reset_value, CYAN)}")
        else:
            print(f"{ts} | {device_name} | {color('RESET', RED)} {color(reset_value, RED)}")
        continue

    # Always keep flash status
    if name == "spark/flash/status":
        if data == "success":
            print(f"{ts} | {device_name} | {color('FLASH success', GREEN)}")
        elif data == "started":
            print(f"{ts} | {device_name} | {color('FLASH started', CYAN)}")
        else:
            print(f"{ts} | {device_name} | {color(f'FLASH {data}', YELLOW)}")
        continue

    # Keep app hash, shortened
    if name == "spark/device/app-hash":
        short_hash = str(data)[:12]
        print(f"{ts} | {device_name} | APPHASH {short_hash}")
        continue

    # Suppress routine diagnostics unless verbose
    if name == "spark/device/diagnostics/update":
        if VERBOSE:
            print(f"{ts} | {device_name} | diagnostics")
        continue

    # Report events become the main one-line output
    nested_device = ""
    if isinstance(parsed_data, dict):
        nested_id = parsed_data.get("deviceid", "")
        if nested_id:
            nested_device = device_map.get(nested_id, nested_id)

    if name == "status":
        if VERBOSE:
            print(
                f"DEBUG STATUS: type={type(parsed_data).__name__} "
                f"value={repr(parsed_data)[:200]}"
            )

    if name == "status" and isinstance(parsed_data, dict):
        reset_reason = parsed_data.get("resetReason", "?")
        alert = parsed_data.get("alert", "?")
        heap = parsed_data.get("freeHeap", "?")
        conn_age = parsed_data.get("lastConnectionAgeSec", "?")
        version = parsed_data.get("version", "?")
        breadcrumb = parsed_data.get("appBreadcrumb", "?")

        line = (
            f"{ts} | {device_name} | STATUS "
            f"ver={version} reset={reset_reason} alert={alert} "
            f"heap={heap} connAge={conn_age} breadcrumb={breadcrumb}"
        )

        alert_num = int(num_value(alert, 0))
        reset_num = int(num_value(reset_reason, 0))

        if alert_num > 0:
            line = color(line, RED)
        elif reset_num not in (0, 30):
            line = color(line, YELLOW)

        print(line)
        continue

    if is_report_event(name) and isinstance(parsed_data, dict):
        report = format_report(parsed_data, nested_device)

        if is_interesting_report(parsed_data):
            print(f"{ts} | {device_name} | {color('REPORT!', YELLOW)} {report}")
        else:
            print(f"{ts} | {device_name} | REPORT {report}")
        continue

    # Everything else: suppress empty routine status unless verbose
    if parsed_data == "":
        if VERBOSE:
            print(f"{ts} | {device_name} | {name} | <empty>")
        continue

    # Keep unknown non-empty events
    if isinstance(parsed_data, dict):
        print(f"{ts} | {device_name} | {name} | {format_report(parsed_data, nested_device)}")
    else:
        print(f"{ts} | {device_name} | {name} | data={parsed_data}")