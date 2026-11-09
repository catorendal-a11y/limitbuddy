// Card construction and rendering for the dashboard.
// Private to dashboard.cpp: included once, after its widget types and caches.

// ───────────────────────────────────────────────────────────────────────────────
// SMALL BUILDERS
// ───────────────────────────────────────────────────────────────────────────────
static lv_obj_t* make_label(lv_obj_t* parent, lv_coord_t x, lv_coord_t y, lv_coord_t w, const lv_font_t* font,
                            uint32_t color, lv_text_align_t align, const char* text) {
  lv_obj_t* lbl = lv_label_create(parent);
  lv_label_set_text(lbl, text);
  lv_obj_set_pos(lbl, x, y);
  lv_obj_set_width(lbl, w);
  lv_label_set_long_mode(lbl, LV_LABEL_LONG_MODE_CLIP);
  lv_obj_set_style_text_font(lbl, font, 0);
  lv_obj_set_style_text_color(lbl, lv_color_hex(color), 0);
  lv_obj_set_style_text_align(lbl, align, 0);
  return lbl;
}

static lv_obj_t* make_line(lv_obj_t* parent, lv_coord_t x, lv_coord_t y, lv_coord_t w, uint32_t color) {
  lv_obj_t* ln = lv_obj_create(parent);
  lv_obj_set_size(ln, w, 1);
  lv_obj_set_pos(ln, x, y);
  lv_obj_set_style_bg_color(ln, lv_color_hex(color), 0);
  lv_obj_set_style_bg_opa(ln, LV_OPA_COVER, 0);
  lv_obj_set_style_border_width(ln, 0, 0);
  lv_obj_set_style_radius(ln, 0, 0);
  lv_obj_set_style_pad_all(ln, 0, 0);
  lv_obj_set_scrollable(ln, false);
  lv_obj_set_clickable(ln, false);
  return ln;
}

static lv_obj_t* make_dot(lv_obj_t* parent, lv_coord_t x, lv_coord_t y, lv_coord_t d, uint32_t color) {
  lv_obj_t* dot = lv_obj_create(parent);
  lv_obj_set_size(dot, d, d);
  lv_obj_set_pos(dot, x, y);
  lv_obj_set_style_radius(dot, LV_RADIUS_CIRCLE, 0);
  lv_obj_set_style_bg_color(dot, lv_color_hex(color), 0);
  lv_obj_set_style_bg_opa(dot, LV_OPA_COVER, 0);
  lv_obj_set_style_border_width(dot, 0, 0);
  lv_obj_set_style_pad_all(dot, 0, 0);
  lv_obj_set_scrollable(dot, false);
  lv_obj_set_clickable(dot, false);
  return dot;
}

static void window_label(uint32_t windowMinutes, char* out, size_t cap) {
  if (windowMinutes == 300) snprintf(out, cap, "5H WINDOW");
  else if (windowMinutes == 10080) snprintf(out, cap, "7 DAY WINDOW");
  else if (windowMinutes == 43200) snprintf(out, cap, "MONTHLY WINDOW");
  else if (windowMinutes == 0) snprintf(out, cap, "WINDOW");
  else if (windowMinutes % 1440 == 0) snprintf(out, cap, "%lu DAY%s", (unsigned long)(windowMinutes / 1440), windowMinutes == 1440 ? "" : "S");
  else snprintf(out, cap, "%lu MIN", (unsigned long)windowMinutes);
}

// Status suffixes share the row's 220 px caption; a short period keeps the status word whole.
static void window_short(uint32_t windowMinutes, char* out, size_t cap) {
  if (windowMinutes == 0) snprintf(out, cap, "QUOTA");
  else if (windowMinutes % 1440 == 0) snprintf(out, cap, "%luD", (unsigned long)(windowMinutes / 1440));
  else if (windowMinutes % 60 == 0) snprintf(out, cap, "%luH", (unsigned long)(windowMinutes / 60));
  else snprintf(out, cap, "%luM", (unsigned long)windowMinutes);
}

static void age_short(uint32_t ageMs, char* out, size_t cap, bool upper = true) {
  const unsigned long minutes = ageMs / 60000u;
  if (minutes < 60) snprintf(out, cap, upper ? "%luM" : "%lu min", minutes);
  else if (minutes < 1440) snprintf(out, cap, upper ? "%luH" : "%lu h", minutes / 60);
  else snprintf(out, cap, upper ? "%luD" : "%lu d", minutes / 1440);
}

// ───────────────────────────────────────────────────────────────────────────────
// CARD BUILD (v2 geometry from the SVG)
// ───────────────────────────────────────────────────────────────────────────────
static void build_row(CardWidgets& c, size_t r, lv_coord_t yTop, bool withDivider) {
  RowWidgets& w = c.rows[r];
  if (withDivider) w.divider = make_line(c.card, 18, yTop - 17, 338, C_LINE_SOFT);
  w.winMeta = make_label(c.card, 18, yTop, 220, &lv_font_montserrat_18, C_META, LV_TEXT_ALIGN_LEFT, "");
  lv_obj_set_style_text_letter_space(w.winMeta, 1, 0);
  w.name = make_label(c.card, 18, yTop + 20, 240, F_ROWLABEL, C_ROWLABEL, LV_TEXT_ALIGN_LEFT, "");
  w.pct = make_label(c.card, 236, yTop + 5, 110, F_PCT, C_PCT, LV_TEXT_ALIGN_RIGHT, "--");
  w.unit = make_label(c.card, 236, yTop + 41, 110, F_META, C_UNIT, LV_TEXT_ALIGN_RIGHT, "");
  lv_obj_set_style_text_letter_space(w.unit, 1, 0);
  w.bar = lv_bar_create(c.card);
  lv_obj_set_size(w.bar, 327, 12);
  lv_obj_set_pos(w.bar, 18, yTop + 62);
  lv_bar_set_range(w.bar, 0, 100);
  lv_obj_set_style_bg_color(w.bar, lv_color_hex(C_BAR_TRACK), LV_PART_MAIN);
  lv_obj_set_style_bg_opa(w.bar, LV_OPA_COVER, LV_PART_MAIN);
  lv_obj_set_style_border_width(w.bar, 0, LV_PART_MAIN);
  lv_obj_set_style_radius(w.bar, 6, LV_PART_MAIN);
  lv_obj_set_style_pad_all(w.bar, 0, LV_PART_MAIN);
  lv_obj_set_style_bg_color(w.bar, lv_color_hex(C_GREEN), LV_PART_INDICATOR);
  lv_obj_set_style_bg_opa(w.bar, LV_OPA_COVER, LV_PART_INDICATOR);
  lv_obj_set_style_radius(w.bar, 6, LV_PART_INDICATOR);
  // Quartile ticks are a scale, not thresholds (those are configurable per provider).
  for (int quarter = 1; quarter <= 3; ++quarter) {
    lv_obj_t* tick = make_line(w.bar, 327 * quarter / 4, 2, 2, C_CARD);
    lv_obj_set_height(tick, 8);
    lv_obj_set_style_bg_opa(tick, LV_OPA_60, 0);
  }
  w.knob = make_dot(w.bar, 314, 2, 8, C_GREEN);  // child of the bar; x set per value
  w.pace = make_line(c.card, 18, yTop + 58, 2, C_PCT);
  lv_obj_set_height(w.pace, 20);
  lv_obj_set_style_radius(w.pace, 1, 0);
  lv_obj_set_hidden(w.pace, true);
  w.reset = make_label(c.card, 18, yTop + 82, 330, &lv_font_montserrat_18, C_RESET, LV_TEXT_ALIGN_LEFT, "");
  // One line with an ellipsis: a retained provider error must never end mid-word.
  lv_obj_set_height(w.reset, lv_font_get_line_height(&lv_font_montserrat_18));
  lv_label_set_long_mode(w.reset, LV_LABEL_LONG_MODE_DOTS);
}

static CardWidgets build_big_card(lv_obj_t* parent, lv_coord_t x, lv_coord_t y) {
  CardWidgets c;
  c.card = lv_obj_create(parent);
  lv_obj_set_size(c.card, 372, 318);
  lv_obj_set_pos(c.card, x, y);
  lv_obj_set_style_bg_color(c.card, lv_color_hex(C_CARD), 0);
  lv_obj_set_style_bg_opa(c.card, LV_OPA_COVER, 0);
  lv_obj_set_style_border_color(c.card, lv_color_hex(C_LINE), 0);
  lv_obj_set_style_border_width(c.card, 1, 0);
  lv_obj_set_style_radius(c.card, 18, 0);
  lv_obj_set_style_shadow_width(c.card, 0, 0);
  lv_obj_set_style_pad_all(c.card, 0, 0);
  lv_obj_set_scrollable(c.card, false);
  lv_obj_set_clickable(c.card, false);
  lv_obj_set_hidden(c.card, true);

  c.spine = make_dot(c.card, 0, 0, 4, C_GREEN);
  lv_obj_set_size(c.spine, 4, 318);
  lv_obj_set_style_radius(c.spine, 2, 0);

  // provider badge (18,18,42,42) rx11
  c.badge = lv_obj_create(c.card);
  lv_obj_set_size(c.badge, 42, 42);
  lv_obj_set_pos(c.badge, 18, 18);
  lv_obj_set_style_radius(c.badge, 11, 0);
  lv_obj_set_style_border_width(c.badge, 1, 0);
  lv_obj_set_style_pad_all(c.badge, 0, 0);
  lv_obj_set_scrollable(c.badge, false);
  lv_obj_set_clickable(c.badge, false);
  c.badgeLetter = make_label(c.badge, 0, 0, 42, F_BADGE, 0xFFFFFF, LV_TEXT_ALIGN_CENTER, "C");
  lv_obj_center(c.badgeLetter);
  c.badgeLogo = lv_image_create(c.badge); lv_obj_set_clickable(c.badgeLogo, false);

  c.name = make_label(c.card, 74, 20, 220, F_PROVIDER, C_NAME, LV_TEXT_ALIGN_LEFT, "-");
  c.vendor = make_label(c.card, 74, 49, 240, F_META, C_META, LV_TEXT_ALIGN_LEFT, "");
  lv_label_set_long_mode(c.vendor, LV_LABEL_LONG_MODE_SCROLL_CIRCULAR);
  lv_obj_set_style_text_letter_space(c.vendor, 1, 0);
  c.remaining = make_label(c.card, 240, 21, 106, F_META, C_META, LV_TEXT_ALIGN_RIGHT, "REMAINING");
  lv_obj_set_style_text_letter_space(c.remaining, 1, 0);
  make_line(c.card, 18, 77, 356, C_LINE);

  build_row(c, 0, 94, false);
  build_row(c, 1, 210, true);
  build_row(c, 2, 238, false);
  return c;
}

// Quarter-height card for the 2 x 2 layout: name, one line per window, no captions or markers.
static CardWidgets build_compact_card(lv_obj_t* parent, lv_coord_t x, lv_coord_t y) {
  CardWidgets c;
  c.compact = true;
  c.card = lv_obj_create(parent);
  lv_obj_set_size(c.card, 372, 150);
  lv_obj_set_pos(c.card, x, y);
  lv_obj_set_style_bg_color(c.card, lv_color_hex(C_CARD), 0);
  lv_obj_set_style_bg_opa(c.card, LV_OPA_COVER, 0);
  lv_obj_set_style_border_color(c.card, lv_color_hex(C_LINE), 0);
  lv_obj_set_style_border_width(c.card, 1, 0);
  lv_obj_set_style_radius(c.card, 18, 0);
  lv_obj_set_style_shadow_width(c.card, 0, 0);
  lv_obj_set_style_pad_all(c.card, 0, 0);
  lv_obj_set_scrollable(c.card, false);
  lv_obj_set_hidden(c.card, true);
  c.spine = make_dot(c.card, 0, 0, 4, C_GREEN);
  lv_obj_set_size(c.spine, 4, 150);
  lv_obj_set_style_radius(c.spine, 2, 0);
  c.badge = lv_obj_create(c.card);
  lv_obj_set_pos(c.badge, 14, 10);
  lv_obj_set_size(c.badge, 28, 28);
  lv_obj_set_style_radius(c.badge, 8, 0);
  lv_obj_set_style_pad_all(c.badge, 0, 0);
  lv_obj_set_style_border_width(c.badge, 1, 0);
  lv_obj_set_scrollable(c.badge, false);
  lv_obj_set_clickable(c.badge, false);
  c.badgeLogo = lv_image_create(c.badge);
  lv_obj_set_pos(c.badgeLogo, 1, 1);
  lv_obj_set_clickable(c.badgeLogo, false);
  c.badgeLetter = make_label(c.badge, 0, 0, 26, F_META, C_NAME, LV_TEXT_ALIGN_CENTER, "-");
  lv_obj_center(c.badgeLetter);
  c.name = make_label(c.card, 50, 10, 190, F_PROVIDER, C_NAME, LV_TEXT_ALIGN_LEFT, "-");
  c.vendor = make_label(c.card, 16, 42, 340, &lv_font_montserrat_14, C_META, LV_TEXT_ALIGN_LEFT, "");
  lv_label_set_long_mode(c.vendor, LV_LABEL_LONG_MODE_DOTS);
  lv_obj_set_style_text_letter_space(c.vendor, 1, 0);
  c.remaining = make_label(c.card, 240, 14, 106, F_META, C_META, LV_TEXT_ALIGN_RIGHT, "REMAINING");
  lv_obj_set_style_text_letter_space(c.remaining, 1, 0);
  for (size_t r = 0; r < aim::kMaxRows; ++r) {
    RowWidgets& w = c.rows[r];
    const lv_coord_t ry = static_cast<lv_coord_t>(64 + r * 30);
    w.name = make_label(c.card, 16, ry, 96, F_META, C_ROWLABEL, LV_TEXT_ALIGN_LEFT, "");
    w.pct = make_label(c.card, 260, ry - 1, 86, &lv_font_montserrat_16, C_PCT, LV_TEXT_ALIGN_RIGHT, "--");
    w.bar = lv_bar_create(c.card);
    lv_obj_set_size(w.bar, 330, 5);
    lv_obj_set_pos(w.bar, 16, ry + 20);
    lv_bar_set_range(w.bar, 0, 100);
    lv_obj_set_style_bg_color(w.bar, lv_color_hex(C_BAR_TRACK), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(w.bar, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_width(w.bar, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(w.bar, 4, LV_PART_MAIN);
    lv_obj_set_style_pad_all(w.bar, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(w.bar, 4, LV_PART_INDICATOR);
    lv_obj_set_style_bg_opa(w.bar, LV_OPA_COVER, LV_PART_INDICATOR);
    w.reset = make_label(c.card, 116, ry, 136, F_META, C_RESET, LV_TEXT_ALIGN_RIGHT, "");
  }
  return c;
}

// ───────────────────────────────────────────────────────────────────────────────
// RENDER ONE CARD
// ───────────────────────────────────────────────────────────────────────────────
static void visible(lv_obj_t* object, bool show) {
  if (!object) return;
  lv_obj_set_hidden(object, !show);
}

static void layout_rows(CardWidgets& card, const aim::ViewData* view) {
  const uint8_t count = view && view->valid && view->rowCount ? view->rowCount : 1;
  const bool notice = view && view->notice && !view->hasUsage;
  if (card.layoutRows == count && card.layoutNotice == notice) return;
  card.layoutRows = count;
  card.layoutNotice = notice;
  for (size_t r = 0; r < aim::kMaxRows; ++r) {
    auto& row = card.rows[r];
    const bool show = r < count;
    for (auto* object : {row.winMeta, row.name, row.pct, row.unit, row.bar, row.knob, row.reset}) visible(object, show);
    visible(row.divider, show && count <= 2);
    if (!show) continue;
    const int top = card.compact ? (count == 3 ? 58 + static_cast<int>(r) * 30 : 64 + static_cast<int>(r) * 38) :
                    (count == 3 ? 94 + static_cast<int>(r) * 72 : 94 + static_cast<int>(r) * 116);
    if (card.compact) {
      lv_obj_set_pos(row.name, 16, top);
      lv_obj_set_pos(row.pct, 260, top - 1);
      lv_obj_set_pos(row.bar, 16, top + 20);
      lv_obj_set_pos(row.reset, 116, top);
    } else {
      // Three rows share 72 px each: the row title already names the window, so
      // drop the caption line and keep a visible gap between reset text and the next row.
      const bool dense = count == 3;
      lv_obj_set_pos(row.winMeta, 18, top);
      visible(row.winMeta, !dense);
      lv_obj_set_pos(row.name, 18, top + (dense ? 2 : 20));
      lv_obj_set_pos(row.pct, 236, top);
      lv_obj_set_style_text_font(row.pct, dense ? &lv_font_montserrat_26 : &lv_font_montserrat_40, 0);
      lv_obj_set_pos(row.unit, 236, top + 45);
      visible(row.unit, !dense);
      lv_obj_set_pos(row.bar, 18, top + (dense ? 32 : 62));
      lv_obj_set_height(row.bar, dense ? 8 : 10);
      lv_obj_set_pos(row.reset, 18, top + (dense ? 44 : 82));
      if (row.divider) lv_obj_set_y(row.divider, top - 17);
    }
    lv_obj_set_width(row.name, notice ? 330 : (card.compact ? 96 : 210));
    lv_obj_set_style_text_font(row.name, notice ? &lv_font_montserrat_14 : (card.compact ? F_META : F_ROWLABEL), 0);
    lv_label_set_long_mode(row.name, notice ? LV_LABEL_LONG_MODE_WRAP : LV_LABEL_LONG_MODE_CLIP);
    if (notice) {
      for (auto* object : {row.pct, row.unit, row.bar, row.knob, row.reset}) visible(object, false);
    }
  }
}

static void render_card(CardWidgets& c, CardCaches& cache, const aim::ViewData* view, const char* key, size_t slot,
                        uint32_t now, bool hostConnected, const SessionStatus& sessions) {
  layout_rows(c, view);
  const V2Style* vs = v2_style(view && view->valid ? view->providerKey : key);
  const char* keyStr = view && view->valid ? view->providerKey : key;
  const uint32_t base = style_base(vs);
  const uint32_t light = style_light(vs);
  const char* vendor = style_vendor(vs, view && view->valid ? view->providerLabel : keyStr);

  // spine + badge colors
  if (c.spine && (!cache.spineKnown || cache.spine != base)) {
    lv_obj_set_style_bg_color(c.spine, lv_color_hex(base), 0);
    cache.spine = base;
    cache.spineKnown = true;
  }
  if (!cache.styleKnown || cache.style != vs) {
    cache.style = vs;
    cache.styleKnown = true;
    if (c.badge) {
      lv_obj_set_style_bg_color(c.badge, lv_color_hex(style_badge_fill(vs)), 0);
      lv_obj_set_style_border_color(c.badge, lv_color_hex(style_badge_stroke(vs)), 0);
    }
    if (c.badgeLetter) lv_obj_set_style_text_color(c.badgeLetter, lv_color_hex(style_badge_letter(vs)), 0);
  }
  char letter[2] = "?";
  if (keyStr && keyStr[0]) {
    letter[0] = (char)((keyStr[0] >= 'a' && keyStr[0] <= 'z') ? keyStr[0] - 32 : keyStr[0]);
  }
  set_label_cached(c.badgeLetter, cache.badgeLetter, sizeof(cache.badgeLetter), letter);
  const auto* logo = nova_assets::logo_for(keyStr, c.compact ? 24 : 42);
  if (logo && lv_image_get_src(c.badgeLogo) != logo) lv_image_set_src(c.badgeLogo, logo);
  lv_obj_set_hidden(c.badgeLogo, !logo);
  lv_obj_set_hidden(c.badgeLetter, logo != nullptr);

  // name + vendor meta
  char nameBuf[16];
  if (view && view->valid) snprintf(nameBuf, sizeof(nameBuf), "%s", view->providerLabel);
  else {
    const aim::ProviderStyle* ps = aim::provider_style(key);
    snprintf(nameBuf, sizeof(nameBuf), "%s", ps ? ps->label : (key ? key : "-"));
  }
  set_label_cached(c.name, cache.name, sizeof(cache.name), nameBuf);

  const bool fresh = view && view->hasUsage && now - view->quotaReceivedMs < STALE_MS;
  bool critical = false, low = false;
  if (fresh && hostConnected && view && !view->notice && !view->fetching) {
    for (size_t r = 0; r < view->rowCount; ++r) {
      const auto& row = view->rows[r];
      if (!row.valid) continue;
      const float remaining = view->showsRemaining ? row.usedPercent : 100.0f - row.usedPercent;
      critical |= quota_critical(remaining, view->providerKey, row);
      low |= quota_low(remaining, view->providerKey, row);
    }
  }
  const quota_state::State quota = quota_state::classify(view, hostConnected, fresh, critical, low);
  // A card that needs attention says so with its own edge, not only with a number's color.
  const uint8_t glow = critical ? 2 : low ? 1 : 0;
  if (cache.glow != glow || cache.glowTheme != ui_theme::revision) {
    const uint32_t edge = glow == 2 ? C_RED : C_AMBER;
    lv_obj_set_style_border_color(c.card, lv_color_hex(glow ? edge : C_LINE), 0);
    lv_obj_set_style_border_width(c.card, glow ? 2 : 1, 0);
    lv_obj_set_style_shadow_width(c.card, glow ? 24 : 0, 0);
    lv_obj_set_style_shadow_color(c.card, lv_color_hex(edge), 0);
    lv_obj_set_style_shadow_opa(c.card, LV_OPA_30, 0);
    cache.glow = glow;
    cache.glowTheme = ui_theme::revision;
  }
  char vendorBuf[sizeof(cache.vendor)];
  snprintf(vendorBuf, sizeof(vendorBuf), "%s - %s", vendor, quota_state::label(quota, false));
  if (hostConnected && sessions.known && (sessions.waiting || sessions.running || sessions.error || sessions.completed)) {
    // Keep quota health visible alongside an independent observed session.
    snprintf(vendorBuf, sizeof(vendorBuf), "%s / %s", quota_state::label(quota, true),
             sessions.waiting ? "NEEDS YOU" : sessions.error ? "SESSION ERROR" : sessions.running ? "RUNNING" : "TURN DONE");
  }
  set_label_cached(c.vendor, cache.vendor, sizeof(cache.vendor), vendorBuf);

  char remBuf[12];
  const bool hasQuota = view && view->hasUsage && view->rowCount > 0;
  snprintf(remBuf, sizeof(remBuf), "%s", view && view->informational ? "LOCAL" :
           hasQuota ? (view->showsRemaining ? "REMAINING" : "USED") : "");
  set_label_cached(c.remaining, cache.remaining, sizeof(cache.remaining), remBuf);

  for (size_t r = 0; r < aim::kMaxRows; ++r) {
    RowWidgets& w = c.rows[r];
    RowCaches& rc = cache.rows[r];
    if (!w.bar) continue;  // row not present in this layout

    char winBuf[36];
    char nameBuf2[48];
    char pctBuf[8];
    char unitBuf[12];
    char resetBuf[48];
    float paceProgress = -1.0f;
    if (view && view->notice && !view->hasUsage && r == 0) {
      snprintf(winBuf, sizeof(winBuf), "NOTICE");
      snprintf(nameBuf2, sizeof(nameBuf2), "%.47s", view->message);
      snprintf(pctBuf, sizeof(pctBuf), "--");
      unitBuf[0] = '\0';
      resetBuf[0] = '\0';
      set_bar_cached(w.bar, slot, r, 0.0f, base);
      if (w.knob) set_knob(w.knob, rc, 0.0f, light);
    } else if (!view || !view->valid || r >= view->rowCount || !view->rows[r].valid) {
      snprintf(winBuf, sizeof(winBuf), "WINDOW");
      snprintf(nameBuf2, sizeof(nameBuf2), "waiting ...");
      snprintf(pctBuf, sizeof(pctBuf), "--");
      unitBuf[0] = '\0';
      resetBuf[0] = '\0';
      set_bar_cached(w.bar, slot, r, 0.0f, base);
      if (w.knob) set_knob(w.knob, rc, 0.0f, light);
    } else {
      const aim::Row& row = view->rows[r];
      window_label(row.windowMinutes, winBuf, sizeof(winBuf));
      snprintf(nameBuf2, sizeof(nameBuf2), "%s", row.title[0] ? row.title : "-");
      format_percent(row.usedPercent, view->showsRemaining, pctBuf, sizeof(pctBuf));
      if (!c.compact) {
        const bool widePercent = strlen(pctBuf) >= 5;
        const int width = widePercent ? 142 : 110, x = widePercent ? 204 : 236;
        if (lv_obj_get_width(w.pct) != width) lv_obj_set_width(w.pct, width);
        if (lv_obj_get_x(w.pct) != x) lv_obj_set_x(w.pct, x);
        const auto* font = c.layoutRows == 3 ? &lv_font_montserrat_26 : (strlen(pctBuf) >= 6 ? &lv_font_montserrat_30 : &lv_font_montserrat_40);
        if (lv_obj_get_style_text_font(w.pct, LV_PART_MAIN) != font) lv_obj_set_style_text_font(w.pct, font, 0);
        const int nameWidth = widePercent ? 174 : 210;
        if (lv_obj_get_width(w.name) != nameWidth) lv_obj_set_width(w.name, nameWidth);
      }
      snprintf(unitBuf, sizeof(unitBuf), "%s", view->showsRemaining ? "LEFT" : "USED");
      if (row.resetsShort[0]) snprintf(resetBuf, sizeof(resetBuf), c.compact ? "%s" : "Resets %s", row.resetsShort);
      else resetBuf[0] = '\0';
      if (row.hasResetCountdown) {
        char countdown[32];
        format_countdown(reset_remaining(row, view->quotaReceivedMs, now), countdown, sizeof(countdown));
        snprintf(resetBuf, sizeof(resetBuf), c.compact ? "%s" : "%.24s / %.19s", countdown, row.resetsShort);
      }
      const float remaining = view->showsRemaining ? row.usedPercent : 100.0f - row.usedPercent;
      const uint32_t quotaColor = !fresh || !hostConnected || view->notice || view->fetching ? C_META :
                                  (quota_critical(remaining, view->providerKey, row) ? C_RED : (quota_low(remaining, view->providerKey, row) ? C_AMBER : base));
      if (fresh && hostConnected && !view->notice && !view->fetching && quota_low(remaining, view->providerKey, row) && !c.compact) {
        char period[16];
        window_short(row.windowMinutes, period, sizeof(period));
        snprintf(winBuf, sizeof(winBuf), "%s / %s", period, quota_critical(remaining, view->providerKey, row) ? "CRITICAL" : "LOW");
      }
      if (view->notice && view->hasUsage) {
        const unsigned long ageMinutes = (now - view->quotaReceivedMs) / 60000u;
        char age[12];
        age_short(now - view->quotaReceivedMs, age, sizeof(age));
        // State the age once per card; later rows keep their window names.
        if (r == 0) snprintf(winBuf, sizeof(winBuf), "LAST GOOD / %s", age);
        if (c.compact) snprintf(resetBuf, sizeof(resetBuf), "Old / %lu m", ageMinutes);
        // Three rows hide the caption line and leave no room for a message (the card
        // header still says ERROR - TAP), so the age moves to the first reset line.
        else if (r == 0 && c.layoutRows <= 2) snprintf(resetBuf, sizeof(resetBuf), "%.47s", view->message);
        else if (r == 0) {
          age_short(now - view->quotaReceivedMs, age, sizeof(age), false);
          snprintf(resetBuf, sizeof(resetBuf), "Last good %s ago", age);
        }
      }
      const uint32_t percentColor = quotaColor == base ? C_PCT : quotaColor;
      if (rc.percentColor != percentColor) {
        rc.percentColor = percentColor;
        lv_obj_set_style_text_color(w.pct, lv_color_hex(percentColor), 0);
      }
      if (fresh && hostConnected && !view->notice && !view->fetching && row.hasResetCountdown)
        paceProgress = window_progress(row.windowMinutes, reset_remaining(row, view->quotaReceivedMs, now));
      set_bar_cached(w.bar, slot, r, row.usedPercent, quotaColor);
      if (w.knob) set_knob(w.knob, rc, row.usedPercent, quotaColor == base ? light : quotaColor);
    }
    set_label_cached(w.winMeta, rc.winMeta, sizeof(rc.winMeta), winBuf);
    set_label_cached(w.name, rc.name, sizeof(rc.name), nameBuf2);
    set_label_cached(w.pct, rc.pct, sizeof(rc.pct), pctBuf);
    if (w.unit) set_label_cached(w.unit, rc.unit, sizeof(rc.unit), unitBuf);
    set_label_cached(w.reset, rc.reset, sizeof(rc.reset), resetBuf);
    set_pace(w.pace, w.bar, paceProgress, view && view->showsRemaining);
  }
}
