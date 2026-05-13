#include <Arduino.h>
#include <esp_camera.h>

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

bool cameraReady = false;

// 固定使用 VGA 分辨率，避免动态切换分辨率导致的不可靠问题
// 流式预览: 高压缩 (quality=30) → 较小文件 ~3-5KB
// 拍照识别: 低压缩 (quality=10) → 较大文件 ~10-20KB

bool initCamera() {
  if (cameraReady) return true;

  // 等待 XCLK 稳定（≥50ms），避免 I2C 配置因时钟未锁相失败
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
  config.xclk_freq_hz = 12000000;    // 12MHz，提升 OV2640 稳定性
  config.ledc_timer = LEDC_TIMER_0;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;  // 固定 640x480
  config.jpeg_quality = 15;           // 平衡清晰度与实时性（12-25）
  config.fb_count = 2;                // 双缓冲提升性能
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_LATEST;

  // 重试初始化，最多 3 次
  esp_err_t err = ESP_FAIL;
  for (int retry = 0; retry < 3; retry++) {
    err = esp_camera_init(&config);
    if (err == ESP_OK) break;
    if (retry < 2) delay(100);  // I2C 重试间隔
  }
  if (err != ESP_OK) {
    return false;
  }

  // 设置 OV2640 CLKRC 寄存器 = 0x01（1 分频，最高时钟频率）
  sensor_t *s = esp_camera_sensor_get();
  s->set_reg(s, 0x11, 0xFF, 0x01);  // CLKRC register: 1 division

  // 禁用自动曝光和自动白平衡，避免帧率不稳定
  // COM8 寄存器 (0x13): bit0=AWB, bit1=AE, bit2=AGC
  s->set_reg(s, 0x13, 0x07, 0x00);  // 禁用 AE, AWB, AGC
  // 设置固定曝光值（高字节）
  s->set_reg(s, 0x10, 0xFF, 0x40);  // AECH - 曝光高字节
  // 设置固定增益
  s->set_reg(s, 0x00, 0xFF, 0x10);  // GAIN - 固定增益
  delay(100);

  cameraReady = true;
  return true;
}

void sendFrame(camera_fb_t *fb) {
  Serial.write("IMG_START");
  uint32_t len = fb->len;
  Serial.write((uint8_t)(len & 0xFF));
  Serial.write((uint8_t)((len >> 8) & 0xFF));
  Serial.write((uint8_t)((len >> 16) & 0xFF));
  Serial.write((uint8_t)((len >> 24) & 0xFF));
  Serial.flush();

  // 分块发送，小块 + flush + delay，避免 USB CDC 缓冲区溢出
  const size_t CHUNK_SIZE = 256;
  size_t offset = 0;
  while (offset < fb->len) {
    size_t toWrite = min(CHUNK_SIZE, fb->len - offset);
    Serial.write(fb->buf + offset, toWrite);
    Serial.flush();
    delay(5);
    offset += toWrite;
  }

  Serial.write("IMG_END");
  Serial.flush();
}

void setup() {
  Serial.begin(921600);
  pinMode(47, OUTPUT);
  digitalWrite(47, LOW);
  delay(2000);
  Serial.println("READY");
  Serial.flush();
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();

    if (cmd == 'C' || cmd == 'F') {
      // 拍照识别：低压缩高质量
      if (!cameraReady) {
        if (!initCamera()) {
          Serial.println("CAMERA_FAIL");
          return;
        }
      }
      // 只切换质量，不切换分辨率
      sensor_t *s = esp_camera_sensor_get();
      s->set_quality(s, 12);  // 平衡清晰度与速度（10太慢，12-25最佳）

      // 闪光灯模式
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
        s->set_quality(s, 30);  // 切回流式质量
        return;
      }
      sendFrame(fb);
      esp_camera_fb_return(fb);

      // 切回流式质量
      s->set_quality(s, 30);

    } else if (cmd == 'S') {
      // 流式预览：高压缩快速
      if (!cameraReady) {
        if (!initCamera()) {
          Serial.println("CAMERA_FAIL");
          return;
        }
      }
      camera_fb_t *fb = esp_camera_fb_get();
      if (!fb) {
        Serial.println("CAPTURE_FAIL");
        return;
      }
      sendFrame(fb);
      esp_camera_fb_return(fb);
    }
  }
}
