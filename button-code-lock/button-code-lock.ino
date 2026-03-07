#include <WiFi.h>
#include <HTTPClient.h>
#include <WebServer.h>
#include <Preferences.h>
#include <Adafruit_NeoPixel.h>
#include <DNSServer.h>

DNSServer dnsServer;

// ============ WiFi CONFIG ============
String wifi_ssid = "";
String wifi_password = "";
bool apMode = false;
const char* AP_SSID = "CodeLock-Setup";
const char* AP_PASS = "codelock1";

// ============ Hardware CONFIG ============
const int BUTTON_PIN = 17;
const int LED_PIN = 16;
const int NUM_LEDS = 12;

// ============ Timing CONFIG ============
int spinSpeedMs = 350;
const int TIMEOUT_MS = 10000;
const int SHOW_DURATION_MS = 800;
const int DEBOUNCE_MS = 250;

// ============ State Machine ============
enum State {
  SLEEP,
  IDLE,
  SPIN_1,
  SHOW_1,
  SPIN_2,
  SHOW_2,
  SPIN_3,
  EVALUATE,
  STATE_SUCCESS,
  STATE_FAIL
};

State currentState = SLEEP;

// ============ Combination Lock ============
int secretCode[3] = {0, 0, 0};
int inputCode[3] = {0, 0, 0};
int currentStep = 0;

// ============ Spin State ============
int currentLed = 0;
int spinDirection = 1;  // 1 = CW, -1 = CCW
unsigned long lastSpinTime = 0;
unsigned long spinStartTime = 0;

// ============ Show State ============
unsigned long showStartTime = 0;

// ============ Idle ============
bool idleShown = false;

// ============ Button ============
unsigned long lastButtonTime = 0;
bool lastButtonState = HIGH;

// ============ Animation tracking ============
unsigned long animStartTime = 0;
bool haCallSent = false;

// ============ Home Assistant Config ============
String ha_url = "http://homeassistant.local:8123/api/webhook/codelock";
String ha_method = "POST";
String ha_token = "";
String ha_payload = "{\"action\":\"unlock\"}";

// ============ Objects ============
Adafruit_NeoPixel ring(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);
WebServer server(80);
Preferences preferences;

// ============ Forward Declarations ============
void handleSleep();
void handleIdle();
void handleSpin();
void handleShow();
void handleEvaluate();
void handleSuccess();
void handleFail();
void callHomeAssistant();
void setupWebServer();
void handleWebRoot();
void handleWebSave();
void loadPreferences();
void savePreferences();
bool buttonPressed();
void setAllLeds(uint32_t color);
void setState(State newState);

// ============ SETUP ============
void startAPMode() {
  apMode = true;
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);
  delay(500);  // Wacht tot AP volledig actief is

  // DNS captive portal — alle domeinen → onze IP
  dnsServer.start(53, "*", WiFi.softAPIP());

  Serial.println();
  Serial.println("╔════════════════════════════════════════╗");
  Serial.println("║       ACCESS POINT MODUS ACTIEF        ║");
  Serial.println("╠════════════════════════════════════════╣");
  Serial.printf( "║  SSID:      %-26s║\n", AP_SSID);
  Serial.printf( "║  Wachtwoord: %-25s║\n", AP_PASS);
  Serial.printf( "║  Config:    http://%-20s║\n", WiFi.softAPIP().toString().c_str());
  Serial.println("╚════════════════════════════════════════╝");

  // Paarse puls om AP-modus aan te geven
  for (int i = 0; i < 3; i++) {
    setAllLeds(ring.Color(100, 0, 180));
    ring.show();
    delay(200);
    ring.clear();
    ring.show();
    delay(200);
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=== Combinatieslot ===");

  // Button
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  Serial.println("[OK] Button op pin " + String(BUTTON_PIN));

  // NeoPixel
  ring.begin();
  ring.setBrightness(60);
  ring.clear();
  ring.show();
  Serial.println("[OK] NeoPixel ring (" + String(NUM_LEDS) + " LEDs)");

  // Preferences laden
  loadPreferences();
  Serial.println("[OK] Preferences geladen");
  Serial.printf("     Code: %d-%d-%d\n", secretCode[0], secretCode[1], secretCode[2]);

  // Check of knop ingedrukt is bij boot → forceer AP-modus
  if (digitalRead(BUTTON_PIN) == LOW) {
    Serial.println("[BOOT] Knop ingedrukt — forceer AP-modus");
    startAPMode();
    setupWebServer();
    return;
  }

  // WiFi verbinden (als credentials beschikbaar)
  if (wifi_ssid.length() == 0) {
    Serial.println("[WIFI] Geen WiFi geconfigureerd — start AP-modus");
    startAPMode();
    setupWebServer();
    return;
  }

  Serial.print("[WIFI] Verbinden met " + wifi_ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifi_ssid.c_str(), wifi_password.c_str());

  int ledIndex = 0;
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 50) {
    delay(200);
    Serial.print(".");
    ring.clear();
    ring.setPixelColor(ledIndex, ring.Color(0, 0, 180));
    ring.show();
    ledIndex = (ledIndex + 1) % NUM_LEDS;
    attempts++;
  }
  Serial.println();

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] Verbinding mislukt — start AP-modus");
    WiFi.disconnect();
    startAPMode();
    setupWebServer();
    return;
  }

  // Groene flash bij succes
  setAllLeds(ring.Color(0, 180, 0));
  ring.show();
  delay(800);
  ring.clear();
  ring.show();

  // WebServer starten
  setupWebServer();

  Serial.println();
  Serial.println("╔════════════════════════════════════════╗");
  Serial.println("║         COMBINATIESLOT GEREED          ║");
  Serial.println("╠════════════════════════════════════════╣");
  Serial.printf( "║  WiFi:      %-26s║\n", wifi_ssid.c_str());
  Serial.printf( "║  IP:        %-26s║\n", WiFi.localIP().toString().c_str());
  Serial.printf( "║  Config:    http://%-20s║\n", WiFi.localIP().toString().c_str());
  Serial.printf( "║  Code:      %d-%d-%-24d║\n", secretCode[0], secretCode[1], secretCode[2]);
  Serial.printf( "║  HA URL:    %-26s║\n", ha_url.substring(0, 26).c_str());
  Serial.println("╚════════════════════════════════════════╝");
  Serial.println();

  ring.clear();
  ring.show();
  currentState = SLEEP;
}

// ============ MAIN LOOP ============
void loop() {
  if (apMode) {
    dnsServer.processNextRequest();
  }
  server.handleClient();

  if (apMode) return;  // In AP-modus geen lock-logica

  switch (currentState) {
    case SLEEP:       handleSleep();    break;
    case IDLE:        handleIdle();     break;
    case SPIN_1:
    case SPIN_2:
    case SPIN_3:      handleSpin();     break;
    case SHOW_1:
    case SHOW_2:      handleShow();     break;
    case EVALUATE:    handleEvaluate(); break;
    case STATE_SUCCESS: handleSuccess(); break;
    case STATE_FAIL:  handleFail();     break;
  }
}

// ============ STATE: SLEEP ============
unsigned long lastDebugTime = 0;
void handleSleep() {
  // Debug: toon button status elke 2 sec
  if (millis() - lastDebugTime > 2000) {
    lastDebugTime = millis();
    Serial.printf("[SLEEP] pin=%d last=%d dt=%lu\n",
                  digitalRead(BUTTON_PIN), lastButtonState,
                  millis() - lastButtonTime);
  }

  // Alles uit, wacht op knop
  if (buttonPressed()) {
    Serial.println("[WAKE] Wakker - LED 0 rood");
    setState(IDLE);
  }
}


// ============ STATE: IDLE ============
void handleIdle() {
  // LED 0 rood als referentiepunt, rest uit
  if (!idleShown) {
    idleShown = true;
    ring.clear();
    ring.setPixelColor(0, ring.Color(255, 0, 0));
    ring.show();
  }

  if (buttonPressed()) {
    Serial.println("[KNOP] Start combinatie-invoer");
    currentStep = 0;
    inputCode[0] = inputCode[1] = inputCode[2] = 0;
    currentLed = 0;
    spinDirection = 1;  // Eerste spin: kloksgewijs
    setState(SPIN_1);
  }
}

// ============ STATE: SPIN ============
void handleSpin() {
  // Timeout check
  if (millis() - spinStartTime > TIMEOUT_MS) {
    Serial.println("[TIMEOUT] Te lang gewacht, terug naar SLEEP");
    ring.clear();
    ring.show();
    setState(SLEEP);
    return;
  }

  // Pixel draaien
  if (millis() - lastSpinTime >= (unsigned long)spinSpeedMs) {
    lastSpinTime = millis();
    currentLed = (currentLed + spinDirection + NUM_LEDS) % NUM_LEDS;

    ring.clear();

    // Toon al gekozen posities dim
    for (int i = 0; i < currentStep; i++) {
      ring.setPixelColor(inputCode[i], ring.Color(40, 40, 40));
    }

    // Trailing pixels (staart-effect)
    int trail1 = (currentLed - spinDirection + NUM_LEDS) % NUM_LEDS;
    int trail2 = (currentLed - 2 * spinDirection + NUM_LEDS) % NUM_LEDS;
    ring.setPixelColor(trail2, ring.Color(10, 5, 0));
    ring.setPixelColor(trail1, ring.Color(60, 30, 0));

    // Hoofdpixel (fel wit-geel)
    ring.setPixelColor(currentLed, ring.Color(255, 200, 50));

    // LED 0 rode referentiemarker (dim, tenzij overruled door hoofdpixel/trail)
    if (currentLed != 0 && trail1 != 0 && trail2 != 0) {
      ring.setPixelColor(0, ring.Color(60, 0, 0));
    }

    ring.show();
  }

  if (buttonPressed()) {
    inputCode[currentStep] = currentLed;
    Serial.printf("[STOP] Positie %d = LED %d\n", currentStep + 1, currentLed);

    // Naar de juiste SHOW state
    if (currentState == SPIN_1) {
      setState(SHOW_1);
    } else if (currentState == SPIN_2) {
      setState(SHOW_2);
    } else {
      // SPIN_3 → direct naar EVALUATE
      setState(EVALUATE);
    }
  }
}

// ============ STATE: SHOW ============
void handleShow() {
  unsigned long elapsed = millis() - showStartTime;

  // Knipperende witte LED op gestopte positie
  bool on = ((elapsed / 100) % 2) == 0;

  ring.clear();

  // Toon al gekozen posities dim
  for (int i = 0; i <= currentStep; i++) {
    ring.setPixelColor(inputCode[i], on && i == currentStep
                       ? ring.Color(255, 255, 255)
                       : ring.Color(40, 40, 40));
  }

  // LED 0 rode referentiemarker (tenzij het een gekozen positie is)
  bool led0Used = false;
  for (int i = 0; i <= currentStep; i++) {
    if (inputCode[i] == 0) led0Used = true;
  }
  if (!led0Used) {
    ring.setPixelColor(0, ring.Color(60, 0, 0));
  }

  ring.show();

  if (elapsed >= SHOW_DURATION_MS) {
    currentStep++;

    if (currentState == SHOW_1) {
      spinDirection = -1;  // Tweede spin: tegen de klok in
      setState(SPIN_2);
    } else {
      spinDirection = 1;   // Derde spin: kloksgewijs
      setState(SPIN_3);
    }
  }
}

// ============ STATE: EVALUATE ============
void handleEvaluate() {
  Serial.printf("[CHECK] Invoer: %d-%d-%d vs Code: %d-%d-%d\n",
                inputCode[0], inputCode[1], inputCode[2],
                secretCode[0], secretCode[1], secretCode[2]);

  bool correct = (inputCode[0] == secretCode[0] &&
                  inputCode[1] == secretCode[1] &&
                  inputCode[2] == secretCode[2]);

  if (correct) {
    Serial.println("[OK] Correcte code!");
    setState(STATE_SUCCESS);
  } else {
    Serial.println("[FOUT] Verkeerde code!");
    setState(STATE_FAIL);
  }
}

// ============ STATE: SUCCESS ============
void handleSuccess() {
  unsigned long elapsed = millis() - animStartTime;

  // Fase 1: Groene chase (0-600ms)
  if (elapsed < 600) {
    int pos = (elapsed / 50) % NUM_LEDS;
    ring.clear();
    for (int i = 0; i <= pos; i++) {
      ring.setPixelColor(i, ring.Color(0, 200, 0));
    }
    ring.show();
    return;
  }

  // Fase 2: Alle LEDs groen (600-1600ms)
  if (elapsed < 1600) {
    setAllLeds(ring.Color(0, 200, 0));
    ring.show();

    // HA call eenmalig bij begin fase 2
    if (!haCallSent) {
      haCallSent = true;
      callHomeAssistant();
    }
    return;
  }

  // Fase 3: Fade out (1600-2600ms)
  if (elapsed < 2600) {
    int brightness = 200 - ((elapsed - 1600) * 200) / 1000;
    if (brightness < 0) brightness = 0;
    setAllLeds(ring.Color(0, brightness, 0));
    ring.show();
    return;
  }

  // Klaar
  ring.clear();
  ring.show();
  Serial.println("[OK] Terug naar SLEEP\n");
  setState(SLEEP);
}

// ============ STATE: FAIL ============
void handleFail() {
  unsigned long elapsed = millis() - animStartTime;

  // 3x rood flashen (600ms totaal)
  if (elapsed < 600) {
    int flashPhase = elapsed / 100;
    bool on = (flashPhase % 2) == 0;
    if (on) {
      setAllLeds(ring.Color(255, 0, 0));
    } else {
      ring.clear();
    }
    ring.show();
    return;
  }

  // Fade out (600-1200ms)
  if (elapsed < 1200) {
    int brightness = 255 - ((elapsed - 600) * 255) / 600;
    if (brightness < 0) brightness = 0;
    setAllLeds(ring.Color(brightness, 0, 0));
    ring.show();
    return;
  }

  // Klaar
  ring.clear();
  ring.show();
  Serial.println("[OK] Terug naar SLEEP\n");
  setState(SLEEP);
}

// ============ STATE TRANSITIONS ============
void setState(State newState) {
  currentState = newState;

  switch (newState) {
    case SLEEP:
      ring.clear();
      ring.show();
      // Reset button state zodat edge-detectie schoon begint
      lastButtonState = digitalRead(BUTTON_PIN);
      lastButtonTime = millis();
      Serial.println("[SLEEP] LEDs uit, wacht op knop...");
      break;
    case IDLE:
      idleShown = false;
      break;
    case SPIN_1:
    case SPIN_2:
    case SPIN_3:
      spinStartTime = millis();
      lastSpinTime = millis();
      break;
    case SHOW_1:
    case SHOW_2:
      showStartTime = millis();
      break;
    case EVALUATE:
      break;
    case STATE_SUCCESS:
      haCallSent = false;
      animStartTime = millis();
      break;
    case STATE_FAIL:
      animStartTime = millis();
      break;
  }
}

// ============ BUTTON HANDLING ============
bool buttonPressed() {
  bool currentButtonState = digitalRead(BUTTON_PIN);

  if (currentButtonState == LOW && lastButtonState == HIGH) {
    if (millis() - lastButtonTime >= DEBOUNCE_MS) {
      lastButtonTime = millis();
      lastButtonState = currentButtonState;
      return true;
    }
  }

  lastButtonState = currentButtonState;
  return false;
}

// ============ HOME ASSISTANT ============
void callHomeAssistant() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HA] WiFi niet verbonden!");
    return;
  }

  if (ha_url.length() == 0) {
    Serial.println("[HA] Geen URL geconfigureerd");
    return;
  }

  HTTPClient http;
  http.begin(ha_url);

  if (ha_token.length() > 0) {
    http.addHeader("Authorization", "Bearer " + ha_token);
  }

  int httpCode;
  if (ha_method == "POST") {
    Serial.println("[HA] POST " + ha_url);
    if (ha_payload.length() > 0) {
      http.addHeader("Content-Type", "application/json");
      httpCode = http.POST(ha_payload);
    } else {
      httpCode = http.POST("");
    }
  } else {
    Serial.println("[HA] GET " + ha_url);
    httpCode = http.GET();
  }

  if (httpCode > 0) {
    Serial.printf("[HA] Response: %d\n", httpCode);
  } else {
    Serial.println("[HA] Fout: " + http.errorToString(httpCode));
  }

  http.end();
}

// ============ PREFERENCES ============
void loadPreferences() {
  preferences.begin("codelock", true);  // read-only
  wifi_ssid = preferences.getString("wifi_ssid", "");
  wifi_password = preferences.getString("wifi_pass", "");
  secretCode[0] = preferences.getInt("code0", 0);
  secretCode[1] = preferences.getInt("code1", 4);
  secretCode[2] = preferences.getInt("code2", 8);
  ha_url = preferences.getString("ha_url", ha_url);
  ha_method = preferences.getString("ha_method", ha_method);
  ha_token = preferences.getString("ha_token", ha_token);
  ha_payload = preferences.getString("ha_payload", ha_payload);
  spinSpeedMs = preferences.getInt("spin_speed", spinSpeedMs);
  preferences.end();
}

void savePreferences() {
  preferences.begin("codelock", false);  // read-write
  preferences.putString("wifi_ssid", wifi_ssid);
  preferences.putString("wifi_pass", wifi_password);
  preferences.putInt("code0", secretCode[0]);
  preferences.putInt("code1", secretCode[1]);
  preferences.putInt("code2", secretCode[2]);
  preferences.putString("ha_url", ha_url);
  preferences.putString("ha_method", ha_method);
  preferences.putString("ha_token", ha_token);
  preferences.putString("ha_payload", ha_payload);
  preferences.putInt("spin_speed", spinSpeedMs);
  preferences.end();
  Serial.printf("[SAVE] Code: %d-%d-%d, Speed: %dms\n", secretCode[0], secretCode[1], secretCode[2], spinSpeedMs);
  Serial.println("[SAVE] HA URL: " + ha_url);
}

// ============ WEB SERVER ============
void setupWebServer() {
  server.on("/", HTTP_GET, handleWebRoot);
  server.on("/save", HTTP_POST, handleWebSave);
  // Captive portal: redirect alle onbekende paden naar /
  server.onNotFound([]() {
    server.sendHeader("Location", "/", true);
    server.send(302, "text/plain", "");
  });
  server.begin();
}

void handleWebRoot() {
  String html = R"rawliteral(<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Combinatieslot Config</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 480px; margin: 20px auto; padding: 0 16px; background: #1a1a2e; color: #e0e0e0; }
  h1 { color: #f0c040; font-size: 1.4em; }
  h2 { color: #a0a0c0; font-size: 1.1em; margin-top: 24px; }
  label { display: block; margin: 10px 0 4px; font-size: 0.9em; color: #b0b0d0; }
  input, select { width: 100%; padding: 8px; border: 1px solid #333; border-radius: 6px; background: #16213e; color: #e0e0e0; box-sizing: border-box; font-size: 1em; }
  select { appearance: auto; }
  .code-row { display: flex; gap: 12px; }
  .code-row > div { flex: 1; }
  button { background: #f0c040; color: #1a1a2e; border: none; padding: 12px; border-radius: 6px; font-size: 1em; font-weight: bold; cursor: pointer; width: 100%; margin-top: 20px; }
  button:hover { background: #ffd060; }
  .info { font-size: 0.8em; color: #808090; margin-top: 4px; }
</style>
</head><body>
<h1>&#x1F512; Combinatieslot</h1>
<form method="POST" action="/save">
<h2>WiFi</h2>
<label>SSID</label>
<input type="text" name="wifi_ssid" value=")rawliteral" + wifi_ssid + R"rawliteral(">
<label>Wachtwoord</label>
<input type="password" name="wifi_pass" value=")rawliteral" + wifi_password + R"rawliteral(">
<div class="info">Na opslaan herstart het apparaat om te verbinden</div>
<h2>Combinatiecode</h2>
<div class="code-row">
)rawliteral";

  // 3 dropdowns voor de code
  const char* labels[] = {"Pos 1 (CW)", "Pos 2 (CCW)", "Pos 3 (CW)"};
  for (int c = 0; c < 3; c++) {
    html += "<div><label>" + String(labels[c]) + "</label><select name=\"code" + String(c) + "\">";
    for (int i = 0; i < NUM_LEDS; i++) {
      html += "<option value=\"" + String(i) + "\"";
      if (secretCode[c] == i) html += " selected";
      html += ">" + String(i) + "</option>";
    }
    html += "</select></div>";
  }

  html += R"rawliteral(</div>

<h2>Draaisnelheid</h2>
<label>Snelheid (ms per stap)</label>
<input type="range" name="spin_speed" min="50" max="300" step="10" value=")rawliteral" + String(spinSpeedMs) + R"rawliteral(" oninput="this.nextElementSibling.textContent=this.value+'ms'">
<span style="color:#f0c040">)rawliteral" + String(spinSpeedMs) + R"rawliteral(ms</span>
<div class="info">50 = heel snel, 300 = heel langzaam (standaard: 150)</div>

<h2>Home Assistant</h2>
<label>Webhook URL</label>
<input type="text" name="ha_url" value=")rawliteral" + ha_url + R"rawliteral(">
<div class="info">bv. http://homeassistant.local:8123/api/webhook/codelock</div>

<label>Methode</label>
<select name="ha_method">
<option value="GET")rawliteral" + String(ha_method == "GET" ? " selected" : "") + R"rawliteral(>GET</option>
<option value="POST")rawliteral" + String(ha_method == "POST" ? " selected" : "") + R"rawliteral(>POST</option>
</select>

<label>Bearer Token (optioneel)</label>
<input type="text" name="ha_token" value=")rawliteral" + ha_token + R"rawliteral(">
<div class="info">Alleen nodig voor REST API, niet voor webhooks</div>

<label>POST Body (optioneel)</label>
<input type="text" name="ha_payload" value=")rawliteral" + ha_payload + R"rawliteral(">
<div class="info">JSON payload, bv. {"action":"unlock"}</div>

<button type="submit">Opslaan</button>
</form>
</body></html>)rawliteral";

  server.send(200, "text/html", html);
}

void handleWebSave() {
  bool wifiChanged = false;
  if (server.hasArg("wifi_ssid")) {
    String newSsid = server.arg("wifi_ssid");
    if (newSsid != wifi_ssid) wifiChanged = true;
    wifi_ssid = newSsid;
  }
  if (server.hasArg("wifi_pass")) {
    String newPass = server.arg("wifi_pass");
    if (newPass != wifi_password) wifiChanged = true;
    wifi_password = newPass;
  }
  if (server.hasArg("code0")) secretCode[0] = server.arg("code0").toInt() % NUM_LEDS;
  if (server.hasArg("code1")) secretCode[1] = server.arg("code1").toInt() % NUM_LEDS;
  if (server.hasArg("code2")) secretCode[2] = server.arg("code2").toInt() % NUM_LEDS;
  if (server.hasArg("spin_speed")) {
    int speed = server.arg("spin_speed").toInt();
    if (speed >= 50 && speed <= 300) spinSpeedMs = speed;
  }
  if (server.hasArg("ha_url")) ha_url = server.arg("ha_url");
  if (server.hasArg("ha_method")) ha_method = server.arg("ha_method");
  if (server.hasArg("ha_token")) ha_token = server.arg("ha_token");
  if (server.hasArg("ha_payload")) ha_payload = server.arg("ha_payload");

  savePreferences();

  String html = R"rawliteral(<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Opgeslagen</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 480px; margin: 40px auto; padding: 0 16px; background: #1a1a2e; color: #e0e0e0; text-align: center; }
  .ok { font-size: 3em; }
  a { color: #f0c040; }
</style>
</head><body>
<div class="ok">&#x2705;</div>
<h2>Instellingen opgeslagen!</h2>
<p>Code: )rawliteral" + String(secretCode[0]) + "-" + String(secretCode[1]) + "-" + String(secretCode[2]) + R"rawliteral(</p>)rawliteral";

  if (wifiChanged && apMode) {
    html += "<p style='color:#f0c040'>WiFi gewijzigd — apparaat herstart over 3 seconden...</p>";
  } else {
    html += "<p><a href=\"/\">Terug</a></p>";
  }

  html += "</body></html>";

  server.send(200, "text/html", html);

  if (wifiChanged && apMode) {
    delay(3000);
    ESP.restart();
  }
}

// ============ HELPERS ============
void setAllLeds(uint32_t color) {
  for (int i = 0; i < NUM_LEDS; i++) {
    ring.setPixelColor(i, color);
  }
}
