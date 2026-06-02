"""
RFID test araci - masaustu uygulamayi KAPATIN, sonra calistirin:
  python test_rfid.py
"""
import time

import serial
import serial.tools.list_ports

BAUD = 9600
TIMEOUT = 12


def main():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    print("Bulunan COM portlari:", ports or "YOK")

    if not ports:
        print("\nHATA: Hic COM portu yok. Arduino USB ile bagli mi?")
        return

    port = ports[0]
    if len(ports) > 1:
        print(f"\nBirden fazla port var, ilki deneniyor: {port}")
        print("Farkli port icin: python test_rfid.py COM6")

    import sys

    if len(sys.argv) > 1:
        port = sys.argv[1]

    print(f"\n{port} aciliyor ({BAUD} baud)...")
    print("NOT: Masaustu uygulama veya Serial Monitor aciksa once kapatın!\n")

    try:
        ser = serial.Serial(port, BAUD, timeout=1)
    except serial.SerialException as exc:
        print(f"HATA: Port acilamadi -> {exc}")
        print("\nCozum:")
        print("  1. start_client.bat ile acik uygulamayi kapat")
        print("  2. Arduino IDE Serial Monitor'u kapat")
        print("  3. USB kabloyu cikar-tak")
        return

    time.sleep(2)
    ser.reset_input_buffer()
    print(f"{TIMEOUT} saniye dinleniyor. Karti okuyucuya yaklastirin...\n")

    start = time.time()
    got_ready = False
    got_uid = False

    while time.time() - start < TIMEOUT:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            continue
        print(f"  -> {line}")
        if line == "RFID:HAZIR" or "UTR-625" in line:
            got_ready = True
        if line == "RFID:HATA":
            print("\n!!! MODUL BULUNAMADI - kablo baglantilarini ve 3.3V gucunu kontrol edin")
        if line.startswith("UID:") or "Kart UID:" in line or "KART UID:" in line.upper():
            got_uid = True

    ser.close()
    print("\n--- SONUC ---")
    if got_uid:
        print("OK: Kart basariyla okundu!")
    elif got_ready:
        print("Modul hazir ama kart okunmadi.")
        print("  - Karti 1-2 cm mesafede tutun")
        print("  - Farkli bir RFID kart deneyin")
    else:
        print("Arduino'dan hic veri gelmedi.")
        print("  - Arduino kodu yuklu mu? (utarit_rfid/utarit_rfid.ino)")
        print("  - UTR-625 baglantisi: TX->D10, RX->D11")
        print("  - Dogru COM portu mu?")


if __name__ == "__main__":
    main()
