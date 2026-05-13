#include <Arduino.h>
#include <esp_camera.h>
#include <WiFi.h>
#include <Preferences.h>
#include <WiFiServer.h>

// ESP32-S3-CAM 引脚定义 (Arduino 官方 ESP32S3_EYE 配置)
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     15
#define SIOD_GPIO_NUM      4
#define SIOC_GPIO_NUM      5
#define Y9_GPIO_NUM       16
#define Y8_GPIO_NUM       17
#define Y7_GPIO_NUM       18
#define Y6_GPIO_NUM       12
#define Y5_GPIO_NUM       10
#define Y4_GPIO_NUM        8
#define Y3_GPIO_NUM        9
#define Y2_GPIO_NUM       11
#define VSYNC_GPIO_NUM     6
#define HREF_GPIO_NUM      7
#define PCLK_GPIO_NUM     13

#define TCP_PORT 8080
#define WIFI_TIMEOUT_MS 15000

bool cameraReady = false;
bool wifiConnected = false;
Preferences prefs;
WiFiServer tcpServer(TCP_PORT);
WiFiClient tcpClient;

// ========== 摄像头初始化（与串口版相同） ==========

bool initCamera() {
  if (cameraReady) return true;

  delay(50);

  camera_config_t config;
  memset(&config, 0, sizeof(config));
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.xclk_freq_hz = 12000000;
  config.ledc_timer = LEDC_TIMER_0;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 15;
  config.fb_count = 2;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_LATEST;

  esp_err_t err = ESP_FAIL;
  for (int retry = 0; retry < 3; retry++) {
    err = esp_camera_init(&config);
    if (err == ESP_OK) break;
    if (retry < 2) delay(100);
  }
  if (err != ESP_OK) {
    return false;
  }

  sensor_t *s = esp_camera_sensor_get();
  s->set_reg(s, 0x11, 0xFF, 0x01);
  s->set_reg(s, 0x13, 0x07, 0x00);
  s->set_reg(s, 0x10, 0xFF, 0x40);
  s->set_reg(s, 0x00, 0xFF, 0x10);
  delay(100);

  cameraReady = true;
  return true;
}

// ========== WiFi 连接 ==========

bool connectWiFi() {
  prefs.begin("wifi", true);  // 只读
  String ssid = prefs.getString("ssid", "");
  String password = prefs.getString("password", "");
  prefs.end();

  if (ssid.length() == 0) {
    Serial.println("WIFI_NO_CREDENTIALS");
    return false;
  }

  Serial.print("WIFI_CONNECTING ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid.c_str(), password.c_str());

  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - startTime > WIFI_TIMEOUT_MS) {
      Serial.println("WIFI_FAIL");
      WiFi.disconnect();
      return false;
    }
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("WIFI_OK ");
  Serial.println(WiFi.localIP().toString());
  return true;
}

// ========== TCP 发送帧 ==========

void sendFrameTCP(camera_fb_t *fb) {
  if (!tcpClient || !tcpClient.connected()) return;

  tcpClient.write("IMG_START", 9);
  uint32_t len = fb->len;
  uint8_t lenBuf[4] = {
    (uint8_t)(len & 0xFF),
    (uint8_t)((len >> 8) & 0xFF),
    (uint8_t)((len >> 16) & 0xFF),
    (uint8_t)((len >> 24) & 0xFF)
  };
  tcpClient.write(lenBuf, 4);

  // TCP 不需要分块，直接发送
  tcpClient.write(fb->buf, fb->len);
  tcpClient.flush();
}

// ========== 串口发送帧（配置阶段使用） ==========

void sendFrameSerial(camera_fb_t *fb) {
  Serial.write("IMG_START");
  uint32_t len = fb->len;
  Serial.write((uint8_t)(len & 0xFF));
  Serial.write((uint8_t)((len >> 8) & 0xFF));
  Serial.write((uint8_t)((len >> 16) & 0xFF));
  Serial.write((uint8_t)((len >> 24) & 0xFF));
  Serial.flush();

  const size_t CHUNK_SIZE = 256;
  size_t offset = 0;
  while (offset < fb->len) {
    size_t toWrite = min(CHUNK_SIZE, fb->len - offset);
    Serial.write(fb->buf + offset, toWrite);
    Serial.flush();
    delay(5);
    offset += toWrite;
  }
}

// ========== 处理串口命令（WiFi 凭据配置） ==========

void handleSerialCommand() {
  // 收到 'W' 命令后，读取 "SSID\nPASSWORD\n"
  // 等待完整数据到达
  unsigned long deadline = millis() + 5000;
  while (millis() < deadline) {
    if (Serial.available() >= 2) break;  // 至少有 SSID 一个字符 + \n
    delay(10);
  }

  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.length() == 0) {
    Serial.println("WIFI_SAVE_FAIL: empty SSID");
    return;
  }
  String ssid = line;

  deadline = millis() + 5000;
  while (millis() < deadline) {
    if (Serial.available() > 0) break;
    delay(10);
  }

  String password = Serial.readStringUntil('\n');
  password.trim();

  // 保存到 Preferences
  prefs.begin("wifi", false);  // 读写
  prefs.putString("ssid", ssid);
  prefs.putString("password", password);
  prefs.end();

  Serial.print("WIFI_SAVED ");
  Serial.println(ssid);
  Serial.println("WIFI_RESTARTING");

  delay(500);
  ESP.restart();
}

// ========== setup ==========

void setup() {
  Serial.begin(115200);
  pinMode(47, OUTPUT);
  digitalWrite(47, LOW);
  delay(1000);

  Serial.println("READY_WIFI");

  // 尝试连接 WiFi
  wifiConnected = connectWiFi();

  if (wifiConnected) {
    tcpServer.begin();
    tcpServer.setNoDelay(true);
    Serial.println("TCP_SERVER_STARTED");
  }
}

// ========== loop ==========

void loop() {
  // 检查串口命令（WiFi 凭据配置）
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'W') {
      handleSerialCommand();
      return;
    }
    // 串口模式下也支持拍照（用于配置阶段测试）
    if (cmd == 'C' || cmd == 'S' || cmd == 'F') {
      if (!cameraReady) {
        if (!initCamera()) {
          Serial.println("CAMERA_FAIL");
          return;
        }
      }
      sensor_t *s = esp_camera_sensor_get();
      if (cmd == 'C' || cmd == 'F') {
        s->set_quality(s, 12);
      }
      if (cmd == 'F') {
        digitalWrite(47, HIGH);
        delay(100);
      }
      camera_fb_t *fb = esp_camera_fb_get();
      if (cmd == 'F') {
        digitalWrite(47, LOW);
      }
      if (!fb) {
        Serial.println("CAPTURE_FAIL");
        s->set_quality(s, 30);
        return;
      }
      sendFrameSerial(fb);
      esp_camera_fb_return(fb);
      s->set_quality(s, 30);
    }
  }

  // WiFi 模式: TCP 服务
  if (wifiConnected) {
    // 接受新的 TCP 客户端
    if (!tcpClient || !tcpClient.connected()) {
      WiFiClient newClient = tcpServer.available();
      if (newClient) {
        tcpClient = newClient;
        tcpClient.setNoDelay(true);
        Serial.println("TCP_CLIENT_CONNECTED");
      }
    }

    // 处理 TCP 客户端命令
    if (tcpClient && tcpClient.connected() && tcpClient.available()) {
      char cmd = tcpClient.read();

      if (cmd == 'C' || cmd == 'S' || cmd == 'F') {
        if (!cameraReady) {
          if (!initCamera()) {
            tcpClient.println("CAMERA_FAIL");
            return;
          }
        }
        sensor_t *s = esp_camera_sensor_get();
        if (cmd == 'C' || cmd == 'F') {
          s->set_quality(s, 12);
        }
        if (cmd == 'F') {
          digitalWrite(47, HIGH);
          delay(100);
        }
        camera_fb_t *fb = esp_camera_fb_get();
        if (cmd == 'F') {
          digitalWrite(47, LOW);
        }
        if (!fb) {
          tcpClient.println("CAPTURE_FAIL");
          s->set_quality(s, 30);
          return;
        }
        sendFrameTCP(fb);
        esp_camera_fb_return(fb);
        s->set_quality(s, 30);
      }
    }
  }
}
