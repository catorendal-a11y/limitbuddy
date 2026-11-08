#include "idle_dim.h"
#include "backlight.h"
#include "../app_settings.h"
#include <Arduino.h>
#include "night_mode.h"
#include "brightness_fade.h"
#include <lvgl.h>

static IdleDimPolicy policy;
static uint32_t nightLastTouch = 0;
static bool nightTouched = false;
static BrightnessFade fade;
static const char* mode = "NORMAL";
const char* idle_dim_mode() { return mode; }
// Night hours add a faint amber veil above every screen to cut blue light. It never takes touches
// and changes only when night starts or ends.
static lv_obj_t* warm = nullptr;
static bool warmShown = false;
static void apply_warm(bool show) {
  if (show == warmShown) return;
  warmShown = show;
  if (!warm) {
    warm = lv_obj_create(lv_layer_sys()); lv_obj_remove_style_all(warm);
    lv_obj_set_size(warm, LV_PCT(100), LV_PCT(100));
    lv_obj_set_style_bg_color(warm, lv_color_hex(0xFF7A1A), 0); lv_obj_set_style_bg_opa(warm, 36, 0);
    lv_obj_set_clickable(warm, false); lv_obj_set_scrollable(warm, false);
  }
  lv_obj_set_hidden(warm, !show);
}
lv_obj_t* idle_dim_warm_overlay() { return warm; }
void idle_dim_update() {
  uint8_t recovered = 0;
  if (app_settings::take_initial_brightness(recovered)) display_apply_brightness(recovered, false);
  const uint32_t now = millis();
  const uint8_t selected = display_get_brightness();
  const uint8_t base = nightTouched && now - nightLastTouch < 60000u ? selected :
                       night_brightness(aim::read(), now, selected, app_settings::night());
  const uint8_t target = policy.update(now, base, app_settings::dim_minutes());
  mode = policy.dimmed() ? "IDLE" : (base < selected ? "NIGHT" : "NORMAL");
  apply_warm(night_active(aim::read(), now, app_settings::night()));
  display_set_brightness(fade.update(now, target, display_get_applied_brightness()));
}
bool idle_dim_touch(bool pressed) {
  if (pressed && display_get_brightness() < brightness_raw(5)) policy.preview();
  const bool accepted = policy.touch(millis(), pressed);
  if (pressed) {
    nightLastTouch = millis(); nightTouched = true;
    if (display_get_brightness() < brightness_raw(5)) display_apply_brightness(brightness_raw(5), false);
    else display_set_brightness(display_get_brightness());
    fade.reset(millis(), display_get_brightness());
    mode = "NORMAL";
  }
  return accepted;
}
void idle_dim_preview() { policy.preview(); idle_dim_update(); }
void idle_dim_alert() { policy.alert(millis()); idle_dim_update(); }
