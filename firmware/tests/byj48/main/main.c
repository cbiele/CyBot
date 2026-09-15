// 28BYJ-48 on a ULN2003 board: one output revolution each way, forever.
// Half-step sequence, 4096 half-steps per output revolution (64:1 nominal gearbox).
#include <stdio.h>
#include "driver/gpio.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"

static const gpio_num_t COIL[4] = {CONFIG_BYJ_IN1, CONFIG_BYJ_IN2, CONFIG_BYJ_IN3, CONFIG_BYJ_IN4};
static const uint8_t HALF_STEP[8] = {0b0001, 0b0011, 0b0010, 0b0110, 0b0100, 0b1100, 0b1000, 0b1001};
#define STEPS_PER_REV 4096

static void set_phase(int idx)
{
    for (int c = 0; c < 4; c++) gpio_set_level(COIL[c], (HALF_STEP[idx & 7] >> c) & 1);
}

static void spin(int steps, int dir)
{
    static int phase = 0;
    int64_t next = esp_timer_get_time();
    for (int i = 0; i < steps; i++) {
        phase = (phase + dir) & 7;
        set_phase(phase);
        next += CONFIG_BYJ_STEP_US;
        int64_t now = esp_timer_get_time();
        if (next > now) {
            int64_t wait = next - now;
            if (wait > 2000) vTaskDelay(pdMS_TO_TICKS(wait / 1000));
            while (esp_timer_get_time() < next) {}
        }
    }
    for (int c = 0; c < 4; c++) gpio_set_level(COIL[c], 0);   // coils off: no heat while idle
}

void app_main(void)
{
    for (int c = 0; c < 4; c++) {
        gpio_reset_pin(COIL[c]);
        gpio_set_direction(COIL[c], GPIO_MODE_OUTPUT);
        gpio_set_level(COIL[c], 0);
    }
    printf("28BYJ-48 test: IN1..IN4 on GPIO %d %d %d %d, %d us per half-step\n",
           CONFIG_BYJ_IN1, CONFIG_BYJ_IN2, CONFIG_BYJ_IN3, CONFIG_BYJ_IN4, CONFIG_BYJ_STEP_US);
    for (int rev = 1;; rev++) {
        printf("rev %d: clockwise\n", rev);
        spin(STEPS_PER_REV, +1);
        vTaskDelay(pdMS_TO_TICKS(500));
        printf("rev %d: counter-clockwise\n", rev);
        spin(STEPS_PER_REV, -1);
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}
