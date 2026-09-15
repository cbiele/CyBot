# 28BYJ-48 + ULN2003 test

Proves a board, its toolchain and four GPIOs by turning the little geared
stepper one revolution each way, forever. Not part of the arm: the arm
never drives coils from GPIOs.

## Wiring (ESP32 DevKit V1)

| DevKit | ULN2003 board |
|---|---|
| GPIO16 | IN1 |
| GPIO17 | IN2 |
| GPIO18 | IN3 |
| GPIO19 | IN4 |
| VIN (USB 5 V) | + (VCC) |
| GND | - (GND) |

The 5-pin motor plug goes on the ULN2003 board as supplied. The board's
inputs switch at 3.3 V. Pins avoid the strapping pins (0, 2, 12, 15) and
the input-only 34-39.

## Build and run

```
. ~/esp/esp-idf/export.sh
cd firmware/tests/byj48
idf.py set-target esp32
idf.py build flash monitor      # add -p /dev/tty.usbserial-XXXX if it does not find the port
```

The console prints the pin map and "rev N: clockwise / counter-clockwise".
One revolution takes about 8 s at the default 2000 us half-step. Pins and
speed live under `idf.py menuconfig` -> "28BYJ-48 test".

## Heltec WiFi LoRa 32 V4 variant

`idf.py set-target esp32s3`, then set the pins to 38, 39, 40, 41 (the GNSS
port; never 34, it drives the GNSS power FET) and take 5 V from VBUS with a
USB cable plugged in. Same code, proves the GNSS pigtail.
