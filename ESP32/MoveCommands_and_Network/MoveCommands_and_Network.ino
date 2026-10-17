#include <WiFi.h>
#include <WiFiUdp.h>

// ── WiFi / UDP ────────────────────────────────────────
const char* AP_SSID     = "ESP32-Signs";
const char* AP_PASSWORD = "semne1234";
const int   UDP_PORT    = 4210;

IPAddress AP_IP     (192, 168, 4, 1);
IPAddress AP_GATEWAY(192, 168, 4, 1);
IPAddress AP_SUBNET (255, 255, 255, 0);

WiFiUDP udp;
char incomingBuffer[64];
String lastCommand = "";

unsigned long lastPacketTime = 0;
const unsigned long TIMEOUT_MS = 2000;
bool standby = false;

// ─── Pini corespondenti conexiunilor ───
#define PWMA 33   // Viteza canal A (motoare STANGA)
#define AIN2 25   // Directie canal A
#define AIN1 26   // Directie canal A
#define STBY 27   // Standby driver
#define BIN1 14   // Directie canal B (motoare DREAPTA)
#define BIN2 12   // Directie canal B
#define PWMB 13   // Viteza canal B (motoare DREAPTA)

#define VITEZA 180
#define VITEZA_MIN 110

#define BUZZER_PIN 32
#define BUZZER_CH  2
#define BUZZER_RES 8

// ── Prototipuri functii ───────────────────────────────
void proceseazaSemn(String semn);
void intraStandby();
void inainte();
void opreste();

// ─────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);

  pinMode(PWMA, OUTPUT);
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(PWMB, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  pinMode(STBY, OUTPUT);

  digitalWrite(STBY, HIGH);

  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(AP_IP, AP_GATEWAY, AP_SUBNET);
  WiFi.softAP(AP_SSID, AP_PASSWORD);

  udp.begin(UDP_PORT);

  Serial.println("Access Point pornit!");
  Serial.print("IP: ");
  Serial.println(WiFi.softAPIP());
  Serial.print("Ascult pe portul UDP: ");
  Serial.println(UDP_PORT);

  opreste();
  lastPacketTime = millis();
}

void loop() {
  int packetSize = udp.parsePacket();

  if (packetSize) {
    lastPacketTime = millis();

    int len = udp.read(incomingBuffer, sizeof(incomingBuffer) - 1);
    incomingBuffer[len] = '\0';
    String semn = String(incomingBuffer);

    Serial.print("Primit: ");
    Serial.println(semn);

    if (semn == "EXIT") {
      intraStandby();
      return;
    }

    if (standby) {
      standby = false;
      lastCommand = "";
      Serial.println("→ PC reconectat, reiau comenzile.");
    }

    if (semn != lastCommand) {
      lastCommand = semn;
      proceseazaSemn(semn);
    }
  }

  if (!standby && millis() - lastPacketTime > TIMEOUT_MS) {
    if (lastCommand != "") {
      Serial.println("→ Niciun semn detectat, stau pe loc.");
      opreste();
      lastCommand = "";
    }
  }
}

// ── Procesare semne ───────────────────────────────────
void proceseazaSemn(String semn) {
  if (semn == "Open") {
    inainte();
  } else if (semn == "Closed") {
    opreste();
  } else if (semn == "Left") {
    vireazaStanga();
  } else if (semn == "Right") {
    vireazaDreapta();
  }
}

void intraStandby() {
  Serial.println("→ EXIT primit. Standby pana la reconectare.");
  opreste();
  standby = true;
  lastCommand = "";
}

// ── Comenzi motoare ───────────────────────────────────
void inainte() {
  Serial.println("→ MERG INAINTE");
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  analogWrite(PWMA, VITEZA);

  digitalWrite(BIN1, HIGH);
  digitalWrite(BIN2, LOW);
  analogWrite(PWMB, VITEZA);
}

void opreste() {
  Serial.println("→ MA OPRESC");
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  analogWrite(PWMA, 0);

  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);
  analogWrite(PWMB, 0);
}

void vireazaStanga() {
    Serial.println("→ VIRAJ STANGA");
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  analogWrite(PWMA, 0);

  digitalWrite(BIN1, HIGH);
  digitalWrite(BIN2, LOW);
  analogWrite(PWMB, VITEZA);
}

void vireazaDreapta() {
    Serial.println("→ VIRAJ DREAPTA");
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  analogWrite(PWMA, VITEZA);

  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);
  analogWrite(PWMB, 0);
}