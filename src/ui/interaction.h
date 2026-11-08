#pragma once
#include <lvgl.h>

namespace ui_interaction {
// A finger owns one target until release. Sliding off cancels that target and
// suppresses new activations even if the same finger enters another button.
// Sliders deliberately retain their own continuous-drag interaction.
inline void cancel_dragged_press(lv_event_t* event) {
  auto* input = lv_indev_active();
  if (!input || lv_indev_get_type(input) != LV_INDEV_TYPE_POINTER) return;
  auto* object = lv_event_get_target_obj(event);
  lv_point_t point{}; lv_indev_get_point(input, &point);
  lv_area_t area{}; lv_obj_get_coords(object, &area);
  if (point.x >= area.x1 && point.x <= area.x2 && point.y >= area.y1 && point.y <= area.y2) return;
  lv_indev_wait_release(input);
  // Restore a cancelled editable draft immediately, rather than displaying
  // an unsaved value until the user eventually lifts the finger.
  lv_obj_send_event(object, LV_EVENT_PRESS_LOST, input);
}
// LVGL still sends CLICKED after a swipe that stayed on one target; page swipes must not open it.
inline bool swiped() {
  auto* input = lv_indev_active();
  return input && lv_indev_get_gesture_dir(input) != LV_DIR_NONE;
}
// After a page swipe, cards glide in from the swipe side and stop at their fixed position.
inline void slide_in(lv_obj_t* object, int32_t from) {
  lv_anim_t anim; lv_anim_init(&anim);
  lv_anim_set_var(&anim, object); lv_anim_set_values(&anim, from, 0); lv_anim_set_duration(&anim, 180);
  lv_anim_set_path_cb(&anim, lv_anim_path_ease_out);
  lv_anim_set_exec_cb(&anim, [](void* target, int32_t value) {
    lv_obj_set_style_translate_x(static_cast<lv_obj_t*>(target), value, 0);
  });
  lv_anim_start(&anim);
}
inline int32_t slide_from(lv_dir_t direction) { return direction == LV_DIR_LEFT ? 60 : -60; }
inline void keep_target(lv_obj_t* object) {
  lv_obj_set_press_lock(object, true);
  lv_obj_add_event_cb(object, cancel_dragged_press, LV_EVENT_PRESSING, nullptr);
}
}
