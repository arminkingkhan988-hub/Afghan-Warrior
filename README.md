# Android Export & Build Guide — AFGHAN WARRIOR

## Prerequisites
1. Godot Engine 4.3+ (Standard GDScript version)
2. Android Export Templates installed in Godot (`Editor -> Manage Export Templates`)
3. OpenJDK 17 (`JAVA_HOME` configured)
4. Android SDK Platform 34 + Build-Tools 34.0.0 + `adb`

## Exporting the APK
1. Open `AfghanWarrior/project.godot` in Godot 4.3+.
2. Go to **Project -> Export...** and select the preconfigured **Android** preset (`export_presets.cfg`).
3. Ensure **Architectures** has `arm64-v8a` (and `armeabi-v7a` if supporting older 32-bit phones).
4. Notice `permissions/internet=false` — the game runs 100% offline.
5. Click **Export Project...** and save as `AfghanWarrior.apk`.

## Real-Device Testing Checklist
- Install via `adb install -r AfghanWarrior.apk`.
- Verify automatic landscape orientation lock during gameplay.
- Test multi-touch: hold left virtual joystick while dragging right-side camera area and tapping Fire / Aim.
- Test Graphics Presets (LOW / MEDIUM / HIGH) on low-end (2–3 GB RAM) and mid/high-end Android phones.
- Confirm Pashto RTL layout rendering and English LTR switching persist across app restarts.
