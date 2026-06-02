import re
import threading
import time
from typing import Callable, Optional

import serial
import serial.tools.list_ports

from client.config import load_config


class RfidReader:
    """Arduino Nano uzerinden seri port ile RFID kart okuma.

    Desteklenen okuyucular:
    - UTR-625 (Utarit) -> utarit_rfid.ino
    - MFRC522 (eski)   -> UID: / RFID:HAZIR formati
    """

    def __init__(self, on_card_read: Callable[[str], None], port: Optional[str] = None):
        self.on_card_read = on_card_read
        self.on_status: Optional[Callable[[str], None]] = None
        self.port = port or load_config()["serial_port"]
        self.baud_rate = load_config()["baud_rate"]
        self._serial: Optional[serial.Serial] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._last_uid = ""
        self._last_read_time = 0.0
        self.is_connected = False
        self.module_ready = False
        self.last_raw_line = ""
        self.last_error = ""

    @staticmethod
    def list_ports() -> list[str]:
        return [p.device for p in serial.tools.list_ports.comports()]

    def connect(self) -> bool:
        self.last_error = ""
        self.module_ready = False
        try:
            if self._serial and self._serial.is_open:
                self._serial.close()
            self._serial = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=1,
                dsrdtr=False,
                rtscts=False,
            )
            time.sleep(2.5)
            self._read_boot_messages()
            self.is_connected = True
            return True
        except serial.SerialException as exc:
            self._serial = None
            self.is_connected = False
            self.last_error = str(exc)
            return False

    @staticmethod
    def _extract_uid(line: str) -> Optional[str]:
        upper = line.upper().strip()

        if upper.startswith("UID:"):
            return upper.replace("UID:", "", 1).strip()

        # UTR-625 ham cikti: "Kart UID: ABCD1234"
        if "KART UID:" in upper:
            return upper.split("KART UID:", 1)[1].strip()

        match = re.search(r"\b([0-9A-F]{4,32})\b", upper)
        if match and ("UID" in upper or "KART" in upper):
            return match.group(1)

        return None

    def _process_line(self, line: str):
        self.last_raw_line = line
        upper = line.upper().strip()

        if upper == "RFID:HAZIR" or "UTR-625 RFID HAZ" in upper or "UTARIT" in upper and "HAZ" in upper:
            self.module_ready = True
            self._emit_status("ready")
            return

        if upper == "RFID:HATA":
            self.module_ready = False
            self._emit_status("module_error")
            return

        uid = self._extract_uid(line)
        if uid and self._should_emit(uid):
            self._last_uid = uid
            self._last_read_time = time.time()
            self.on_card_read(uid)

    def _read_boot_messages(self):
        if not self._serial:
            return
        deadline = time.time() + 3.0
        while time.time() < deadline:
            line = self._serial.readline().decode("utf-8", errors="ignore").strip()
            if line:
                self._process_line(line)
            elif self.module_ready or self.last_raw_line == "RFID:HATA":
                break

        try:
            self._serial.write(b"STATUS\n")
            time.sleep(0.3)
            for _ in range(5):
                line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    self._process_line(line)
        except Exception:
            pass

    def disconnect(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None
        self.is_connected = False
        self.module_ready = False

    def start_listening(self) -> bool:
        if self._thread and self._thread.is_alive():
            return True
        self._running = True
        self._thread = threading.Thread(target=self._connect_and_read_loop, daemon=True)
        self._thread.start()
        return True

    def _connect_and_read_loop(self):
        if not self._serial or not self._serial.is_open:
            if not self.connect():
                return
        self._read_loop()

    def _emit_status(self, message: str):
        if self.on_status:
            self.on_status(message)

    def _read_loop(self):
        while self._running and self._serial and self._serial.is_open:
            try:
                line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    self._process_line(line)
            except Exception as exc:
                self.last_error = str(exc)
                time.sleep(0.5)

    def _should_emit(self, uid: str) -> bool:
        now = time.time()
        if uid == self._last_uid and (now - self._last_read_time) < 2.0:
            return False
        return True

    def simulate_read(self, uid: str):
        self.on_card_read(uid.upper())
