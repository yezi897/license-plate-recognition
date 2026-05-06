#include "esp_camera.h"
#include "Arduino.h"

// ESP32-CAM (AI Thinker) 引脚定义
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// 闪光灯
#define FLASH_GPIO_NUM     4

void setup() {
  Serial.begin(921600);
  Serial.setDebugOutput(true);

  // 初始化摄像头
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_LATEST;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // 根据 PSRAM 调整分辨率
  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;  // 640x480
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;  // 320x240
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("摄像头初始化失败: 0x%x\n", err);
    return;
  }

  // 设置摄像头参数
  sensor_t *s = esp_camera_sensor_get();
  s->set_brightness(s, 1);
  s->set_contrast(s, 1);

  // 初始化闪光灯
  pinMode(FLASH_GPIO_NUM, OUTPUT);
  digitalWrite(FLASH_GPIO_NUM, LOW);

  Serial.println("READY");
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'C') {
      captureAndSend();
    } else if (cmd == 'F') {
      flashCapture();
    }
  }
}

void captureAndSend() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("CAPTURE_FAIL");
    return;
  }

  // 发送帧头标记
  Serial.write("IMG_START");
  // 发送图片长度（4字节）
  uint32_t len = fb->len;
  Serial.write((uint8_t)(len & 0xFF));
  Serial.write((uint8_t)((len >> 8) & 0xFF));
  Serial.write((uint8_t)((len >> 16) & 0xFF));
  Serial.write((uint8_t)((len >> 24) & 0xFF));
  // 发送图片数据
  Serial.write(fb->buf, fb->len);
  // 发送帧尾标记
  Serial.write("IMG_END");

  esp_camera_fb_return(fb);
}

void flashCapture() {
  digitalWrite(FLASH_GPIO_NUM, HIGH);
  delay(100);
  captureAndSend();
  digitalWrite(FLASH_GPIO_NUM, LOW);
}
