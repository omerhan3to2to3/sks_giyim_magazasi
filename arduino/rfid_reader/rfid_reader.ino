/*
 * UTR-625 icin ana Arduino kodu (utarit_rfid ile ayni).
 * Arduino IDE'de bu klasoru veya utarit_rfid/ klasorunu acip yukleyin.
 */

#include <SoftwareSerial.h>

SoftwareSerial rfid(10, 11);

const uint8_t POLL_CMD[] = {0xFF, 0x00, 0x01, 0x83, 0x84};
const unsigned long POLL_INTERVAL_MS = 500;
const unsigned long DEBOUNCE_MS = 2000;

unsigned long lastPoll = 0;
String lastUid = "";
unsigned long lastReadMs = 0;

void reportReady() {
  Serial.println("RFID:HAZIR");
}

bool parseFrame(uint8_t* frame, uint8_t len, char* uidOut) {
  if (len < 4) return false;
  if (frame[0] != 0xFF || frame[1] != 0x00 || frame[3] != 0x83) return false;

  uint8_t nn = frame[2];
  if (len < 4 + nn) return false;
  if (nn <= 2) return false;

  uint16_t cs = 0;
  for (int i = 2; i < 4 + nn - 1; i++) cs += frame[i];
  if ((cs & 0xFF) != frame[4 + nn - 1]) return false;

  uidOut[0] = '\0';
  for (int i = 4; i < 4 + nn - 1; i++) {
    char hex[3];
    sprintf(hex, "%02X", frame[i]);
    strcat(uidOut, hex);
  }
  return true;
}

void setup() {
  Serial.begin(9600);
  rfid.begin(115200);
  delay(300);
  reportReady();
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "STATUS") {
      reportReady();
    }
  }

  unsigned long now = millis();
  if (now - lastPoll < POLL_INTERVAL_MS) return;
  lastPoll = now;

  rfid.write(POLL_CMD, 5);

  unsigned long t = millis();
  uint8_t buf[16];
  uint8_t idx = 0;

  while (millis() - t < 200 && idx < sizeof(buf)) {
    if (rfid.available()) {
      buf[idx++] = rfid.read();
    }
  }

  if (idx < 4) return;

  char uid[32] = "";
  if (!parseFrame(buf, idx, uid)) return;

  String uidStr = String(uid);
  uidStr.toUpperCase();

  if (uidStr == lastUid && (now - lastReadMs) < DEBOUNCE_MS) return;

  lastUid = uidStr;
  lastReadMs = now;

  Serial.print("UID:");
  Serial.println(uidStr);
}
