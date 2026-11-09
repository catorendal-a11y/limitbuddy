// AI Monitor P4 - Dashboard (v2 design)
// Pixel-matched to the user's ui_dashboard_preview_v2.svg:
//   header 78 px with eyebrow title, live dot + halo, 26 px clock, gear SET
//   button; two cards with provider-colored spine, letter badge, vendor meta,
//   "REMAINING" column, window meta rows, 30 px percentages with LEFT unit,
//   pill bars with light end-knob; system bar footer.
// Two full-size cards per page by default; the user may choose one card, or four compact cards,
// and hide AIs (MENU > SETTINGS > CARDS). Extra providers use pages.

#include "dashboard.h"

#include <Arduino.h>
#include <lvgl.h>

#include <cstdio>
#include <cstring>
#include <algorithm>
#include <initializer_list>

#include "ai_monitor/ai_monitor.h"
#include "ui/backlight.h"
#include "ui/theme.h"
#include "ui/usage_format.h"
#include "ui/token_status.h"
#include "ui/session_status.h"
#include "ui/interaction.h"
#include "ui/navigation.h"
#include "ui/quota_alert.h"
#include "ui/quota_headline.h"
#include "ui/quota_state.h"
#include "ui_usage_details.h"
#include "ui_nova.h"
#include "ui/nova_assets.h"
#include "ui_settings.h"
#include "ui_menu.h"
#include "app_settings.h"

// ───────────────────────────────────────────────────────────────────────────────
// V2 PALETTE (from the SVG)
// ───────────────────────────────────────────────────────────────────────────────
static const uint32_t& C_BG = ui_theme::background;
static const uint32_t& C_HEADER = ui_theme::header;
static const uint32_t& C_LINE = ui_theme::border;
static const uint32_t& C_LINE_SOFT = ui_theme::border;
static const uint32_t& C_EYEBROW = ui_theme::muted;
static const uint32_t& C_TITLE = ui_theme::text;
static const uint32_t& C_META = ui_theme::muted;
static const uint32_t& C_META_BRIGHT = ui_theme::muted;
static const uint32_t& C_CARD = ui_theme::surface;
static const uint32_t& C_NAME = ui_theme::text;
static const uint32_t& C_ROWLABEL = ui_theme::text;
static const uint32_t& C_PCT = ui_theme::text;
static const uint32_t& C_UNIT = ui_theme::muted;
static const uint32_t& C_RESET = ui_theme::muted;
static const uint32_t& C_BAR_TRACK = ui_theme::border;
static const uint32_t& C_SET_BG = ui_theme::button;
static const uint32_t& C_SET_BORDER = ui_theme::border;
static const uint32_t& C_GEAR = ui_theme::muted;
static const uint32_t& C_SET_TXT = ui_theme::text;
static const uint32_t& C_FOOTER_BG = ui_theme::header;
static const uint32_t& C_FOOTER_STRONG = ui_theme::text;
static const uint32_t& C_FOOTER = ui_theme::muted;
static const uint32_t& C_GREEN = ui_theme::accent;
static const uint32_t C_RED = 0xFF5252;
static const uint32_t C_AMBER = 0xFFAA00;

#define F_EYEBROW &lv_font_montserrat_18
#define F_META &lv_font_montserrat_16
#define F_ROWLABEL &lv_font_montserrat_22
#define F_PROVIDER &lv_font_montserrat_26
#define F_TIME &lv_font_montserrat_26
#define F_PCT &lv_font_montserrat_30
#define F_BADGE &lv_font_montserrat_22

static constexpr size_t kBigCards = 2;       // side-by-side full-size cards
static constexpr size_t kCompactCards = 4;   // 2 x 2 grid when the user picks four per page
static constexpr uint32_t STALE_MS = aim::kQuotaStaleMs;

// Per-provider v2 styling: brand base, light knob tint, badge colors, vendor.
struct V2Style {
  const char* key;
  uint32_t base;
  uint32_t light;
  uint32_t badgeFill;
  uint32_t badgeStroke;
  uint32_t badgeLetter;
  const char* vendor;
};

static const V2Style* v2_style(const char* key) {
  static const V2Style kTable[] = {
      {"codex", 0x10A37F, 0x74E3C9, 0x102E29, 0x17443B, 0x50D4B5, "OPENAI"},
      {"zcode", 0x14B8A6, 0x75E5D9, 0x10302E, 0x164541, 0x61DDD0, "Z.AI"},
      {"claude", 0xD97757, 0xF2AE91, 0x2E1D14, 0x4A3220, 0xF2AE91, "ANTHROPIC"},
      {"gemini", 0x4285F4, 0x8AB4F8, 0x14202E, 0x1D3050, 0x8AB4F8, "GOOGLE"},
      {"antigravity", 0x4E8CFF, 0x8AB4F8, 0x14202E, 0x1D3050, 0x8AB4F8, "GOOGLE"},
      {"copilot", 0xA371F7, 0xC9ACFB, 0x201A2E, 0x32264A, 0xC9ACFB, "GITHUB"},
      {"cursor", 0x9AD1D4, 0xC4E8EA, 0x1A2628, 0x27393B, 0xC4E8EA, "CURSOR"},
      {"opencode", 0xB9B9C7, 0xDADAE5, 0x202028, 0x34343F, 0xDADAE5, "OPENCODE"},
  };
  for (const auto& s : kTable) {
    if (key && strcmp(s.key, key) == 0) return &s;
  }
  return nullptr;
}

static uint32_t style_base(const V2Style* s) { return s ? s->base : 0xFF6B38; }
static uint32_t style_light(const V2Style* s) { return s ? s->light : 0xFFB380; }
static uint32_t style_badge_fill(const V2Style* s) { return s ? s->badgeFill : 0x1A2429; }
static uint32_t style_badge_stroke(const V2Style* s) { return s ? s->badgeStroke : 0x2A373D; }
static uint32_t style_badge_letter(const V2Style* s) { return s ? s->badgeLetter : 0xC5CED2; }
static const char* style_vendor(const V2Style* s, const char* fallback) {
  return s ? s->vendor : fallback;
}

// ───────────────────────────────────────────────────────────────────────────────
// WIDGETS
// ───────────────────────────────────────────────────────────────────────────────
struct RowWidgets {
  lv_obj_t* divider = nullptr;
  lv_obj_t* winMeta = nullptr;   // "5H WINDOW"
  lv_obj_t* name = nullptr;      // "Session"
  lv_obj_t* pct = nullptr;       // "33%"
  lv_obj_t* unit = nullptr;      // "LEFT"
  lv_obj_t* bar = nullptr;
  lv_obj_t* knob = nullptr;      // light dot at the bar end
  lv_obj_t* pace = nullptr;      // where an even burn would be by now
  lv_obj_t* reset = nullptr;     // "Resets 23:30"
};

struct CardWidgets {
  uint8_t viewIndex = 0;
  char providerKey[16] = {};
  bool compact = false;
  uint8_t layoutRows = 0;
  bool layoutNotice = false;
  lv_obj_t* card = nullptr;
  lv_obj_t* spine = nullptr;
  lv_obj_t* badge = nullptr;
  lv_obj_t* badgeLetter = nullptr;
  lv_obj_t* badgeLogo = nullptr;
  lv_obj_t* name = nullptr;
  lv_obj_t* vendor = nullptr;    // "OPENAI · CONNECTED"
  lv_obj_t* remaining = nullptr; // "REMAINING" / "USED"
  RowWidgets rows[aim::kMaxRows];
};

struct HeaderWidgets {
  lv_obj_t* eyebrow = nullptr;
  lv_obj_t* title = nullptr;
  lv_obj_t* dot = nullptr;
  lv_obj_t* halo = nullptr;
  lv_obj_t* live = nullptr;
  lv_obj_t* clock = nullptr;
};

static HeaderWidgets hdr;
static CardWidgets big[kBigCards];
static CardWidgets compact[kCompactCards];
static lv_obj_t* footDot = nullptr;
static lv_obj_t* footStrong = nullptr;
static lv_obj_t* footFrames = nullptr;
static lv_obj_t* footSync = nullptr;
static lv_obj_t* footServices = nullptr;
static lv_obj_t* hintLabel = nullptr;
static lv_obj_t* dashboardScreen = nullptr;

static void settings_open_cb(lv_event_t* e) {
  (void)e;
  ui_menu_show();
}

bool dashboard_is_active() { return dashboardScreen && lv_screen_active() == dashboardScreen; }

// ───────────────────────────────────────────────────────────────────────────────
// CHANGE-DETECTION CACHES
// ───────────────────────────────────────────────────────────────────────────────
struct RowCaches {
  uint32_t percentColor = 0;
  char winMeta[36];
  char name[48];
  char pct[8];
  char unit[12];
  char reset[48];
  float bar;
  bool knobColorKnown;
  uint32_t knobColor;
};

struct CardCaches {
  const V2Style* style = nullptr;
  bool styleKnown = false;
  char badgeLetter[2];
  uint32_t spine;
  bool spineKnown;
  uint8_t glow = 0xFF;          // 0 healthy, 1 low, 2 critical; 0xFF = not applied yet
  uint32_t glowTheme = UINT32_MAX;
  char name[16];
  char vendor[48];
  char remaining[12];
  RowCaches rows[aim::kMaxRows];
};

static CardCaches bigCache[kBigCards];
static CardCaches compactCache[kCompactCards];
static char liveCache[12] = {0};
static char clockCache[8] = {0};
static char titleCache[64] = {0};
static uint32_t titleColorCache = 0;
static uint32_t liveDotColor = 0;
static char footStrongCache[20] = {0};
static char footFramesCache[24] = {0};
static char footSyncCache[24] = {0};
static char footServicesCache[24] = {0};
static char hintCache[96] = {0};
static uint32_t footDotColor = 0;
static lv_obj_t* pageButton = nullptr;
static lv_obj_t* pageLabel = nullptr;     // "1 / 2 >" kept for screen readers and tests; dots are shown
static lv_obj_t* pageArrow = nullptr;
static lv_obj_t* pageDots[aim::kMaxViews] = {};
static uint8_t dotsPage = UINT8_MAX, dotsCount = UINT8_MAX;
static uint8_t currentPage = 0, pageCount = 1;
static uint32_t lastPageMs = 0, viewRevision = UINT32_MAX;
// bar value/color cache slots: stable index per (layout, card, row)
static float g_barValue[kBigCards + kCompactCards][aim::kMaxRows];
static uint32_t g_barColor[kBigCards + kCompactCards][aim::kMaxRows];

static void set_label_cached(lv_obj_t* lbl, char* cache, size_t cap, const char* text) {
  if (!lbl || (strncmp(cache, text, cap) == 0 && strcmp(lv_label_get_text(lbl), cache) == 0)) return;
  const size_t length = std::min(strlen(text), cap - 1);
  memcpy(cache, text, length);
  cache[length] = '\0';
  lv_label_set_text(lbl, cache);
}

// A bar that ends lighter than it starts reads as filled with light, not as a flat strip.
static uint32_t toward_white(uint32_t color, unsigned percent) {
  uint32_t out = 0;
  for (int shift = 16; shift >= 0; shift -= 8) {
    const uint32_t channel = (color >> shift) & 0xFF;
    out |= (channel + (255 - channel) * percent / 100) << shift;
  }
  return out;
}

static void set_bar_cached(lv_obj_t* bar, size_t slot, size_t row, float pct, uint32_t base) {
  if (!bar) return;
  if (g_barColor[slot][row] != base) {
    lv_obj_set_style_bg_color(bar, lv_color_hex(base), LV_PART_INDICATOR);
    lv_obj_set_style_bg_grad_color(bar, lv_color_hex(toward_white(base, 38)), LV_PART_INDICATOR);
    lv_obj_set_style_bg_grad_dir(bar, LV_GRAD_DIR_HOR, LV_PART_INDICATOR);
    g_barColor[slot][row] = base;
  }
  if (pct < 0.0f) pct = 0.0f;
  if (pct > 100.0f) pct = 100.0f;
  if (g_barValue[slot][row] != pct) {
    lv_bar_set_value(bar, pct, LV_ANIM_OFF);
    g_barValue[slot][row] = pct;
  }
}

// The marker shows where an even burn would stand at this point of the window. A fill that is
// past it (toward the empty end for "left") means the quota is going faster than the window.
static void set_pace(lv_obj_t* pace, lv_obj_t* bar, float progress, bool showsRemaining) {
  if (!pace) return;
  if (progress < 0.0f) {
    if (!lv_obj_is_hidden(pace)) lv_obj_set_hidden(pace, true);
    return;
  }
  const float position = showsRemaining ? 1.0f - progress : progress;
  // Style positions are what was set; lv_obj_get_x() also folds in the parent's border.
  const int32_t x = lv_obj_get_style_x(bar, LV_PART_MAIN) + static_cast<int32_t>(327.0f * position + 0.5f) - 1;
  const int32_t y = lv_obj_get_style_y(bar, LV_PART_MAIN) - 4;
  if (lv_obj_get_style_x(pace, LV_PART_MAIN) != x) lv_obj_set_x(pace, x);
  if (lv_obj_get_style_y(pace, LV_PART_MAIN) != y) lv_obj_set_y(pace, y);
  if (lv_obj_is_hidden(pace)) lv_obj_set_hidden(pace, false);
}

static void set_knob(lv_obj_t* knob, RowCaches& rc, float pct, uint32_t light) {
  if (!knob) return;
  if (!rc.knobColorKnown || rc.knobColor != light) {
    lv_obj_set_style_bg_color(knob, lv_color_hex(light), 0);
    rc.knobColor = light;
    rc.knobColorKnown = true;
  }
  if (pct < 0.0f) pct = 0.0f;
  if (pct > 100.0f) pct = 100.0f;
  int32_t x = (int32_t)(327.0f * pct / 100.0f) - 4;
  if (x < 0) x = 0;
  if (x > 319) x = 319;
  lv_obj_set_pos(knob, x, 2);  // parented to the 12 px bar
}

#include "dashboard_cards.h"

// ───────────────────────────────────────────────────────────────────────────────
// BUILD
// ───────────────────────────────────────────────────────────────────────────────
static void move_page(int step) {
  if (pageCount < 2) return;
  currentPage = static_cast<uint8_t>((currentPage + pageCount + step) % pageCount);
  lastPageMs = millis();
}
static void next_page_cb(lv_event_t*) { move_page(1); }
// Swipe left for the next card page, right for the previous one.
static void swipe_cards(lv_dir_t direction) { if (direction == LV_DIR_LEFT) move_page(1); else if (direction == LV_DIR_RIGHT) move_page(-1); }
void dashboard_update();
static void gesture_cb(lv_event_t*) {
  auto* input = lv_indev_active();
  if (!input) return;
  const auto direction = lv_indev_get_gesture_dir(input);
  const uint8_t before = currentPage;
  swipe_cards(direction);
  if (currentPage == before) return;
  dashboard_update();   // draw the new page first, then let it glide in
  for (auto* cards : {big, compact})
    for (size_t i = 0; i < (cards == big ? kBigCards : kCompactCards); ++i)
      if (cards[i].card && !lv_obj_is_hidden(cards[i].card)) ui_interaction::slide_in(cards[i].card, ui_interaction::slide_from(direction));
}

static void open_card_cb(lv_event_t* event) {
  const auto* card = static_cast<CardWidgets*>(lv_event_get_user_data(event));
  if (!card || !card->providerKey[0] || ui_interaction::swiped()) return;
  // A configuration frame may arrive between the last draw and release.
  // Follow the identity the user saw, never a newly rebound numeric slot.
  const auto snapshot = aim::read();
  for (size_t i = 0; i < aim::kMaxViews; ++i) {
    if (snapshot.viewsConfigured && i >= snapshot.viewCount) break;
    const auto* key = snapshot.viewsConfigured ? snapshot.viewKeys[i] : snapshot.views[i].providerKey;
    if (strcmp(key, card->providerKey) == 0) { ui_details_show(static_cast<uint8_t>(i)); return; }
  }
}
void dashboard_init() {
  lv_obj_t* scr = lv_screen_active();
  ui_theme::watch(scr);
  dashboardScreen = scr;
  lv_obj_add_event_cb(scr, gesture_cb, LV_EVENT_GESTURE, nullptr);
  lv_obj_set_style_bg_color(scr, lv_color_hex(C_BG), 0);
  lv_obj_set_style_bg_opa(scr, LV_OPA_COVER, 0);
  lv_obj_set_style_border_width(scr, 0, 0);
  lv_obj_set_style_pad_all(scr, 0, 0);

  // ── header (78 px) ──
  lv_obj_t* header = lv_obj_create(scr);
  lv_obj_set_size(header, 800, 78);
  lv_obj_set_pos(header, 0, 0);
  lv_obj_set_style_bg_color(header, lv_color_hex(C_HEADER), 0);
  lv_obj_set_style_bg_opa(header, LV_OPA_COVER, 0);
  lv_obj_set_style_border_width(header, 0, 0);
  lv_obj_set_style_radius(header, 0, 0);
  lv_obj_set_style_pad_all(header, 0, 0);
  lv_obj_set_scrollable(header, false);
  make_line(header, 0, 77, 800, C_LINE);

#if defined(AIM_BOARD_WAVESHARE_S3)
  const char* boardCaption = "LIMITBUDDY / S3";
#else
  const char* boardCaption = "LIMITBUDDY / P4";
#endif
  hdr.eyebrow = make_label(header, 24, 13, 300, F_EYEBROW, C_EYEBROW, LV_TEXT_ALIGN_LEFT, boardCaption);
  lv_obj_set_style_text_letter_space(hdr.eyebrow, 2, 0);
  // Wide enough for "99% left / Z CODE Monthly", ending before the status dot at x 437; an
  // ellipsis, never a hard clip, shows when a long provider or window name does not fit.
  hdr.title = make_label(header, 24, 31, 405, F_PROVIDER, C_TITLE, LV_TEXT_ALIGN_LEFT, "Usage Dashboard");
  lv_label_set_long_mode(hdr.title, LV_LABEL_LONG_MODE_DOTS);
  lv_obj_set_height(hdr.title, lv_font_get_line_height(F_PROVIDER));
  // live dot + halo + label (SVG: dot center (475,30) r4, halo r8)
  // Room for the longest state (FETCHING / NO HOST) left of the right-aligned clock.
  hdr.halo = make_dot(header, 437, 22, 16, C_GREEN);
  lv_obj_set_style_bg_opa(hdr.halo, LV_OPA_20, 0);
  hdr.dot = make_dot(header, 441, 26, 8, C_GREEN);
  hdr.live = make_label(header, 458, 22, 112, F_META, C_META_BRIGHT, LV_TEXT_ALIGN_LEFT, "LIVE");
  lv_obj_set_style_text_letter_space(hdr.live, 1, 0);

  hdr.clock = make_label(header, 574, 26, 78, F_TIME, C_TITLE, LV_TEXT_ALIGN_RIGHT, "--:--");

  // SET button with gear icon (684,18,92,42)
  lv_obj_t* setBtn = lv_btn_create(header);
  lv_obj_set_size(setBtn, 120, 48);
  lv_obj_set_pos(setBtn, 656, 14);
  lv_obj_set_style_bg_color(setBtn, lv_color_hex(C_SET_BG), 0);
  lv_obj_set_style_bg_opa(setBtn, LV_OPA_COVER, 0);
  lv_obj_set_style_border_color(setBtn, lv_color_hex(C_SET_BORDER), 0);
  lv_obj_set_style_border_width(setBtn, 1, 0);
  lv_obj_set_style_radius(setBtn, 11, 0);
  lv_obj_set_style_shadow_width(setBtn, 0, 0);
  lv_obj_set_style_pad_all(setBtn, 0, 0);
  lv_obj_set_style_bg_color(setBtn, lv_color_hex(ui_theme::pressed), LV_STATE_PRESSED);
  lv_obj_add_event_cb(setBtn, settings_open_cb, LV_EVENT_CLICKED, nullptr);
  ui_interaction::keep_target(setBtn);

  auto* setLbl = make_label(setBtn, 0, 0, 96, &lv_font_montserrat_22, C_SET_TXT, LV_TEXT_ALIGN_CENTER, "MENU");
  lv_obj_center(setLbl);

  // ── cards ──
  for (size_t i = 0; i < kBigCards; ++i) big[i] = build_big_card(scr, (lv_coord_t)(20 + i * 388), 96);
  static const lv_coord_t kCompactX[kCompactCards] = {20, 408, 20, 408};
  static const lv_coord_t kCompactY[kCompactCards] = {96, 96, 258, 258};
  for (size_t i = 0; i < kCompactCards; ++i) compact[i] = build_compact_card(scr, kCompactX[i], kCompactY[i]);
  auto attach = [](CardWidgets& card) {
    lv_obj_set_clickable(card.card, true);
    lv_obj_add_event_cb(card.card, open_card_cb, LV_EVENT_CLICKED, &card);
    ui_interaction::keep_target(card.card);
    for (auto& row : card.rows) if (row.bar) lv_obj_set_clickable(row.bar, false);
  };
  for (auto& card : big) attach(card);
  for (auto& card : compact) attach(card);
  hintLabel = make_label(scr, 0, 230, 800, F_ROWLABEL, C_META, LV_TEXT_ALIGN_CENTER, "");

  // ── system bar footer (0,432,800,48) ──
  lv_obj_t* footer = lv_obj_create(scr);
  lv_obj_set_size(footer, 800, 48);
  lv_obj_set_pos(footer, 0, 432);
  lv_obj_set_style_bg_color(footer, lv_color_hex(C_FOOTER_BG), 0);
  lv_obj_set_style_bg_opa(footer, LV_OPA_COVER, 0);
  lv_obj_set_style_border_width(footer, 0, 0);
  lv_obj_set_style_radius(footer, 0, 0);
  lv_obj_set_style_pad_all(footer, 0, 0);
  lv_obj_set_scrollable(footer, false);
  make_line(footer, 0, 0, 800, C_LINE);
  footDot = make_dot(scr, 21, 420, 8, C_GREEN);
  // The strip above the navigation row is 18 px tall: 14 px is the largest font that fits it.
  footStrong = make_label(scr, 37, 415, 150, &lv_font_montserrat_14, C_FOOTER_STRONG, LV_TEXT_ALIGN_LEFT, "NO HOST");
  footFrames = nullptr;  // frame counts remain in the protocol, outside the daily-use footer
  // Data age and refresh hints matter most, so they sit in the empty middle of the navigation row
  // (between the three tabs, ending at x 376, and the page selector, starting at x 628) in 18 px.
  footSync = make_label(scr, 392, 445, 224, &lv_font_montserrat_18, C_META_BRIGHT, LV_TEXT_ALIGN_LEFT, "Updated -");
  footServices = make_label(scr, 552, 415, 224, &lv_font_montserrat_14, C_FOOTER, LV_TEXT_ALIGN_RIGHT, "0 / 0 services online");
  ui_navigation::create(scr,ui_navigation::Page::usage);
  pageButton = lv_btn_create(footer);
  lv_obj_set_pos(pageButton, 628, 0);
  lv_obj_set_size(pageButton, 148, 48);
  lv_obj_set_style_bg_color(pageButton, lv_color_hex(C_SET_BG), 0);
  lv_obj_set_style_radius(pageButton, 8, 0);
  lv_obj_set_style_shadow_width(pageButton, 0, 0);
  lv_obj_set_style_border_width(pageButton, 1, 0);
  lv_obj_set_style_border_color(pageButton, lv_color_hex(C_SET_BORDER), 0);
  lv_obj_set_style_bg_color(pageButton, lv_color_hex(ui_theme::pressed), LV_STATE_PRESSED);
  lv_obj_set_style_bg_color(pageButton, lv_color_hex(ui_theme::button), LV_STATE_DISABLED);
  lv_obj_set_style_opa(pageButton, LV_OPA_50, LV_STATE_DISABLED);
  lv_obj_set_style_recolor_opa(pageButton, LV_OPA_TRANSP, LV_STATE_DISABLED);
  lv_obj_add_event_cb(pageButton, next_page_cb, LV_EVENT_CLICKED, nullptr);
  ui_interaction::keep_target(pageButton);
  pageLabel = make_label(pageButton, 0, 0, 70, F_META, C_TITLE, LV_TEXT_ALIGN_CENTER, "1 / 2 >");
  lv_obj_center(pageLabel);
  lv_obj_set_hidden(pageLabel, true);
  pageArrow = make_label(pageButton, 118, 0, 22, F_META, C_TITLE, LV_TEXT_ALIGN_CENTER, ">");
  lv_obj_align(pageArrow, LV_ALIGN_RIGHT_MID, -10, 0);
  for (auto*& dot : pageDots) {
    dot = lv_obj_create(pageButton); lv_obj_set_size(dot, 6, 6);
    lv_obj_set_style_radius(dot, LV_RADIUS_CIRCLE, 0); lv_obj_set_style_border_width(dot, 0, 0);
    lv_obj_set_style_pad_all(dot, 0, 0); lv_obj_set_scrollable(dot, false); lv_obj_set_clickable(dot, false);
    lv_obj_set_hidden(dot, true);
  }
  dotsPage = dotsCount = UINT8_MAX;
  lv_obj_set_state(pageButton, LV_STATE_DISABLED, true);

  for (auto& cache : bigCache) cache = CardCaches{};
  for (auto& cache : compactCache) cache = CardCaches{};
  memset(g_barValue, 0, sizeof(g_barValue));
  memset(g_barColor, 0, sizeof(g_barColor));
  liveCache[0] = clockCache[0] = titleCache[0] = '\0';
  titleColorCache = 0;
  footStrongCache[0] = footFramesCache[0] = footSyncCache[0] = footServicesCache[0] = hintCache[0] = '\0';
  liveDotColor = footDotColor = 0;
}

void dashboard_update() {
  if (!dashboard_is_active()) return;  // settings screen visible
  // Do not move, hide or rebind an active touch target. Release activation
  // resolves the saved provider identity against the newest snapshot.
  for (const auto& card : big) if (lv_obj_has_state(card.card, LV_STATE_PRESSED)) return;
  for (const auto& card : compact) if (lv_obj_has_state(card.card, LV_STATE_PRESSED)) return;
  if (lv_obj_has_state(pageButton, LV_STATE_PRESSED)) return;
  const aim::Snapshot snap = aim::read();
  const uint32_t now = millis();
  // Same session inputs as the NOVA screen, so both report one status per provider.
  const auto agentEvents = agent::read();
  const auto liveAgents = live_agent::read_usb();
  const bool recent = snap.frameCount != 0 && (now - snap.lastFrameMs < STALE_MS);
  size_t onlineCount = 0, activeCount = 0, fetchingCount = 0;
  for (size_t i = 0; i < aim::kMaxViews; ++i) {
    if (snap.viewsConfigured && i >= snap.viewCount) continue;
    const auto& view = snap.views[i];
    if (!view.valid && !(snap.viewsConfigured && snap.viewKeys[i][0])) continue;
    ++activeCount;
    if (view.valid && view.fetching && !view.notice) ++fetchingCount;
    const auto* provider = aim::provider_style(view.providerKey);
    // Quota and local activity are independent capabilities. A fresh signal
    // from some other selected AI must not mark a missing bridge healthy.
    const bool local = view.valid && view.informational && provider &&
        ((token_signal_fresh(snap, now) && (snap.tokenSourceMask & provider->activityMask)) ||
         session_status(snap, now, provider->activityMask, agentEvents, liveAgents).known);
    if (snap.hostPresent && (local || (view.valid && !view.notice && !view.fetching && view.rowCount &&
        now - view.quotaReceivedMs < STALE_MS))) ++onlineCount;
  }

  // ── header: dot + LIVE/STALE/NO HOST + clock ──
  char liveBuf[12];
  uint32_t dotColor = C_GREEN;
  if (!snap.hostPresent) {
    snprintf(liveBuf, sizeof(liveBuf), "NO HOST");
    dotColor = C_AMBER;
  } else if (snap.frameCount == 0) {
    snprintf(liveBuf, sizeof(liveBuf), "WAITING");
    dotColor = C_AMBER;
  } else if (recent) {
    const bool fetching = activeCount > 0 && fetchingCount == activeCount;
    const bool issue = activeCount > 0 && onlineCount == 0 && !fetching;
    const bool partial = onlineCount < activeCount;
    snprintf(liveBuf, sizeof(liveBuf), "%s", fetching ? "FETCHING" : (issue ? "ISSUE" : (partial ? "PARTIAL" : "LIVE")));
    dotColor = issue ? C_RED : (partial ? C_AMBER : C_GREEN);
  } else {
    snprintf(liveBuf, sizeof(liveBuf), "STALE");
    dotColor = C_RED;
  }
  set_label_cached(hdr.live, liveCache, sizeof(liveCache), liveBuf);
  if (liveDotColor != dotColor) {
    liveDotColor = dotColor;
    lv_obj_set_style_bg_color(hdr.dot, lv_color_hex(dotColor), 0);
    lv_obj_set_style_bg_color(hdr.halo, lv_color_hex(dotColor), 0);
  }
  char clockBuf[8] = "--:--";
  uint16_t clockMinutes = 0;
  // Same freshness policy as every other clock consumer: stop extrapolating
  // from a host sync older than 12 h instead of presenting a derived clock.
  if (local_minutes(snap, now, clockMinutes)) {
    snprintf(clockBuf, sizeof(clockBuf), "%02u:%02u", clockMinutes / 60u, clockMinutes % 60u);
  }
  set_label_cached(hdr.clock, clockCache, sizeof(clockCache), clockBuf);

  // The title names the most urgent window over all AIs, also those on another card page.
  char titleBuf[64] = "Usage Dashboard";
  uint32_t titleColor = C_TITLE;
  const QuotaHeadline headline = quota_headline(snap, now);
  if (headline.valid && recent) {
    char percent[16];
    format_percent(headline.remaining, true, percent, sizeof(percent));
    snprintf(titleBuf, sizeof(titleBuf), "%s left / %s %s", percent, headline.provider, headline.window);
    titleColor = headline.level == 2 ? C_RED : (headline.level == 1 ? C_AMBER : C_TITLE);
  }
  set_label_cached(hdr.title, titleCache, sizeof(titleCache), titleBuf);
  if (titleColorCache != titleColor) {
    titleColorCache = titleColor;
    lv_obj_set_style_text_color(hdr.title, lv_color_hex(titleColor), 0);
  }

  // ── collect entries ──
  struct Entry {
    uint8_t index;
    const aim::ViewData* view;
    const char* key;
  };
  Entry entries[aim::kMaxViews];
  size_t used = 0;
  for (size_t v = 0; v < aim::kMaxViews; ++v) {
    if (snap.viewsConfigured && v >= snap.viewCount) continue;
    const bool configured = snap.viewsConfigured && v < snap.viewCount && snap.viewKeys[v][0] != '\0';
    if (!snap.views[v].valid && !configured) continue;
    entries[used].view = &snap.views[v];
    entries[used].index = static_cast<uint8_t>(v);
    entries[used].key = snap.viewKeys[v];
    used++;
  }
  // Drop AIs the user hid, unless that would leave the page empty.
  size_t shown = 0;
  for (size_t k = 0; k < used; ++k)
    if (!app_settings::provider_hidden(entries[k].key[0] ? entries[k].key : entries[k].view->providerKey)) entries[shown++] = entries[k];
  if (shown) used = shown;
  const size_t perPage = app_settings::card_layout().perPage;

  pageCount = static_cast<uint8_t>(std::max<size_t>(1, (used + perPage - 1) / perPage));
  if (viewRevision != snap.viewRevision) {
    viewRevision = snap.viewRevision;
    // activeView is a raw slot; skipped slots shift the compacted entries.
    size_t position = 0;
    for (size_t k = 0; k < used; ++k) if (entries[k].index == snap.activeView) { position = k; break; }
    currentPage = static_cast<uint8_t>((position / perPage) % pageCount);
    lastPageMs = now;
  }
  currentPage %= pageCount;
  const uint32_t period = static_cast<uint32_t>(snap.viewIntervalSeconds) * 1000u;
  if (pageCount > 1 && snap.automaticViews && period && now - lastPageMs >= period) {
    currentPage = (currentPage + (now - lastPageMs) / period) % pageCount;
    lastPageMs = now;
  }
  lv_obj_set_state(pageButton, LV_STATE_DISABLED, pageCount < 2);
  lv_obj_set_hidden(pageButton, pageCount < 2);
  {
    char text[16];
    snprintf(text, sizeof(text), "%u / %u >", currentPage + 1u, pageCount);
    if (strcmp(lv_label_get_text(pageLabel), text) != 0) lv_label_set_text(pageLabel, text);
  }
  if (dotsPage != currentPage || dotsCount != pageCount) {
    // Page dots: the current page is a wider accent pill, the same language as the home screen.
    dotsPage = currentPage; dotsCount = pageCount;
    int x = 4;
    for (size_t d = 0; d < aim::kMaxViews; ++d) {
      const bool shown = d < pageCount, active = d == currentPage;
      lv_obj_set_hidden(pageDots[d], !shown);
      if (!shown) continue;
      lv_obj_set_width(pageDots[d], active ? 18 : 6);
      lv_obj_align(pageDots[d], LV_ALIGN_LEFT_MID, x, 0);
      lv_obj_set_style_bg_color(pageDots[d], lv_color_hex(active ? ui_theme::accent : ui_theme::muted), 0);
      x += (active ? 18 : 6) + 6;
    }
  }
  const size_t start = currentPage * perPage;
  const size_t onPage = std::min(perPage, used - std::min(start, used));
  const bool useCompact = perPage == kCompactCards;
  // One card per page sits centred; two use the left and right columns.
  const lv_coord_t firstX = perPage == 1 ? 214 : 20;
  if (lv_obj_get_style_x(big[0].card, LV_PART_MAIN) != firstX) lv_obj_set_x(big[0].card, firstX);
  for (size_t i = 0; i < kBigCards + kCompactCards; ++i) {
    const bool isCompact = i >= kBigCards;
    const size_t slot = isCompact ? i - kBigCards : i;
    auto& card = isCompact ? compact[slot] : big[slot];
    const bool show = isCompact == useCompact && slot < onPage;
    lv_obj_set_hidden(card.card, !show);
    if (!show) continue;
    const auto& entry = entries[start + slot];
    card.viewIndex = entry.index;
    snprintf(card.providerKey, sizeof(card.providerKey), "%s", entry.key[0] ? entry.key : entry.view->providerKey);
    render_card(card, isCompact ? compactCache[slot] : bigCache[slot], entry.view, entry.key, i, now, snap.hostPresent,
                session_status(snap, now, entry.key, agentEvents, liveAgents));
  }

  char hintBuf[96];
  if (used > 0 || snap.viewsConfigured) hintBuf[0] = '\0';
  else if (!snap.hostPresent) snprintf(hintBuf, sizeof(hintBuf), "Waiting for the LimitBuddy host on USB ...");
  else snprintf(hintBuf, sizeof(hintBuf), "Connected - waiting for the first usage frame ...");
  set_label_cached(hintLabel, hintCache, sizeof(hintCache), hintBuf);

  // ── system bar footer ──
  char strongBuf[20];
  uint32_t fdot = C_GREEN;
  if (!snap.hostPresent) {
    snprintf(strongBuf, sizeof(strongBuf), "NO HOST");
    fdot = C_AMBER;
  } else {
    snprintf(strongBuf, sizeof(strongBuf), "HOST CONNECTED");
  }
  set_label_cached(footStrong, footStrongCache, sizeof(footStrongCache), strongBuf);
  if (footDotColor != fdot) {
    footDotColor = fdot;
    lv_obj_set_style_bg_color(footDot, lv_color_hex(fdot), 0);
  }
  char framesBuf[24];
  snprintf(framesBuf, sizeof(framesBuf), "%lu frames", (unsigned long)snap.frameCount);
  set_label_cached(footFrames, footFramesCache, sizeof(footFramesCache), framesBuf);
  char syncBuf[24];
  const uint32_t age = snap.frameCount ? (now - snap.lastFrameMs) / 1000u : 0;
  const char* refreshHint = refresh_hint(snap, now);
  if (refreshHint[0]) snprintf(syncBuf, sizeof(syncBuf), "%s", refreshHint);
  else if (!snap.frameCount) snprintf(syncBuf, sizeof(syncBuf), "Updated -");
  else if (age < 60) snprintf(syncBuf, sizeof(syncBuf), "Updated %lu s ago", (unsigned long)age);
  else if (age < 3600) snprintf(syncBuf, sizeof(syncBuf), "Updated %lu m ago", (unsigned long)(age / 60));
  else snprintf(syncBuf, sizeof(syncBuf), "Updated %lu h ago", (unsigned long)(age / 3600));
  set_label_cached(footSync, footSyncCache, sizeof(footSyncCache), syncBuf);
  char servicesBuf[24];
  snprintf(servicesBuf, sizeof(servicesBuf), "%lu / %lu services online", (unsigned long)onlineCount, (unsigned long)used);
  set_label_cached(footServices, footServicesCache, sizeof(footServicesCache), servicesBuf);

}

void dashboard_show() {if(dashboardScreen){lv_screen_load(dashboardScreen);dashboard_update();}}
