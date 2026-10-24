"""Apply the Cybot changes to a clean Marlin Configuration.h / Configuration_adv.h.
Each entry is (file, exact old line, new line); every edit must match exactly once, so a
Marlin update that moves or renames a define fails loudly here instead of silently
building a printer. Run by build.sh after resetting upstream/Marlin/Configuration*.h."""
import sys, pathlib
UP = pathlib.Path(__file__).resolve().parent / "upstream" / "Marlin"
C, A = "Configuration.h", "Configuration_adv.h"
# Octopus Pro V1.1 (STM32H723) slot map: MOTOR0 X=J1, MOTOR1 Y=J2 (NEMA23), MOTOR2 Z=J3 (NEMA23),
# MOTOR3 unused (Z2), MOTOR4 I/A=J4, MOTOR5 J/B=J5, MOTOR6 K/C=J6, MOTOR7 free (gripper as U later).
# Steps per degree = 200 steps x 16 microsteps x total ratio / 360. J1 is the printed 27T on the
# 179T band (bench-checked 2026-10-22 over five turns). J4 is 88:1 with a 20T motor pulley, found
# by marking full turns 2026-10-24. The J6 belt ratio is a placeholder.
EDITS = [
    (C, "  #define MOTHERBOARD BOARD_RAMPS_14_EFB", "  #define MOTHERBOARD BOARD_BTT_OCTOPUS_PRO_V1_1"),
    (C, "#define SERIAL_PORT 0", "#define SERIAL_PORT -1"),                       # USB
    (C, "//#define SERIAL_PORT_2 -1", "#define SERIAL_PORT_2 1"),                # TFT header UART, for the Heltec
    (C, '//#define CUSTOM_MACHINE_NAME "3D Printer"', '#define CUSTOM_MACHINE_NAME "Cybot"'),
    (C, "#define X_DRIVER_TYPE  A4988", "#define X_DRIVER_TYPE  TMC2209"),
    (C, "#define Y_DRIVER_TYPE  A4988", "#define Y_DRIVER_TYPE  TMC5160"),
    (C, "#define Z_DRIVER_TYPE  A4988", "#define Z_DRIVER_TYPE  TMC5160"),
    (C, "//#define I_DRIVER_TYPE  A4988", "#define I_DRIVER_TYPE  TMC2209"),
    (C, "//#define J_DRIVER_TYPE  A4988", "#define J_DRIVER_TYPE  TMC2209"),
    (C, "//#define K_DRIVER_TYPE  A4988", "#define K_DRIVER_TYPE  TMC2209"),
    (C, "#define EXTRUDERS 1", "#define EXTRUDERS 0"),
    (C, "#define TEMP_SENSOR_0 1", "#define TEMP_SENSOR_0 0"),
    (C, "#define TEMP_SENSOR_BED 1", "#define TEMP_SENSOR_BED 0"),
    (C, "#define DEFAULT_AXIS_STEPS_PER_UNIT   { 80, 80, 400, 500 }",
        "#define DEFAULT_AXIS_STEPS_PER_UNIT   { 58.93, 306.67, 266.67, 782.22, 97.78, 88.89 }  // steps/deg: J1 179/27, J2 1.5x23, J3 1.5x20, J4 88 (bench), J5 11, J6 (TBD)"),
    (C, "#define DEFAULT_MAX_FEEDRATE          { 300, 300, 5, 25 }", "#define DEFAULT_MAX_FEEDRATE          { 30, 20, 20, 45, 45, 60 }  // deg/s"),
    (C, "#define DEFAULT_MAX_ACCELERATION      { 3000, 3000, 100, 10000 }", "#define DEFAULT_MAX_ACCELERATION      { 60, 40, 40, 90, 90, 120 }  // deg/s^2"),
    (C, "#define DEFAULT_ACCELERATION          3000    // X, Y, Z and E acceleration for printing moves",
        "#define DEFAULT_ACCELERATION          40      // deg/s^2"),
    (C, "#define DEFAULT_TRAVEL_ACCELERATION   3000    // X, Y, Z acceleration for travel (non printing) moves",
        "#define DEFAULT_TRAVEL_ACCELERATION   40      // deg/s^2"),
    (C, "#define INVERT_Y_DIR true", "#define INVERT_Y_DIR false"),
    (C, "//#define INVERT_I_DIR false", "#define INVERT_I_DIR false"),
    (C, "//#define INVERT_J_DIR false", "#define INVERT_J_DIR false"),
    (C, "//#define INVERT_K_DIR false", "#define INVERT_K_DIR false"),
    (C, "//#define I_HOME_DIR -1", "#define I_HOME_DIR -1"),
    (C, "//#define J_HOME_DIR -1", "#define J_HOME_DIR -1"),
    (C, "//#define K_HOME_DIR -1", "#define K_HOME_DIR -1"),
    (C, "#define X_MIN_POS 0", "#define X_MIN_POS -180"),
    (C, "#define Y_MIN_POS 0", "#define Y_MIN_POS -90"),
    (C, "#define Z_MIN_POS 0", "#define Z_MIN_POS -150"),
    (C, "#define X_MAX_POS X_BED_SIZE", "#define X_MAX_POS 180"),
    (C, "#define Y_MAX_POS Y_BED_SIZE", "#define Y_MAX_POS 90"),
    (C, "#define Z_MAX_POS 200", "#define Z_MAX_POS 150"),
    (C, "//#define I_MIN_POS 0", "#define I_MIN_POS -180"),
    (C, "//#define I_MAX_POS 50", "#define I_MAX_POS 180"),
    (C, "//#define J_MIN_POS 0", "#define J_MIN_POS -120"),
    (C, "//#define J_MAX_POS 50", "#define J_MAX_POS 120"),
    (C, "//#define K_MIN_POS 0", "#define K_MIN_POS -180"),
    (C, "//#define K_MAX_POS 50", "#define K_MAX_POS 180"),
    # bench: no homing, no software limits until joint zeros exist
    (C, "#define MIN_SOFTWARE_ENDSTOPS", "//#define MIN_SOFTWARE_ENDSTOPS"),
    (C, "#define MAX_SOFTWARE_ENDSTOPS", "//#define MAX_SOFTWARE_ENDSTOPS"),
    (C, "#define HOMING_FEEDRATE_MM_M { (50*60), (50*60), (4*60) }", "#define HOMING_FEEDRATE_MM_M { (10*60), (10*60), (10*60), (10*60), (10*60), (10*60) }"),
    (C, "//#define EEPROM_SETTINGS     // Persistent storage with M500 and M501", "#define EEPROM_SETTINGS     // Persistent storage with M500 and M501"),
    (C, "  //#define EEPROM_AUTO_INIT  // Init EEPROM automatically on any errors.", "  #define EEPROM_AUTO_INIT  // Init EEPROM automatically on any errors."),
    # drivers: hold the arm forever, spreadCycle for torque, currents per motor (RMS)
    (A, "#define DEFAULT_STEPPER_TIMEOUT_SEC 120", "#define DEFAULT_STEPPER_TIMEOUT_SEC 0"),
    (A, "    #define X_CURRENT       800        // (mA) RMS current. Multiply by 1.414 for peak current.",
        "    #define X_CURRENT      1200        // (mA) RMS; 17HS8401B rated 1.8 A peak"),
    (A, "    #define Y_CURRENT       800", "    #define Y_CURRENT      2000        // 23HS22-2804S rated 2.8 A peak"),
    (A, "    #define Z_CURRENT       800", "    #define Z_CURRENT      2000"),
    (A, "    #define Y_RSENSE          0.11", "    #define Y_RSENSE          0.075     // BTT TMC5160: verify against the module"),
    (A, "    #define Z_RSENSE          0.11", "    #define Z_RSENSE          0.075"),
    (A, "    #define I_CURRENT      800", "    #define I_CURRENT     1200"),
    (A, "    #define J_CURRENT      800", "    #define J_CURRENT     1200"),
    (A, "    #define K_CURRENT      800", "    #define K_CURRENT     1200"),
    (A, "    #define STEALTHCHOP_XY", "    //#define STEALTHCHOP_XY"),
    (A, "    #define STEALTHCHOP_Z", "    //#define STEALTHCHOP_Z"),
    (A, "    #define STEALTHCHOP_I", "    //#define STEALTHCHOP_I"),
    (A, "    #define STEALTHCHOP_J", "    //#define STEALTHCHOP_J"),
    (A, "    #define STEALTHCHOP_K", "    //#define STEALTHCHOP_K"),
    (A, "  //#define MONITOR_DRIVER_STATUS", "  #define MONITOR_DRIVER_STATUS"),
    # TMC_DEBUG stays off: its M122 table reads every register of every driver with no watchdog
    # refresh, and the UART timeouts on empty TMC2209 sockets trip the 4 s watchdog (board reset).
    (C, "//#define I_ENABLE_ON LOW", "#define I_ENABLE_ON LOW"),
    (C, "//#define J_ENABLE_ON LOW", "#define J_ENABLE_ON LOW"),
    (C, "//#define K_ENABLE_ON LOW", "#define K_ENABLE_ON LOW"),
    # I/J/K endstops on the board's E0/E1/E2-STOP inputs (unused otherwise); Marlin insists on one per homed axis
    (C, "#define K_HOME_DIR -1", "#define K_HOME_DIR -1\n#define I_STOP_PIN PG12  // E0-STOP\n#define J_STOP_PIN PG13  // E1-STOP\n#define K_STOP_PIN PG14  // E2-STOP"),
    (A, "#define AXIS_RELATIVE_MODES { false, false, false, false }", "#define AXIS_RELATIVE_MODES { false, false, false, false, false, false }"),
    (A, "#define HOMING_BUMP_MM      { 5, 5, 2 }       // (linear=mm, rotational=\u00b0) Backoff from endstops after first bump", "#define HOMING_BUMP_MM      { 2, 2, 2, 2, 2, 2 }"),
    (A, "#define HOMING_BUMP_DIVISOR { 2, 2, 4 }       // Re-Bump Speed Divisor (Divides the Homing Feedrate)", "#define HOMING_BUMP_DIVISOR { 4, 4, 4, 4, 4, 4 }"),
    (C, "#define X_BED_SIZE 200", "#define X_BED_SIZE 360  // no bed; must fit inside the X/Y bounds"),
    (C, "#define Y_BED_SIZE 200", "#define Y_BED_SIZE 180"),
]
for fname, old, new in EDITS:
    p = UP / fname; s = p.read_text()
    n = s.count("\n" + old + "\n")
    if n != 1:
        sys.exit(f"{fname}: expected exactly one line {old!r}, found {n}")
    p.write_text(s.replace("\n" + old + "\n", "\n" + new + "\n", 1))
print(f"configured {len(EDITS)} edits")
