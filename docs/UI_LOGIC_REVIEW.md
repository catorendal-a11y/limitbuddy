# UI logic review (rc10 and rc11)

Dated review records. The Qt desktop app they mention was retired in rc15 for the terminal ([TERMINAL.md](TERMINAL.md)); those rows are history. Firmware UI rules still apply: [device navigation](DEVICE_NAVIGATION.md). Coverage and test counts are rc10 figures.

## rc11 device navigation follow-up

Feedback exposed a defect the rc10 review missed: selected providers appeared among real sessions on Agents. rc11:

- removed those rows; shows a short session ID; distinguishes "no observed sessions" from "no live feed";
- gave Home, Usage and Agents shared fixed primary destinations at the bottom (current one outlined); Usage keeps two full-size cards; MENU stays fixed and secondary screens return to the caller.

Native regressions: direct navigation, identical button geometry on all three screens, empty/disconnected feeds, quota-provider independence, multiple session identities, paging, expiry, rollover, session/event timing. Synthetic screens do not establish physical touch validation; passing rc10 tests did not establish usability.

## rc10 review

Scope: desktop action/state flows and firmware UI, by source review, synthetic Qt/LVGL runs and separately recorded device checks. Not every hardware interaction or provider model.

| Surface | Result in rc10 |
| --- | --- |
| Setup and selection | Explicit selection; stale or mismatched status never confirms a connection |
| Desktop actions | Main-thread UI updates, one action worker; failure does not complete a pending close |
| Provider setup | Uninstall removes only exactly-owned hooks, keeps unrelated settings/metadata; alternate Claude root handled |
| Provider health | Separate quota vs activity and last-check vs last-success timestamps; saving credentials never implies working quota |
| Diagnostic export | Whitelist, protected atomic write; excludes keys, raw errors, account IDs, arguments, conversations |
| Desktop history | Local calendar boundaries shared by chart/table/CSV; UTC observations unchanged; unknown gaps kept |
| History clearing | Confirm, revoke before transactional delete, no database unlink, no old results during clear |
| Companion library | Activation needs matching fresh device status; packages stay data-only |
| Device mirror | Read-only pixels via existing serial owner; protected screens excluded |
| Home / Usage / Agents | Quota errors stay visible; token-only activity never claims agent work; expired metadata says Last and is muted |
| Menu, details, history | Touch geometry kept; return navigation, drag cancel, dropdown identity; unknowns stay unknown |
| Settings, notifications | Draft/cancel/save feedback; fail-closed persistence |
| Permission / enrollment | Production approval stays disabled; synthetic tests are not physical validation |
| Upgrade / uninstall | New helper stops old host; uncertain cleanup blocks uninstall; private data kept |

Coverage: changed Python modules 89% combined executable lines; the nine main firmware UI modules 97-100% (connection UI 89%); main modules hit 54-74% of branch outcomes (gcov, including compiler-generated paths); the permission wrapper has its own native target. Coverage measures exercised code, not absence of defects.

Still separate gates: real hold/release/enrollment, physical unplug/suspend, S3 panel/touch, clean Windows profile install, genuine publisher signing, full eight-hour endurance. Full-suite and package/device/endurance results are in the local rc10 delivery.

## Visual follow-up

75 native 800x480 states and 19 Qt views/dialogs (real Segoe fonts, minimum desktop size) were reviewed across provider paging, precision, remaining/used labels, offline values, long errors, session vs token activity, history gaps, warning/critical overlays, notification pages, brightness, night minutes, themes, enrollment comparison and blocked/held permissions.

| Defect | Fix |
| --- | --- |
| History actions exceeded minimum desktop width | Two rows; real-font geometry asserts no horizontal overflow |
| SAVED / SAVE FAILED covered by alert and night overlays | Feedback in front of every settings overlay, outside action buttons; stacking, position and visibility tested; failure frame inspected |

Snapshot data and comparison codes were synthetic. Physical capture verifies only the current P4 frame, not untested touch flows. No virtual approval/touch path was added.
