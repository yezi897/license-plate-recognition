"""
ESP32-S3 串口诊断脚本
用法: python test_serial.py COM4
"""
import sys
import time
import serial


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "COM4"
    baud = 115200

    print(f"连接 {port} @ {baud}...")
    try:
        ser = serial.Serial(port, baud, timeout=2)
    except Exception as e:
        print(f"连接失败: {e}")
        return

    time.sleep(0.5)

    # 1. 读取启动信息
    print("\n=== 读取启动信息 (2秒) ===")
    start = time.time()
    while time.time() - start < 2:
        if ser.in_waiting:
            line = ser.readline().decode("utf-8", errors="replace").strip()
            if line:
                print(f"  RX: {line}")
        time.sleep(0.01)

    # 2. 发送 'C' 指令 (拍照)
    print("\n=== 发送 'C' (拍照指令) ===")
    ser.reset_input_buffer()
    ser.write(b"C")

    start = time.time()
    buffer = b""
    found = False
    while time.time() - start < 10:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            buffer += chunk
        time.sleep(0.01)

        if b"IMG_START" in buffer and not found:
            found = True
            idx = buffer.find(b"IMG_START")
            print(f"  收到 IMG_START (偏移 {idx}), 累计 {len(buffer)} 字节")

        if found:
            idx = buffer.find(b"IMG_START")
            len_start = idx + 9
            if len(buffer) >= len_start + 4:
                img_len = int.from_bytes(buffer[len_start:len_start + 4], "little")
                print(f"  图片长度: {img_len} 字节")
                data_start = len_start + 4
                data_end = data_start + img_len
                if len(buffer) >= data_end:
                    img = buffer[data_end - 10:data_end]
                    print(f"  图片接收完成! 尾部: {img.hex()}")
                    break

    if not found:
        elapsed = time.time() - start
        print(f"  超时 ({elapsed:.1f}s), 收到 {len(buffer)} 字节")
        if buffer:
            print(f"  前200字节: {buffer[:200]}")

    # 3. 发送 'S' 指令 (视频帧)
    print("\n=== 发送 'S' (视频帧指令) ===")
    ser.reset_input_buffer()
    ser.write(b"S")

    start = time.time()
    buffer = b""
    found = False
    while time.time() - start < 5:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            buffer += chunk
        time.sleep(0.01)

        if b"IMG_START" in buffer and not found:
            found = True
            print(f"  收到 IMG_START, 累计 {len(buffer)} 字节")
            break

    if not found:
        elapsed = time.time() - start
        print(f"  超时 ({elapsed:.1f}s), 收到 {len(buffer)} 字节")
        if buffer:
            print(f"  前200字节: {buffer[:200]}")

    ser.close()
    print("\n完成.")


if __name__ == "__main__":
    main()
