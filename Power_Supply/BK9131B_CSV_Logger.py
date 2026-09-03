#!/usr/bin/env python3
"""
BK Precision 9131B Programmable DC Power Supply - Voltage/Current CSV Logger
Polls the power supply's live output voltage and current over SCPI and
appends timestamped readings to a CSV file.

Requires: pip install pyvisa pyvisa-py pyusb
(pyvisa-py + pyusb give a pure-Python VISA backend for USB/LAN instruments;
NI-VISA can be used instead if already installed.)

Example:
    python BK9131B_CSV_Logger.py --resource "USB0::0x2EC7::0x9130::123456::INSTR" \\
        --channels 1 2 --interval 1 --output run1.csv
"""

import argparse
import csv
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

import pyvisa

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Reading:
    """A single voltage/current sample from one output channel"""
    timestamp: datetime
    channel: int
    voltage: float
    current: float


class BK9131B:
    """SCPI interface to a BK Precision 9131B triple-output DC power supply"""

    def __init__(self, resource: str, timeout_ms: int = 5000):
        self.resource_name = resource
        self._rm = pyvisa.ResourceManager()
        self._inst = self._rm.open_resource(resource)
        self._inst.timeout = timeout_ms
        self._inst.read_termination = '\n'
        self._inst.write_termination = '\n'

    def identify(self) -> str:
        """Query *IDN? to confirm the instrument connection"""
        return self._inst.query("*IDN?").strip()

    def select_channel(self, channel: int) -> None:
        # The 9130 series requires selecting the active output before
        # MEAS:VOLT?/MEAS:CURR? report that channel's readings.
        self._inst.write(f"INST:NSEL {channel}")

    def read_channel(self, channel: int) -> Reading:
        self.select_channel(channel)
        voltage = float(self._inst.query("MEAS:VOLT?"))
        current = float(self._inst.query("MEAS:CURR?"))
        return Reading(
            timestamp=datetime.now(),
            channel=channel,
            voltage=voltage,
            current=current,
        )

    def close(self) -> None:
        self._inst.close()
        self._rm.close()


class CSVLogger:
    """Appends readings to a CSV file, writing the header only once"""

    def __init__(self, path: Path):
        self.path = path
        self._write_header = not path.exists() or path.stat().st_size == 0

    def append(self, readings: List[Reading]) -> None:
        with self.path.open("a", newline="") as f:
            writer = csv.writer(f)
            if self._write_header:
                writer.writerow(["timestamp", "channel", "voltage_V", "current_A"])
                self._write_header = False
            for r in readings:
                writer.writerow([
                    r.timestamp.isoformat(),
                    r.channel,
                    f"{r.voltage:.6f}",
                    f"{r.current:.6f}",
                ])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Log voltage and current from a BK Precision 9131B power supply to CSV"
    )
    parser.add_argument(
        "--resource",
        required=True,
        help='VISA resource string, e.g. "USB0::0x2EC7::0x9130::123456::INSTR" '
             'or "TCPIP0::192.168.1.50::inst0::INSTR"',
    )
    parser.add_argument(
        "--channels",
        type=int,
        nargs="+",
        default=[1],
        choices=[1, 2, 3],
        help="Output channel(s) to log (default: 1)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between samples (default: 1.0)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Total logging duration in seconds (default: run until Ctrl+C)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("9131b_log.csv"),
        help="Output CSV file path (default: 9131b_log.csv)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        psu = BK9131B(args.resource)
    except Exception as e:
        logger.error(f"Failed to connect to {args.resource}: {e}")
        return 1

    try:
        idn = psu.identify()
        logger.info(f"Connected to: {idn}")
    except Exception as e:
        logger.error(f"Failed to query instrument identity: {e}")
        psu.close()
        return 1

    csv_logger = CSVLogger(args.output)
    logger.info(f"Logging channel(s) {args.channels} every {args.interval}s to {args.output}")

    start = time.monotonic()
    sample_count = 0
    try:
        while True:
            readings = []
            for ch in args.channels:
                try:
                    reading = psu.read_channel(ch)
                    readings.append(reading)
                    logger.info(f"CH{ch}: {reading.voltage:.4f} V, {reading.current:.4f} A")
                except Exception as e:
                    logger.error(f"Failed to read channel {ch}: {e}")

            if readings:
                csv_logger.append(readings)
                sample_count += 1

            if args.duration is not None and (time.monotonic() - start) >= args.duration:
                break

            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Stopping logging (Ctrl+C received)")
    finally:
        psu.close()

    logger.info(f"Logged {sample_count} sample(s) to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
