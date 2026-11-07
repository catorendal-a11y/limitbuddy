# Choose your display board

One repository and one Windows x64 terminal package hold two separate firmware builds. In the terminal, open **Settings > Edit settings**, choose the exact board, USB port and providers, then save. New installations preselect no board or provider; configurations without a `board` field keep the original P4 target.

| | GUITION JC4880P433 ESP32-P4 | Original Waveshare ESP32-S3-Touch-LCD-4.3 |
| --- | --- | --- |
| Status | Supported | **Experimental; physical hardware unverified** |
| Screen | ST7701S MIPI DSI, rotated to 800 x 480 | ST7262 RGB, 800 x 480 |
| Host connection | Espressif USB data port | **USB TO UART** connector (CH343 bridge) |
| Build environment | `esp32p4-release` | `esp32s3-waveshare-43-release` |
| Companions | NOVA, ORBIT, CLAUDE, WRAITH, GLITCH | NOVA, ORBIT, CLAUDE (no flash for more) |
| Backlight dimming | Hardware PWM | On/off only; dims via black overlay |
| Bootloader / app offset | `0x2000` / `0x10000` | `0x0` / `0x10000` |

> [!IMPORTANT]
> The S3 build targets the **original CH422G board with 16 MB flash and 8 MB OPI PSRAM**. B, C and similarly named variants are not supported. Verify the model before installing.

Both builds use LVGL 9.6 and share the dashboard, providers, themes, warnings and saved settings, but have independent display drivers and firmware identities. The terminal picks the matching image and esptool chip, verifies file sizes, SHA-256, chip headers and factory/application consistency, and checks board identity in the host handshake. USB vendor IDs only identify candidate ports, so select an explicit port when several appear. Both targets use this project's 16 MB layout; factory images flash at `0x0`. Never apply an application-only update to a board with a different partition layout.

## Waveshare S3 setup

1. Connect a data cable to **USB TO UART**. Use it for flashing and daily operation; the native USB connector is not the transport.
2. **Settings > Edit settings**: choose **Waveshare ESP32-S3-Touch-LCD-4.3**, your providers and the UART COM port, then save. Install the manufacturer's CH343 driver if Windows does not list the bridge.
3. **Device > Firmware**: recheck the board. Use **First installation / factory image** when replacing the demo or another project's firmware; type `FLASH` only after checking board and port.
4. **Settings > Start host**. If flashing cannot connect, follow Waveshare's BOOT/RESET recovery for this exact model. Stop the host and close serial monitors before flashing.

## Brightness and performance

The S3 exposes its backlight through CH422G EXIO2 as an **on/off switch**. Brightness presets, fades and the night schedule therefore attenuate the image with a black overlay (touch passes through; it stays above dashboard, settings and alerts); zero switches the LEDs off. Intermediate values do not reduce LED power like PWM.

The S3 backend uses one PSRAM framebuffer, two 10-line RGB bounce buffers and one 20-line LVGL draw buffer, and pins Arduino 3.2.0 with Espressif's matching high-performance SDK (PSRAM XIP; a compile-time guard rejects other cache configurations). The P4 SDK is independent. A single RGB framebuffer can tear during updates.

> [!NOTE]
> Smoothness, touch alignment, cold boot, USB reconnect, long operation and persistence while RGB scans still need a physical S3 test. Passing native UI tests or compiling does not establish them.

## References

- [Waveshare board documentation](https://docs.waveshare.com/ESP32-S3-Touch-LCD-4.3) and [FAQ](https://docs.waveshare.com/ESP32-S3-Touch-LCD-4.3/FAQ)
- [Official pin/timing profile, ESP32 Display Panel v1.0.4](https://github.com/esp-arduino-libs/ESP32_Display_Panel/blob/v1.0.4/src/board/supported/waveshare/BOARD_WAVESHARE_ESP32_S3_TOUCH_LCD_4_3.h)
- [WCH CH422 datasheet](https://files.waveshare.com/wiki/common/CH422DS1_EN.pdf): system address `0x24`, output bank `0x38` (7-bit I2C); EXIO1 touch reset, EXIO2 backlight, EXIO3 LCD reset, EXIO5 USB/CAN selection
- [Espressif RGB LCD driver and bounce buffers](https://docs.espressif.com/projects/esp-idf/en/v5.5.2/esp32s3/api-reference/peripherals/lcd/rgb_lcd.html)
- [Matching high-performance Arduino SDK](https://github.com/esp-arduino-libs/arduino-esp32-sdk)
