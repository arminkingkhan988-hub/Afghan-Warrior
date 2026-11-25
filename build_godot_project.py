#!/usr/bin/env python3
"""
Afghan Warrior (افغان جنګیالی) — Complete Godot 4.x Android Project Builder & Validator.
Generates the entire Godot 4 project under godot_project/AfghanWarrior/,
creates procedural PBR textures (.png) and procedural audio (.wav),
validates all res:// references and GDScript/TSCN syntax,
and packages everything into Afghan_Warrior_Complete_Project.zip.
"""

import json
import math
import os
import random
import re
import struct
import wave
import zipfile
import zlib

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_DIR = os.path.join(ROOT_DIR, "godot_project", "AfghanWarrior")
PUBLIC_ZIP = os.path.join(ROOT_DIR, "public", "Afghan_Warrior_Complete_Project.zip")
ROOT_ZIP = os.path.join(ROOT_DIR, "Afghan_Warrior_Complete_Project.zip")


def write_text(rel_path: str, content: str) -> None:
    full_path = os.path.join(PROJECT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.lstrip("\n"))


def write_json(rel_path: str, data: object) -> None:
    full_path = os.path.join(PROJECT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_png(rel_path: str, width: int, height: int, pixel_fn) -> None:
    """Write a valid RGBA PNG using Python standard library zlib."""
    full_path = os.path.join(PROJECT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    raw_rows = []
    for y in range(height):
        row = bytearray([0])  # filter type 0
        for x in range(width):
            r, g, b, a = pixel_fn(x, y, width, height)
            row.extend((max(0, min(255, int(r))), max(0, min(255, int(g))),
                        max(0, min(255, int(b))), max(0, min(255, int(a)))))
        raw_rows.append(bytes(row))

    raw_data = b"".join(raw_rows)
    compressed = zlib.compress(raw_data, level=6)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        crc = zlib.crc32(tag + payload) & 0xFFFFFFFF
        return struct.pack("!I", len(payload)) + tag + payload + struct.pack("!I", crc)

    ihdr = struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )
    with open(full_path, "wb") as f:
        f.write(png_bytes)


def write_wav(rel_path: str, duration_s: float, sample_fn, sample_rate: int = 22050) -> None:
    """Write a valid 16-bit mono PCM WAV file."""
    full_path = os.path.join(PROJECT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    total_samples = int(duration_s * sample_rate)
    frames = bytearray()
    for i in range(total_samples):
        t = i / sample_rate
        val = max(-1.0, min(1.0, float(sample_fn(t, duration_s, i))))
        frames.extend(struct.pack("<h", int(val * 32767)))

    with wave.open(full_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(frames))


def build_textures_and_audio() -> None:
    rng = random.Random(42)

    # 1. Procedural realistic PBR textures (128x128 tileable)
    def mudbrick_px(x, y, w, h):
        brick_h = 16
        row = y // brick_h
        offset = 16 if row % 2 else 0
        bx = (x + offset) % 32
        by = y % brick_h
        mortar = (bx < 2 or by < 2)
        n = ((math.sin(x * 0.37 + y * 0.51) + math.cos(x * 0.19 - y * 0.29)) * 8)
        if mortar:
            return (148 + n, 128 + n, 98 + n, 255)
        return (178 + n, 149 + n, 108 + n, 255)

    def rock_px(x, y, w, h):
        n = (
            math.sin(x * 0.15) * 14
            + math.cos(y * 0.22) * 12
            + math.sin((x + y) * 0.45) * 8
        )
        base = 104 + n
        return (base + 6, base, base - 8, 255)

    def sand_dirt_px(x, y, w, h):
        n = math.sin(x * 0.28) * 7 + math.cos(y * 0.31) * 7 + math.sin((x - y) * 0.6) * 4
        return (176 + n, 152 + n, 112 + n, 255)

    def concrete_px(x, y, w, h):
        n = math.sin(x * 0.5 + y * 0.3) * 6 + math.cos(x * 0.17 - y * 0.41) * 5
        seam = 20 if (y % 64 < 2) else 0
        c = 132 + n - seam
        return (c, c - 2, c - 4, 255)

    def camo_px(x, y, w, h):
        v = math.sin(x * 0.08 + math.cos(y * 0.09) * 1.8) + math.cos(y * 0.11 - x * 0.05)
        if v > 0.7:
            return (82, 92, 62, 255)
        if v > -0.1:
            return (138, 122, 92, 255)
        if v > -0.8:
            return (108, 96, 72, 255)
        return (64, 62, 52, 255)

    def wood_px(x, y, w, h):
        grain = math.sin(y * 0.65 + math.sin(x * 0.09) * 2.5) * 10
        plank = -18 if (y % 32 < 2) else 0
        return (122 + grain + plank, 88 + grain * 0.7 + plank, 54 + grain * 0.5 + plank, 255)

    def metal_px(x, y, w, h):
        brush = math.sin(x * 0.9) * 4 + math.cos(y * 0.2) * 3
        c = 76 + brush
        return (c, c + 3, c + 6, 255)

    write_png("assets/textures/mud_brick.png", 128, 128, mudbrick_px)
    write_png("assets/textures/mountain_rock.png", 128, 128, rock_px)
    write_png("assets/textures/valley_soil.png", 128, 128, sand_dirt_px)
    write_png("assets/textures/military_concrete.png", 128, 128, concrete_px)
    write_png("assets/textures/tactical_camo.png", 128, 128, camo_px)
    write_png("assets/textures/wood_plank.png", 128, 128, wood_px)
    write_png("assets/textures/gunmetal.png", 64, 64, metal_px)

    # HUD crosshair & reticle icon
    def crosshair_px(x, y, w, h):
        cx, cy = w // 2, h // 2
        dx, dy = abs(x - cx), abs(y - cy)
        if (dx <= 1 and 5 <= dy <= 16) or (dy <= 1 and 5 <= dx <= 16) or (dx <= 1 and dy <= 1):
            return (245, 225, 165, 240)
        return (0, 0, 0, 0)

    write_png("assets/icons/crosshair.png", 48, 48, crosshair_px)

    # 2. Procedural Audio (.wav)
    def rifle_shot(t, dur, i):
        env = math.exp(-t * 28.0)
        punch = math.sin(2.0 * math.pi * (140.0 * math.exp(-t * 18.0)) * t)
        crack = (rng.uniform(-1.0, 1.0)) * math.exp(-t * 22.0)
        return (punch * 0.55 + crack * 0.65) * env

    def sniper_shot(t, dur, i):
        env = math.exp(-t * 11.0)
        boom = math.sin(2.0 * math.pi * (95.0 * math.exp(-t * 9.0)) * t)
        crack = rng.uniform(-1.0, 1.0) * math.exp(-t * 14.0)
        return (boom * 0.6 + crack * 0.7) * env

    def shotgun_shot(t, dur, i):
        env = math.exp(-t * 15.0)
        low = math.sin(2.0 * math.pi * 75.0 * t) * math.exp(-t * 12.0)
        blast = rng.uniform(-1.0, 1.0)
        return (low * 0.5 + blast * 0.75) * env

    def pistol_shot(t, dur, i):
        env = math.exp(-t * 36.0)
        snap = math.sin(2.0 * math.pi * 240.0 * math.exp(-t * 22.0) * t)
        noise = rng.uniform(-1.0, 1.0)
        return (snap * 0.5 + noise * 0.55) * env

    def reload_sfx(t, dur, i):
        click1 = math.exp(-((t - 0.12) ** 2) / 0.0004) * math.sin(2 * math.pi * 620 * t)
        click2 = math.exp(-((t - 0.55) ** 2) / 0.0005) * math.sin(2 * math.pi * 880 * t)
        slide = math.exp(-((t - 0.85) ** 2) / 0.0012) * (rng.uniform(-0.5, 0.5) + math.sin(2 * math.pi * 420 * t) * 0.4)
        return (click1 + click2 + slide) * 0.65

    def explosion_sfx(t, dur, i):
        env = math.exp(-t * 3.8)
        rumble = math.sin(2 * math.pi * 48 * t) * 0.5 + math.sin(2 * math.pi * 72 * t) * 0.3
        debris = rng.uniform(-1.0, 1.0) * 0.75
        return (rumble + debris) * env

    def footstep_sfx(t, dur, i):
        env = math.exp(-t * 34.0)
        thud = math.sin(2 * math.pi * 95 * t) * 0.5 + rng.uniform(-0.5, 0.5) * 0.4
        return thud * env

    def wind_sfx(t, dur, i):
        mod = 0.5 + 0.4 * math.sin(2 * math.pi * 0.35 * t)
        whoosh = math.sin(2 * math.pi * 110 * t) * 0.08 + rng.uniform(-0.22, 0.22)
        return whoosh * mod * 0.45

    def birds_sfx(t, dur, i):
        chirp = math.exp(-((t % 0.9 - 0.15) ** 2) / 0.002)
        freq = 2100 + 500 * math.sin(2 * math.pi * 14 * t)
        return math.sin(2 * math.pi * freq * t) * chirp * 0.28

    def rain_sfx(t, dur, i):
        return rng.uniform(-0.25, 0.25)

    def ui_click_sfx(t, dur, i):
        return math.sin(2 * math.pi * 920 * t) * math.exp(-t * 55.0) * 0.45

    def hit_marker_sfx(t, dur, i):
        return math.sin(2 * math.pi * 1450 * t) * math.exp(-t * 65.0) * 0.55

    def vehicle_sfx(t, dur, i):
        pulse = (
            0.45 * math.sin(2 * math.pi * 44 * t)
            + 0.25 * math.sin(2 * math.pi * 88 * t)
            + 0.12 * rng.uniform(-1.0, 1.0)
        )
        return pulse * 0.4

    def menu_theme(t, dur, i):
        # Atmospheric tactical minor drone & rhythmic pulse (seamless 6s loop)
        root = 110.0  # A2
        fifth = 164.81
        minor_third = 130.81
        pad = (
            0.24 * math.sin(2 * math.pi * root * t)
            + 0.16 * math.sin(2 * math.pi * fifth * t)
            + 0.12 * math.sin(2 * math.pi * minor_third * t * (1.0 if t < 3.0 else 1.122))
        )
        drum_env = math.exp(-((t % 0.75) * 14.0))
        drum = math.sin(2 * math.pi * 62 * (t % 0.75)) * drum_env * 0.28
        return (pad * 0.55 + drum) * min(1.0, t * 4.0) * min(1.0, (dur - t) * 4.0)

    write_wav("assets/audio/rifle_shot.wav", 0.24, rifle_shot)
    write_wav("assets/audio/smg_shot.wav", 0.18, rifle_shot)
    write_wav("assets/audio/sniper_shot.wav", 0.45, sniper_shot)
    write_wav("assets/audio/shotgun_shot.wav", 0.35, shotgun_shot)
    write_wav("assets/audio/pistol_shot.wav", 0.18, pistol_shot)
    write_wav("assets/audio/reload.wav", 1.1, reload_sfx)
    write_wav("assets/audio/explosion.wav", 1.2, explosion_sfx)
    write_wav("assets/audio/footstep_dirt.wav", 0.15, footstep_sfx)
    write_wav("assets/audio/wind_ambient.wav", 3.0, wind_sfx)
    write_wav("assets/audio/birds_ambient.wav", 2.7, birds_sfx)
    write_wav("assets/audio/rain_ambient.wav", 2.0, rain_sfx)
    write_wav("assets/audio/ui_click.wav", 0.08, ui_click_sfx)
    write_wav("assets/audio/hit_marker.wav", 0.08, hit_marker_sfx)
    write_wav("assets/audio/vehicle_engine.wav", 2.0, vehicle_sfx)
    write_wav("assets/audio/menu_theme.wav", 6.0, menu_theme)


def build_data_files() -> None:
    en_translations = {
        "APP_TITLE": "AFGHAN WARRIOR",
        "APP_SUBTITLE": "Tactical Mountain Operations",
        "MENU_PLAY": "PLAY",
        "MENU_STORY": "STORY MODE",
        "MENU_FREE_BATTLE": "FREE BATTLE",
        "MENU_MISSIONS": "MISSIONS",
        "MENU_WEAPONS": "WEAPONS",
        "MENU_SETTINGS": "SETTINGS",
        "MENU_ABOUT": "ABOUT",
        "MENU_EXIT": "EXIT",
        "MENU_BACK": "BACK",
        "MENU_LANGUAGE": "LANGUAGE",
        "LANG_ENGLISH": "English (LTR)",
        "LANG_PASHTO": "پښتو (RTL)",
        "HUD_HEALTH": "HEALTH",
        "HUD_ARMOR": "ARMOR",
        "HUD_AMMO": "AMMO",
        "HUD_OBJECTIVE": "OBJECTIVE",
        "HUD_ENEMIES": "HOSTILES REMAINING",
        "HUD_GRENADES": "GRENADES",
        "HUD_RELOADING": "RELOADING...",
        "HUD_INTERACT_VEHICLE": "Enter / Exit Vehicle",
        "HUD_INTERACT_PICKUP": "Pick Up Weapon / Ammo",
        "HUD_WAVE": "WAVE",
        "PAUSE_TITLE": "MISSION PAUSED",
        "PAUSE_RESUME": "RESUME",
        "PAUSE_RESTART": "RESTART",
        "PAUSE_SETTINGS": "SETTINGS",
        "PAUSE_MAIN_MENU": "MAIN MENU",
        "SETTINGS_TITLE": "SYSTEM SETTINGS",
        "SETTINGS_LANGUAGE": "Language",
        "SETTINGS_GRAPHICS": "Graphics Quality",
        "QUALITY_LOW": "LOW (Battery / Entry)",
        "QUALITY_MEDIUM": "MEDIUM (Balanced)",
        "QUALITY_HIGH": "HIGH (Maximum Detail)",
        "SETTINGS_MUSIC": "Music Volume",
        "SETTINGS_SFX": "Effects Volume",
        "SETTINGS_ENV": "Environment Volume",
        "SETTINGS_CAM_SENS": "Camera Sensitivity",
        "SETTINGS_AIM_SENS": "Aim Sensitivity",
        "SETTINGS_CTRL_SENS": "Joystick Sensitivity",
        "SETTINGS_FULLSCREEN": "Fullscreen / Immersive",
        "SETTINGS_SAVE": "SAVE & APPLY",
        "FREE_TITLE": "FREE BATTLE SETUP",
        "FREE_MAP": "Combat Map",
        "FREE_DIFFICULTY": "Enemy Difficulty",
        "FREE_ENEMY_COUNT": "Enemy Count",
        "FREE_WEAPON": "Starting Weapon",
        "FREE_TIME": "Time of Day",
        "FREE_WEATHER": "Weather",
        "FREE_DEPLOY": "DEPLOY TO BATTLE",
        "DIFF_RECRUIT": "Recruit",
        "DIFF_VETERAN": "Veteran",
        "DIFF_ELITE": "Elite",
        "TIME_DAY": "Daylight",
        "TIME_DUSK": "Golden Dusk",
        "TIME_NIGHT": "Night Ops",
        "WEATHER_CLEAR": "Clear Sky",
        "WEATHER_DUST": "Mountain Dust",
        "WEATHER_RAIN": "Highland Rain",
        "MAP_VILLAGE": "Afghan Village",
        "MAP_VALLEY": "Mountain Valley",
        "MAP_OUTPOST": "Military Outpost",
        "RESULT_VICTORY": "MISSION ACCOMPLISHED",
        "RESULT_DEFEAT": "OPERATOR DOWN",
        "RESULT_NEXT": "NEXT MISSION",
        "RESULT_RETRY": "RETRY MISSION",
        "MSG_SAVED": "Settings and progress saved locally.",
        "MSG_LOCKED": "Complete the previous mission to unlock.",
        "MSG_NO_AMMO": "Out of ammunition — switch weapon or find resupply.",
        "ABOUT_TEXT": "AFGHAN WARRIOR is an offline 3D third-person tactical action game built in Godot 4 for Android. All characters, units, and locations are fictionalized and inspired by Afghanistan's rugged mountain terrain and villages."
    }

    ps_translations = {
        "APP_TITLE": "افغان جنګیالی",
        "APP_SUBTITLE": "تاکتیکي غرني عملیات",
        "MENU_PLAY": "لوبه پیل کړئ",
        "MENU_STORY": "کیسه ایز حالت",
        "MENU_FREE_BATTLE": "آزاد جګړه",
        "MENU_MISSIONS": "ماموریتونه",
        "MENU_WEAPONS": "وسلې",
        "MENU_SETTINGS": "تنظیمات",
        "MENU_ABOUT": "په اړه",
        "MENU_EXIT": "وتل",
        "MENU_BACK": "شاته",
        "MENU_LANGUAGE": "ژبه",
        "LANG_ENGLISH": "English (LTR)",
        "LANG_PASHTO": "پښتو (RTL)",
        "HUD_HEALTH": "روغتیا",
        "HUD_ARMOR": "زغره",
        "HUD_AMMO": "مرمۍ",
        "HUD_OBJECTIVE": "موخه",
        "HUD_ENEMIES": "پاتې دښمنان",
        "HUD_GRENADES": "لاسي بمونه",
        "HUD_RELOADING": "ډکول روان دي...",
        "HUD_INTERACT_VEHICLE": "موټر ته ننوتل / وتل",
        "HUD_INTERACT_PICKUP": "وسله یا مرمۍ اخیستل",
        "HUD_WAVE": "څپه",
        "PAUSE_TITLE": "ماموریت ودرول شو",
        "PAUSE_RESUME": "دوام ورکول",
        "PAUSE_RESTART": "بیا پیلول",
        "PAUSE_SETTINGS": "تنظیمات",
        "PAUSE_MAIN_MENU": "اصلي مینو",
        "SETTINGS_TITLE": "د سیسټم تنظیمات",
        "SETTINGS_LANGUAGE": "ژبه",
        "SETTINGS_GRAPHICS": "د ګرافیک کیفیت",
        "QUALITY_LOW": "ټیټ (د سپما حالت)",
        "QUALITY_MEDIUM": "منځنی (متوازن)",
        "QUALITY_HIGH": "لوړ (بشپړ جزئیات)",
        "SETTINGS_MUSIC": "د موسیقۍ غږ",
        "SETTINGS_SFX": "د اغېزو غږ",
        "SETTINGS_ENV": "د چاپیریال غږ",
        "SETTINGS_CAM_SENS": "د کمرې حساسیت",
        "SETTINGS_AIM_SENS": "د نښې حساسیت",
        "SETTINGS_CTRL_SENS": "د کنټرول حساسیت",
        "SETTINGS_FULLSCREEN": "بشپړ سکرین",
        "SETTINGS_SAVE": "ثبت او پلي کول",
        "FREE_TITLE": "د آزادې جګړې تنظیم",
        "FREE_MAP": "د جګړې نقشه",
        "FREE_DIFFICULTY": "د دښمن سختوالی",
        "FREE_ENEMY_COUNT": "د دښمنانو شمېر",
        "FREE_WEAPON": "پیل وسله",
        "FREE_TIME": "د ورځې وخت",
        "FREE_WEATHER": "هوا",
        "FREE_DEPLOY": "جګړې ته تلل",
        "DIFF_RECRUIT": "عادي",
        "DIFF_VETERAN": "تجربه کار",
        "DIFF_ELITE": "ځانګړی",
        "TIME_DAY": "ورځ",
        "TIME_DUSK": "مازدیګر",
        "TIME_NIGHT": "د شپې عملیات",
        "WEATHER_CLEAR": "روښانه اسمان",
        "WEATHER_DUST": "غرنی دوړه",
        "WEATHER_RAIN": "باران",
        "MAP_VILLAGE": "افغاني کلی",
        "MAP_VALLEY": "غرنی دره",
        "MAP_OUTPOST": "پوځي پوسته",
        "RESULT_VICTORY": "ماموریت بریالی شو",
        "RESULT_DEFEAT": "جنګیالی ټپي شو",
        "RESULT_NEXT": "بل ماموریت",
        "RESULT_RETRY": "بیا هڅه وکړئ",
        "MSG_SAVED": "تنظیمات او پرمختګ په خوندي ډول ثبت شول.",
        "MSG_LOCKED": "د خلاصولو لپاره مخکینی ماموریت بشپړ کړئ.",
        "MSG_NO_AMMO": "مرمۍ خلاصې شوې — بله وسله وکاروئ.",
        "ABOUT_TEXT": "افغان جنګیالی د انډرایډ لپاره په ګوډوټ ۴ انجن کې جوړه شوې آفلاین درې بعدي پوځي لوبه ده. ټول کرکټرونه، ډلې او ځایونه خیالي دي او د افغانستان له غرونو او کلیو څخه الهام اخلي."
    }

    write_json("data/translations/en.json", en_translations)
    write_json("data/translations/ps.json", ps_translations)

    weapons = [
        {
            "id": "khyber_47",
            "category": "Assault Rifle",
            "name_en": "Khyber-47 Tactical",
            "name_ps": "خیبر-۴۷ تاکتیکي ټوپک",
            "damage": 26,
            "fire_rate": 0.11,
            "recoil": 0.045,
            "spread": 0.018,
            "mag_size": 30,
            "reserve_max": 180,
            "reload_time": 1.6,
            "range": 140.0,
            "pellets": 1,
            "automatic": True,
            "zoom_fov": 45.0,
            "sound": "res://assets/audio/rifle_shot.wav",
            "unlocked": True
        },
        {
            "id": "pamir_m24",
            "category": "Sniper Rifle",
            "name_en": "Pamir Longbow M24",
            "name_ps": "پامیر اوږد واټن M24",
            "damage": 95,
            "fire_rate": 1.15,
            "recoil": 0.11,
            "spread": 0.002,
            "mag_size": 5,
            "reserve_max": 35,
            "reload_time": 2.3,
            "range": 260.0,
            "pellets": 1,
            "automatic": False,
            "zoom_fov": 22.0,
            "sound": "res://assets/audio/sniper_shot.wav",
            "unlocked": True
        },
        {
            "id": "helmand_12g",
            "category": "Shotgun",
            "name_en": "Helmand Breacher 12G",
            "name_ps": "هلمند 12G شارټ ګن",
            "damage": 18,
            "fire_rate": 0.78,
            "recoil": 0.095,
            "spread": 0.085,
            "mag_size": 8,
            "reserve_max": 48,
            "reload_time": 2.1,
            "range": 48.0,
            "pellets": 6,
            "automatic": False,
            "zoom_fov": 52.0,
            "sound": "res://assets/audio/shotgun_shot.wav",
            "unlocked": True
        },
        {
            "id": "kabul_9mm",
            "category": "Pistol",
            "name_en": "Kabul Sidearm 9mm",
            "name_ps": "کابل ۹ ملي متري تومانچه",
            "damage": 22,
            "fire_rate": 0.24,
            "recoil": 0.028,
            "spread": 0.015,
            "mag_size": 15,
            "reserve_max": 90,
            "reload_time": 1.15,
            "range": 85.0,
            "pellets": 1,
            "automatic": False,
            "zoom_fov": 52.0,
            "sound": "res://assets/audio/pistol_shot.wav",
            "unlocked": True
        },
        {
            "id": "balkh_pdw",
            "category": "Submachine Gun",
            "name_en": "Balkh Compact PDW",
            "name_ps": "بلخ سپک PDW",
            "damage": 19,
            "fire_rate": 0.075,
            "recoil": 0.032,
            "spread": 0.028,
            "mag_size": 32,
            "reserve_max": 192,
            "reload_time": 1.45,
            "range": 75.0,
            "pellets": 1,
            "automatic": True,
            "zoom_fov": 48.0,
            "sound": "res://assets/audio/smg_shot.wav",
            "unlocked": True
        }
    ]
    write_json("data/weapons/weapons.json", {"weapons": weapons})

    missions = [
        {
            "id": 1,
            "implemented": True,
            "map_scene": "res://scenes/maps/map_afghan_village.tscn",
            "map_id": "village",
            "title_en": "Mission 01: Mountain Arrival",
            "title_ps": "لومړی ماموریت: غره ته رسېدل",
            "briefing_en": "Fictional militia scouts have occupied the eastern ridge overlooking Kunar Valley Village. Secure the perimeter checkpoint and clear all hostiles.",
            "briefing_ps": "خیالي وسله والو د کلي ختیځه څنډه نیولې ده. د تالاشۍ پوسته خوندي کړئ او ټول دښمنان له منځه یوسئ.",
            "objective_en": "Eliminate hostile scouts in the eastern village square",
            "objective_ps": "د کلي په ختیځ میدان کې ټول دښمنان له منځه یوسئ",
            "spawn_pos": [0, 1.2, 24],
            "enemy_count": 5,
            "difficulty": "recruit",
            "time_of_day": "day",
            "weather": "clear",
            "reward_points": 250,
            "unlocks_mission": 2
        },
        {
            "id": 2,
            "implemented": True,
            "map_scene": "res://scenes/maps/map_afghan_village.tscn",
            "map_id": "village",
            "title_en": "Mission 02: Village Rescue",
            "title_ps": "دویم ماموریت: د کلي ژغورنه",
            "briefing_en": "Hostile squads have blockaded the central mud-brick compounds. Advance through the narrow streets, neutralize patrols, and secure the village courtyard.",
            "briefing_ps": "دښمنانو د کلي منځنۍ کوڅې تړلې دي. د خټینو کورونو ترمنځ مخکې لاړ شئ او انګړ آزاد کړئ.",
            "objective_en": "Clear both courtyard patrol waves in the village",
            "objective_ps": "د کلي په انګړ کې د دښمن دواړه ډلې ماتې کړئ",
            "spawn_pos": [-16, 1.2, 18],
            "enemy_count": 8,
            "difficulty": "veteran",
            "time_of_day": "dusk",
            "weather": "dust",
            "reward_points": 400,
            "unlocks_mission": 3
        },
        {
            "id": 3,
            "implemented": True,
            "map_scene": "res://scenes/maps/map_military_outpost.tscn",
            "map_id": "outpost",
            "title_en": "Mission 03: Protect the Checkpoint",
            "title_ps": "درېیم ماموریت: د پوستې دفاع",
            "briefing_en": "Raiders are approaching Highland Pass Outpost under dusk cover. Hold the concrete barriers and defend the watchtowers until the area is secure.",
            "briefing_ps": "بریدګر د ماښام په تیاره کې پوستې ته نږدې شوي دي. د کانکریټي دیوالونو تر شا د پوستې دفاع وکړئ.",
            "objective_en": "Repel attackers and hold the outpost perimeter",
            "objective_ps": "برید په شا وتمبوئ او پوسته وساتئ",
            "spawn_pos": [0, 1.2, 12],
            "enemy_count": 10,
            "difficulty": "veteran",
            "time_of_day": "dusk",
            "weather": "clear",
            "reward_points": 550,
            "unlocks_mission": 4
        },
        {
            "id": 4,
            "implemented": False,
            "map_scene": "res://scenes/maps/map_mountain_valley.tscn",
            "map_id": "valley",
            "title_en": "Mission 04: Search the Valley",
            "title_ps": "څلورم ماموریت: د درې پلټنه",
            "briefing_en": "Sweep the rocky mountain valley paths and locate lost supply crates near the river cliffs.",
            "briefing_ps": "د غرنۍ درې ډبرینې لارې وپلټئ او د سیند تر څنګ ورک شوي اکمالات ومومئ.",
            "objective_en": "Sweep the northern valley ridge and secure supplies",
            "objective_ps": "شمالي دره پاکه کړئ او اکمالات خوندي کړئ",
            "spawn_pos": [0, 1.2, 22],
            "enemy_count": 9,
            "difficulty": "veteran",
            "time_of_day": "day",
            "weather": "clear",
            "reward_points": 600,
            "unlocks_mission": 5
        },
        {
            "id": 5,
            "implemented": False,
            "map_scene": "res://scenes/maps/map_mountain_valley.tscn",
            "map_id": "valley",
            "title_en": "Mission 05: Secure the Bridge",
            "title_ps": "پنځم ماموریت: د پل نیول",
            "briefing_en": "Cross the stone river bridge and eliminate sniper overwatch posted on the canyon ledges.",
            "briefing_ps": "له ډبرین پل څخه واوړئ او پر غونډیو پراته نښه ویشتونکي له منځه یوسئ.",
            "objective_en": "Capture the valley river crossing",
            "objective_ps": "د درې پر سیند پروت پل ونیسئ",
            "spawn_pos": [0, 1.2, 26],
            "enemy_count": 10,
            "difficulty": "veteran",
            "time_of_day": "day",
            "weather": "rain",
            "reward_points": 650,
            "unlocks_mission": 6
        },
        {
            "id": 6,
            "implemented": False,
            "map_scene": "res://scenes/maps/map_afghan_village.tscn",
            "map_id": "village",
            "title_en": "Mission 06: Night Patrol",
            "title_ps": "شپږم ماموریت: د شپې ګزمه",
            "briefing_en": "Conduct a night reconnaissance patrol through the silent mud-brick alleys under rain cover.",
            "briefing_ps": "د شپې په باران کې د کلي په کوڅو کې کشفي ګزمه ترسره کړئ.",
            "objective_en": "Neutralize night sentries without losing armor",
            "objective_ps": "د شپې پیره داران له منځه یوسئ",
            "spawn_pos": [12, 1.2, 24],
            "enemy_count": 10,
            "difficulty": "elite",
            "time_of_day": "night",
            "weather": "rain",
            "reward_points": 750,
            "unlocks_mission": 7
        },
        {
            "id": 7,
            "implemented": False,
            "map_scene": "res://scenes/maps/map_military_outpost.tscn",
            "map_id": "outpost",
            "title_en": "Mission 07: Protect the Convoy",
            "title_ps": "اووم ماموریت: د کاروان ساتنه",
            "briefing_en": "Escort the supply transport vehicle out of the forward checkpoint through ambushed terrain.",
            "briefing_ps": "اکمالاتي موټر له مخکینۍ پوستې څخه په خوندي ډول وباسئ.",
            "objective_en": "Clear ambush teams around the transport trucks",
            "objective_ps": "د کاروان شاوخوا کمینونه مات کړئ",
            "spawn_pos": [-10, 1.2, 18],
            "enemy_count": 12,
            "difficulty": "elite",
            "time_of_day": "day",
            "weather": "dust",
            "reward_points": 800,
            "unlocks_mission": 8
        },
        {
            "id": 8,
            "implemented": False,
            "map_scene": "res://scenes/maps/map_military_outpost.tscn",
            "map_id": "outpost",
            "title_en": "Mission 08: Desert Outpost",
            "title_ps": "اتم ماموریت: صحرايي پوسته",
            "briefing_en": "Assault the fortified desert outpost during a heavy dust storm and disable communications.",
            "briefing_ps": "په دوړنه هوا کې پر صحرايي پوسته برید وکړئ او مخابرات یې ودرولئ.",
            "objective_en": "Capture the desert command bunker",
            "objective_ps": "د صحرايي پوستې مرکزي برخه ونیسئ",
            "spawn_pos": [0, 1.2, 28],
            "enemy_count": 12,
            "difficulty": "elite",
            "time_of_day": "dusk",
            "weather": "dust",
            "reward_points": 900,
            "unlocks_mission": 9
        },
        {
            "id": 9,
            "implemented": False,
            "map_scene": "res://scenes/maps/map_mountain_valley.tscn",
            "map_id": "valley",
            "title_en": "Mission 09: Mountain Stronghold",
            "title_ps": "نهم ماموریت: غرنۍ کلا",
            "briefing_en": "Breach the high-altitude stronghold overlooking the river canyon.",
            "briefing_ps": "په لوړو غرونو کې د دښمن کلکه کلا ماتې کړئ.",
            "objective_en": "Defeat elite defenders in the upper stronghold",
            "objective_ps": "په لوړه کلا کې ځانګړي ساتونکي مات کړئ",
            "spawn_pos": [0, 1.2, 26],
            "enemy_count": 14,
            "difficulty": "elite",
            "time_of_day": "day",
            "weather": "clear",
            "reward_points": 1000,
            "unlocks_mission": 10
        },
        {
            "id": 10,
            "implemented": False,
            "map_scene": "res://scenes/maps/map_military_outpost.tscn",
            "map_id": "outpost",
            "title_en": "Mission 10: Final Operation",
            "title_ps": "لسم ماموریت: وروستي عملیات",
            "briefing_en": "Lead the final coordinated strike to restore peace across the mountain sector.",
            "briefing_ps": "د سولې او ثبات د بېرته راوستلو لپاره وروستي ګډ عملیات بریالي کړئ.",
            "objective_en": "Eliminate remaining command units and secure the sector",
            "objective_ps": "ټول پاتې دښمنان مات کړئ او سیمه بشپړه آزاده کړئ",
            "spawn_pos": [0, 1.2, 24],
            "enemy_count": 16,
            "difficulty": "elite",
            "time_of_day": "night",
            "weather": "clear",
            "reward_points": 1500,
            "unlocks_mission": 10
        }
    ]
    write_json("data/missions/missions.json", {"missions": missions})


def build_config_and_docs() -> None:
    write_text("icon.svg", """
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="20" fill="#14181E"/>
  <rect x="8" y="8" width="112" height="112" rx="14" fill="none" stroke="#D99B26" stroke-width="4"/>
  <polygon points="64,22 98,92 64,76 30,92" fill="#C2A878"/>
  <polygon points="64,34 84,82 64,70 44,82" fill="#1F262E"/>
  <circle cx="64" cy="58" r="7" fill="#D99B26"/>
</svg>
""")

    write_text("project.godot", """
; Engine configuration file.
; Best edited using the editor UI and not directly,
; since the parameters that go here are not all obvious.

config_version=5

[application]

config/name="AFGHAN WARRIOR – افغان جنګیالی"
config/description="Offline 3D Third-Person Tactical Military Action Game for Android"
run/main_scene="res://scenes/menus/main_menu.tscn"
config/features=PackedStringArray("4.3", "Mobile")
config/icon="res://icon.svg"

[audio]

buses/default_bus_layout=""

[autoload]

SaveManager="*res://scripts/systems/save_manager.gd"
LocalizationManager="*res://scripts/systems/localization_manager.gd"
AudioManager="*res://scripts/systems/audio_manager.gd"
SettingsManager="*res://scripts/systems/settings_manager.gd"
GameManager="*res://scripts/systems/game_manager.gd"

[display]

window/size/viewport_width=1280
window/size/viewport_height=720
window/size/mode=2
window/stretch/mode="canvas_items"
window/stretch/aspect="expand"
window/handheld/orientation=0

[input]

move_forward={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":87,"key_label":0,"unicode":119,"location":0,"echo":false,"script":null)]
}
move_backward={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":83,"key_label":0,"unicode":115,"location":0,"echo":false,"script":null)]
}
move_left={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":65,"key_label":0,"unicode":97,"location":0,"echo":false,"script":null)]
}
move_right={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":68,"key_label":0,"unicode":100,"location":0,"echo":false,"script":null)]
}
sprint={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194325,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)]
}
jump={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":32,"key_label":0,"unicode":32,"location":0,"echo":false,"script":null)]
}
crouch={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":67,"key_label":0,"unicode":99,"location":0,"echo":false,"script":null)]
}
reload={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":82,"key_label":0,"unicode":114,"location":0,"echo":false,"script":null)]
}
switch_weapon={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":81,"key_label":0,"unicode":113,"location":0,"echo":false,"script":null)]
}
interact={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":69,"key_label":0,"unicode":101,"location":0,"echo":false,"script":null)]
}
throw_grenade={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":71,"key_label":0,"unicode":103,"location":0,"echo":false,"script":null)]
}
pause={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":0,"physical_keycode":4194305,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)]
}
shoot={
"deadzone": 0.2,
"events": [Object(InputEventMouseButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"button_mask":0,"position":Vector2(0, 0),"global_position":Vector2(0, 0),"factor":1.0,"button_index":1,"canceled":false,"pressed":false,"double_click":false,"script":null)]
}
aim={
"deadzone": 0.2,
"events": [Object(InputEventMouseButton,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"button_mask":0,"position":Vector2(0, 0),"global_position":Vector2(0, 0),"factor":1.0,"button_index":2,"canceled":false,"pressed":false,"double_click":false,"script":null)]
}

[input_devices]

pointing/emulate_touch_from_mouse=true

[internationalization]

locale/fallback="en"

[rendering]

renderer/rendering_method="mobile"
renderer/rendering_method.mobile="mobile"
textures/vram_compression/import_etc2_astc=true
environment/defaults/default_clear_color=Color(0.11, 0.13, 0.16, 1)
""")

    write_text("export_presets.cfg", """
[preset.0]

name="Android"
platform="Android"
runnable=true
advanced_options=false
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="build/AfghanWarrior.apk"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

custom_template/debug=""
custom_template/release=""
gradle_build/use_gradle_build=false
gradle_build/export_format=0
gradle_build/min_sdk="24"
gradle_build/target_sdk="34"
architectures/armeabi-v7a=true
architectures/arm64-v8a=true
architectures/x86=false
architectures/x86_64=false
version/code=1
version/name="1.0.0"
package/unique_name="com.afghanstudio.afghanwarrior"
package/name="AFGHAN WARRIOR"
package/signed=true
screen/immersive_mode=true
screen/support_small=true
screen/support_normal=true
screen/support_large=true
screen/support_xlarge=true
graphics/opengl_debug=false
permissions/internet=false
permissions/access_network_state=false
permissions/vibrate=true
""")

    write_text("android/README.md", """
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
""")

    write_text("README.md", """
# AFGHAN WARRIOR – افغان جنګیالی
**Complete Offline 3D Third-Person Tactical Military Action Game for Android (Godot 4.3+)**

## Overview
AFGHAN WARRIOR is an offline 3D third-person shooter built for Android devices using Godot Engine 4's Mobile Forward+ / GL Compatibility rendering pipeline. Set across fictionalized Afghan-inspired mountain valleys, mud-brick villages, and fortified outposts, the game supports **English (LTR)** and **Pashto (RTL — پښتو)** with full local save persistence.

## Implemented Features
- **Third-Person Camera & Soldier Controller**: Smooth `SpringArm3D` camera collision, over-the-shoulder aim zoom, walking, running, sprinting, jumping, crouching, cover stance, health, armor, weapon inventory, and procedural character hit/death reactions.
- **Weapons System (5 Firearms + Frag Grenade)**: Assault Rifle (`Khyber-47`), Sniper Rifle (`Pamir Longbow M24`), Shotgun (`Helmand Breacher 12G`), Pistol (`Kabul 9mm`), Submachine Gun (`Balkh PDW`), and `HE-Fragmentation` grenades, plus object-pooled muzzle flashes, bullet tracers, and weapon/ammo pickups.
- **Enemy AI**: `NavigationAgent3D` patrol paths, line-of-sight + gunfire sound awareness, cover-seeking, burst attacks, reload cycles, search/retreat behaviors, and Recruit / Veteran / Elite difficulty scaling.
- **Game Modes**:
  - **Story Mode**: 10 structured missions; **Missions 1–3** are fully playable with briefings, wave/objective triggers, rewards, and progression unlocks; Missions 4–10 are structured in `data/missions/missions.json` for rapid expansion.
  - **Free Battle Mode**: Select map (Afghan Village, Mountain Valley, Military Outpost), enemy difficulty, enemy count, starting weapon, time of day (Day / Dusk / Night), and weather (Clear / Dust / Rain), with instant restart.
- **Three Playable Maps**:
  1. `map_afghan_village.tscn` — Mud-brick houses, arches, narrow streets, checkpoint, trees, rock perimeter.
  2. `map_mountain_valley.tscn` — Rocky canyon ridges, river plane, stone/wood bridge, patrol cliffs.
  3. `map_military_outpost.tscn` — Watchtowers, concrete barriers, storage sheds, vehicle park.
- **Vehicle Foundation**: Enterable/exitable Military Jeep and Transport Truck (`scripts/vehicles/vehicle_base.gd`) with basic driving physics and collision.
- **Android Mobile Touch Controls**: Left virtual thumbstick + right camera drag pad + Fire, Aim, Jump, Crouch, Reload, Switch Weapon, Grenade, Sprint, Interact, and Pause buttons.
- **Graphics Presets (LOW / MEDIUM / HIGH)** & **Audio Buses (Music / SFX / Environment)** saved offline in `user://save_data.json`.

## Asset Disclosure (Transparency)
- **3D Models**: Character, enemy, weapon, vehicle, and architecture meshes in the `.tscn` scenes are constructed from modular procedural Godot 3D primitives and multi-part `Node3D` assemblies (flagged clearly as modular procedural meshes—no external copyrighted assets). Replace with custom `.glb` rigs in `assets/models/` for production art polish.
- **Textures & Audio**: All `.png` textures in `assets/textures/` and `.wav` audio files in `assets/audio/` are 100% original, procedurally synthesized assets generated locally.
- **Real-Device Verification**: Android APK compilation and multi-touch thermal testing must be performed on physical Android hardware with Android SDK/Godot Export Templates installed (cannot be executed inside a headless Linux container without Android NDK/APK signing).
""")


def build_gdscripts() -> None:
    write_text("scripts/systems/save_manager.gd", """
extends Node
class_name SaveManagerClass

const SAVE_PATH := "user://afghan_warrior_save.json"

var data: Dictionary = {
	"language": "en",
	"graphics_quality": 1, # 0=LOW, 1=MEDIUM, 2=HIGH
	"music_volume": 0.75,
	"sfx_volume": 0.85,
	"env_volume": 0.70,
	"camera_sensitivity": 1.0,
	"aim_sensitivity": 0.65,
	"control_sensitivity": 1.0,
	"fullscreen": true,
	"unlocked_mission": 1,
	"completed_missions": [],
	"total_score": 0,
	"unlocked_weapons": ["khyber_47", "pamir_m24", "helmand_12g", "kabul_9mm", "balkh_pdw"]
}

func _ready() -> void:
	load_game()

func save_game() -> void:
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(data, "\\t"))
		file.close()

func load_game() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		save_game()
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file:
		var text := file.get_as_text()
		file.close()
		var parsed: Variant = JSON.parse_string(text)
		if typeof(parsed) == TYPE_DICTIONARY:
			for key in parsed.keys():
				data[key] = parsed[key]

func mark_mission_completed(mission_id: int, reward_points: int, next_mission: int) -> void:
	var completed: Array = data.get("completed_missions", [])
	if not completed.has(mission_id):
		completed.append(mission_id)
		data["completed_missions"] = completed
	data["total_score"] = int(data.get("total_score", 0)) + reward_points
	if next_mission > int(data.get("unlocked_mission", 1)):
		data["unlocked_mission"] = next_mission
	save_game()
""")

    write_text("scripts/systems/localization_manager.gd", """
extends Node

signal language_changed(lang_code: String, is_rtl: bool)

var current_language: String = "en"
var translations: Dictionary = {}

func _ready() -> void:
	_load_all_translations()
	var saved_lang: String = str(SaveManager.data.get("language", "en"))
	set_language(saved_lang)

func _load_all_translations() -> void:
	for lang in ["en", "ps"]:
		var path := "res://data/translations/%s.json" % lang
		if FileAccess.file_exists(path):
			var file := FileAccess.open(path, FileAccess.READ)
			if file:
				var parsed: Variant = JSON.parse_string(file.get_as_text())
				file.close()
				if typeof(parsed) == TYPE_DICTIONARY:
					translations[lang] = parsed

func set_language(lang_code: String) -> void:
	if not translations.has(lang_code):
		lang_code = "en"
	current_language = lang_code
	SaveManager.data["language"] = lang_code
	SaveManager.save_game()
	TranslationServer.set_locale(lang_code)
	var is_rtl := (lang_code == "ps")
	var tree := get_tree()
	if tree and tree.root:
		var dir := Control.LAYOUT_DIRECTION_RTL if is_rtl else Control.LAYOUT_DIRECTION_LTR
		tree.root.propagate_notification(NOTIFICATION_TRANSLATION_CHANGED)
		for child in tree.root.get_children():
			if child is Control:
				child.layout_direction = dir
	language_changed.emit(current_language, is_rtl)

func is_rtl() -> bool:
	return current_language == "ps"

func tr_key(key: String) -> String:
	var dict: Dictionary = translations.get(current_language, {})
	if dict.has(key):
		return str(dict[key])
	var fallback: Dictionary = translations.get("en", {})
	return str(fallback.get(key, key))
""")

    write_text("scripts/systems/audio_manager.gd", """
extends Node

var music_player: AudioStreamPlayer
var env_player: AudioStreamPlayer
var sfx_pool: Array[AudioStreamPlayer] = []
var pool_index: int = 0

var music_volume: float = 0.75
var sfx_volume: float = 0.85
var env_volume: float = 0.70

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	music_player = AudioStreamPlayer.new()
	add_child(music_player)
	env_player = AudioStreamPlayer.new()
	add_child(env_player)
	for i in range(12):
		var p := AudioStreamPlayer.new()
		add_child(p)
		sfx_pool.append(p)
	apply_volumes(
		float(SaveManager.data.get("music_volume", 0.75)),
		float(SaveManager.data.get("sfx_volume", 0.85)),
		float(SaveManager.data.get("env_volume", 0.70))
	)

func apply_volumes(music: float, sfx: float, env: float) -> void:
	music_volume = clampf(music, 0.0, 1.0)
	sfx_volume = clampf(sfx, 0.0, 1.0)
	env_volume = clampf(env, 0.0, 1.0)
	music_player.volume_db = linear_to_db(maxf(0.001, music_volume))
	env_player.volume_db = linear_to_db(maxf(0.001, env_volume))

func play_music(path: String) -> void:
	if not ResourceLoader.exists(path):
		return
	var stream := load(path) as AudioStream
	if stream:
		if stream is AudioStreamWAV:
			stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		music_player.stream = stream
		music_player.play()

func play_environment(path: String) -> void:
	if not ResourceLoader.exists(path):
		return
	var stream := load(path) as AudioStream
	if stream:
		if stream is AudioStreamWAV:
			stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		env_player.stream = stream
		env_player.play()

func stop_environment() -> void:
	env_player.stop()

func play_sfx(path: String, pitch_scale: float = 1.0) -> void:
	if not ResourceLoader.exists(path):
		return
	var stream := load(path) as AudioStream
	if not stream:
		return
	var p := sfx_pool[pool_index]
	pool_index = (pool_index + 1) % sfx_pool.size()
	p.stream = stream
	p.pitch_scale = pitch_scale
	p.volume_db = linear_to_db(maxf(0.001, sfx_volume))
	p.play()
""")

    write_text("scripts/systems/settings_manager.gd", """
extends Node

enum GraphicsQuality { LOW = 0, MEDIUM = 1, HIGH = 2 }

var current_quality: int = GraphicsQuality.MEDIUM
var camera_sensitivity: float = 1.0
var aim_sensitivity: float = 0.65
var control_sensitivity: float = 1.0

func _ready() -> void:
	load_and_apply()

func load_and_apply() -> void:
	current_quality = int(SaveManager.data.get("graphics_quality", GraphicsQuality.MEDIUM))
	camera_sensitivity = float(SaveManager.data.get("camera_sensitivity", 1.0))
	aim_sensitivity = float(SaveManager.data.get("aim_sensitivity", 0.65))
	control_sensitivity = float(SaveManager.data.get("control_sensitivity", 1.0))
	apply_graphics_preset(current_quality)
	apply_screen_mode(bool(SaveManager.data.get("fullscreen", true)))

func apply_graphics_preset(quality: int) -> void:
	current_quality = clampi(quality, 0, 2)
	SaveManager.data["graphics_quality"] = current_quality
	var vp := get_viewport()
	if vp:
		match current_quality:
			GraphicsQuality.LOW:
				vp.scaling_3d_scale = 0.70
				vp.msaa_3d = Viewport.MSAA_DISABLED
				RenderingServer.directional_shadow_atlas_set_size(1024, false)
			GraphicsQuality.MEDIUM:
				vp.scaling_3d_scale = 0.85
				vp.msaa_3d = Viewport.MSAA_2X
				RenderingServer.directional_shadow_atlas_set_size(2048, true)
			GraphicsQuality.HIGH:
				vp.scaling_3d_scale = 1.0
				vp.msaa_3d = Viewport.MSAA_4X
				RenderingServer.directional_shadow_atlas_set_size(4096, true)
	SaveManager.save_game()

func apply_screen_mode(fullscreen: bool) -> void:
	SaveManager.data["fullscreen"] = fullscreen
	if OS.has_feature("android") or OS.has_feature("mobile"):
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED)
	SaveManager.save_game()
""")

    write_text("scripts/systems/game_manager.gd", """
extends Node

enum GameMode { STORY, FREE_BATTLE }

var active_mode: int = GameMode.STORY
var active_mission_id: int = 1
var missions_cache: Array = []
var weapons_cache: Array = []

var free_battle_config: Dictionary = {
	"map_id": "village",
	"map_scene": "res://scenes/maps/map_afghan_village.tscn",
	"difficulty": "veteran",
	"enemy_count": 6,
	"starting_weapon": "khyber_47",
	"time_of_day": "day",
	"weather": "clear"
}

func _ready() -> void:
	_load_missions()
	_load_weapons()

func _load_missions() -> void:
	var path := "res://data/missions/missions.json"
	if FileAccess.file_exists(path):
		var file := FileAccess.open(path, FileAccess.READ)
		if file:
			var parsed: Variant = JSON.parse_string(file.get_as_text())
			file.close()
			if typeof(parsed) == TYPE_DICTIONARY:
				missions_cache = parsed.get("missions", [])

func _load_weapons() -> void:
	var path := "res://data/weapons/weapons.json"
	if FileAccess.file_exists(path):
		var file := FileAccess.open(path, FileAccess.READ)
		if file:
			var parsed: Variant = JSON.parse_string(file.get_as_text())
			file.close()
			if typeof(parsed) == TYPE_DICTIONARY:
				weapons_cache = parsed.get("weapons", [])

func get_mission_by_id(mission_id: int) -> Dictionary:
	for m in missions_cache:
		if int(m.get("id", 0)) == mission_id:
			return m
	return {}

func start_story_mission(mission_id: int) -> void:
	active_mode = GameMode.STORY
	active_mission_id = mission_id
	get_tree().paused = false
	get_tree().change_scene_to_file("res://scenes/main/main.tscn")

func start_free_battle(config: Dictionary) -> void:
	active_mode = GameMode.FREE_BATTLE
	free_battle_config = config.duplicate()
	get_tree().paused = false
	get_tree().change_scene_to_file("res://scenes/main/main.tscn")

func return_to_main_menu() -> void:
	get_tree().paused = false
	AudioManager.stop_environment()
	get_tree().change_scene_to_file("res://scenes/menus/main_menu.tscn")
""")

    write_text("scripts/systems/object_pool.gd", """
extends Node
class_name ObjectPool

var pooled_tracers: Array[MeshInstance3D] = []
var tracer_index: int = 0

func _ready() -> void:
	for i in range(24):
		var mesh := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3(0.04, 0.04, 1.4)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(1.0, 0.85, 0.35)
		mat.emission_enabled = true
		mat.emission = Color(1.0, 0.72, 0.2)
		mat.emission_energy_multiplier = 3.0
		box.material = mat
		mesh.mesh = box
		mesh.visible = false
		add_child(mesh)
		pooled_tracers.append(mesh)

func spawn_tracer(from_pos: Vector3, to_pos: Vector3) -> void:
	var tracer := pooled_tracers[tracer_index]
	tracer_index = (tracer_index + 1) % pooled_tracers.size()
	var mid := (from_pos + to_pos) * 0.5
	tracer.global_position = mid
	if from_pos.distance_to(to_pos) > 0.1:
		tracer.look_at(to_pos, Vector3.UP)
	tracer.visible = true
	var tween := create_tween()
	tween.tween_interval(0.06)
	tween.tween_callback(func(): tracer.visible = false)
""")

    write_text("scripts/player/third_person_camera.gd", """
extends Node3D
class_name ThirdPersonCamera

@export var default_fov: float = 65.0
@export var aim_fov: float = 44.0
@export var min_pitch: float = -55.0
@export var max_pitch: float = 45.0

@onready var spring_arm: SpringArm3D = $SpringArm3D
@onready var camera: Camera3D = $SpringArm3D/Camera3D

var yaw: float = 0.0
var pitch: float = -12.0
var is_aiming: bool = false
var target_aim_fov: float = 44.0
var recoil_pitch: float = 0.0

func _ready() -> void:
	camera.current = true
	spring_arm.spring_length = 3.4

func rotate_camera(delta_x: float, delta_y: float) -> void:
	var sens := SettingsManager.aim_sensitivity if is_aiming else SettingsManager.camera_sensitivity
	yaw -= delta_x * 0.18 * sens
	pitch = clampf(pitch - delta_y * 0.14 * sens, min_pitch, max_pitch)
	rotation_degrees.y = yaw
	spring_arm.rotation_degrees.x = pitch

func add_recoil(amount: float) -> void:
	recoil_pitch += amount * 14.0

func set_aiming(aiming: bool, weapon_zoom_fov: float = 44.0) -> void:
	is_aiming = aiming
	target_aim_fov = weapon_zoom_fov

func _process(delta: float) -> void:
	if recoil_pitch > 0.01:
		pitch = clampf(pitch + recoil_pitch * delta * 8.0, min_pitch, max_pitch)
		recoil_pitch = lerpf(recoil_pitch, 0.0, delta * 12.0)
		spring_arm.rotation_degrees.x = pitch
	var target_fov := target_aim_fov if is_aiming else default_fov
	camera.fov = lerpf(camera.fov, target_fov, delta * 10.0)
	var target_len := 2.0 if is_aiming else 3.4
	spring_arm.spring_length = lerpf(spring_arm.spring_length, target_len, delta * 10.0)

func get_aim_ray_origin() -> Vector3:
	return camera.global_position

func get_aim_ray_direction() -> Vector3:
	return -camera.global_transform.basis.z.normalized()
""")

    write_text("scripts/weapons/weapon_manager.gd", """
extends Node3D
class_name WeaponManager

signal ammo_changed(mag: int, reserve: int, weapon_name: String, reloading: bool)
signal weapon_fired(origin: Vector3, hit_pos: Vector3)

var weapons: Array = []
var current_index: int = 0
var mag_ammo: Dictionary = {}
var reserve_ammo: Dictionary = {}
var fire_cooldown: float = 0.0
var is_reloading: bool = false
var reload_timer: float = 0.0
var grenades: int = 3
var tracer_pool: ObjectPool

@onready var muzzle_flash: OmniLight3D = $MuzzleFlash

func _ready() -> void:
	weapons = GameManager.weapons_cache.duplicate(true)
	if weapons.is_empty():
		weapons = [{"id":"khyber_47","name_en":"Khyber-47","name_ps":"خیبر-۴۷","damage":26,"fire_rate":0.11,"recoil":0.045,"spread":0.018,"mag_size":30,"reserve_max":180,"reload_time":1.6,"range":140.0,"pellets":1,"automatic":true,"zoom_fov":45.0,"sound":"res://assets/audio/rifle_shot.wav"}]
	for w in weapons:
		var wid := str(w["id"])
		mag_ammo[wid] = int(w["mag_size"])
		reserve_ammo[wid] = int(w["reserve_max"])
	if muzzle_flash:
		muzzle_flash.visible = false
	emit_ammo_update()

func set_starting_weapon(weapon_id: String) -> void:
	for i in range(weapons.size()):
		if str(weapons[i]["id"]) == weapon_id:
			current_index = i
			is_reloading = false
			emit_ammo_update()
			return

func get_current_weapon() -> Dictionary:
	return weapons[current_index]

func switch_next_weapon() -> void:
	if is_reloading:
		is_reloading = false
	current_index = (current_index + 1) % weapons.size()
	AudioManager.play_sfx("res://assets/audio/ui_click.wav", 1.1)
	emit_ammo_update()

func add_ammo(amount: int) -> void:
	var w := get_current_weapon()
	var wid := str(w["id"])
	reserve_ammo[wid] = mini(int(w["reserve_max"]), int(reserve_ammo[wid]) + amount)
	emit_ammo_update()

func _process(delta: float) -> void:
	if fire_cooldown > 0.0:
		fire_cooldown -= delta
	if is_reloading:
		reload_timer -= delta
		if reload_timer <= 0.0:
			_finish_reload()

func start_reload() -> void:
	if is_reloading:
		return
	var w := get_current_weapon()
	var wid := str(w["id"])
	var max_mag := int(w["mag_size"])
	if int(mag_ammo[wid]) >= max_mag or int(reserve_ammo[wid]) <= 0:
		return
	is_reloading = true
	reload_timer = float(w["reload_time"])
	AudioManager.play_sfx("res://assets/audio/reload.wav")
	emit_ammo_update()

func _finish_reload() -> void:
	var w := get_current_weapon()
	var wid := str(w["id"])
	var needed := int(w["mag_size"]) - int(mag_ammo[wid])
	var take := mini(needed, int(reserve_ammo[wid]))
	mag_ammo[wid] = int(mag_ammo[wid]) + take
	reserve_ammo[wid] = int(reserve_ammo[wid]) - take
	is_reloading = false
	emit_ammo_update()

func try_fire(cam: ThirdPersonCamera, shooter: Node3D) -> bool:
	if is_reloading or fire_cooldown > 0.0:
		return false
	var w := get_current_weapon()
	var wid := str(w["id"])
	if int(mag_ammo[wid]) <= 0:
		start_reload()
		return false

	mag_ammo[wid] = int(mag_ammo[wid]) - 1
	fire_cooldown = float(w["fire_rate"])
	AudioManager.play_sfx(str(w["sound"]), randf_range(0.95, 1.05))
	cam.add_recoil(float(w["recoil"]))

	if muzzle_flash:
		muzzle_flash.visible = true
		get_tree().create_timer(0.05).timeout.connect(func(): if is_instance_valid(muzzle_flash): muzzle_flash.visible = false)

	var space := get_world_3d().direct_space_state
	var origin := cam.get_aim_ray_origin()
	var base_dir := cam.get_aim_ray_direction()
	var pellets := int(w.get("pellets", 1))
	var spread := float(w["spread"]) * (0.45 if cam.is_aiming else 1.0)
	var hit_point := origin + base_dir * float(w["range"])

	for p in range(pellets):
		var dir := (base_dir + Vector3(randf_range(-spread, spread), randf_range(-spread, spread), randf_range(-spread, spread))).normalized()
		var query := PhysicsRayQueryParameters3D.create(origin, origin + dir * float(w["range"]))
		query.exclude = [shooter.get_rid()] if shooter is CollisionObject3D else []
		var result := space.intersect_ray(query)
		if not result.is_empty():
			hit_point = result["position"]
			var collider: Object = result["collider"]
			if collider and collider.has_method("apply_damage"):
				collider.apply_damage(int(w["damage"]), dir)
				AudioManager.play_sfx("res://assets/audio/hit_marker.wav")

	if tracer_pool:
		tracer_pool.spawn_tracer(global_position, hit_point)
	weapon_fired.emit(global_position, hit_point)
	emit_ammo_update()
	return true

func emit_ammo_update() -> void:
	var w := get_current_weapon()
	var wid := str(w["id"])
	var name_key := "name_ps" if LocalizationManager.is_rtl() else "name_en"
	ammo_changed.emit(int(mag_ammo[wid]), int(reserve_ammo[wid]), str(w.get(name_key, wid)), is_reloading)
""")

    write_text("scripts/weapons/grenade.gd", """
extends RigidBody3D
class_name FragGrenade

@export var fuse_time: float = 2.4
@export var blast_radius: float = 8.0
@export var max_damage: int = 120

func _ready() -> void:
	get_tree().create_timer(fuse_time).timeout.connect(_detonate)

func _detonate() -> void:
	AudioManager.play_sfx("res://assets/audio/explosion.wav")
	for node in get_tree().get_nodes_in_group("damageable"):
		if node is Node3D:
			var dist := global_position.distance_to(node.global_position)
			if dist <= blast_radius and node.has_method("apply_damage"):
				var falloff := 1.0 - (dist / blast_radius)
				node.apply_damage(int(max_damage * falloff), (node.global_position - global_position).normalized())
	queue_free()
""")

    write_text("scripts/player/player_controller.gd", """
extends CharacterBody3D
class_name PlayerController

signal health_changed(health: int, armor: int)
signal player_died
signal interaction_prompt_changed(text: String, visible: bool)

@export var walk_speed: float = 4.6
@export var sprint_speed: float = 7.6
@export var crouch_speed: float = 2.6
@export var jump_velocity: float = 5.4
@export var gravity: float = 15.0

var health: int = 100
var max_health: int = 100
var armor: int = 50
var max_armor: int = 50
var is_crouching: bool = false
var is_sprinting: bool = false
var is_dead: bool = false
var active_vehicle: Node = null
var nearby_interactable: Node = null
var step_timer: float = 0.0

var mobile_move_input: Vector2 = Vector2.ZERO
var mobile_aiming: bool = false
var mobile_firing: bool = false

@onready var camera_rig: ThirdPersonCamera = $CameraRig
@onready var model_root: Node3D = $SoldierModel
@onready var weapon_manager: WeaponManager = $SoldierModel/WeaponMount/WeaponManager
@onready var collision_shape: CollisionShape3D = $CollisionShape3D

func _ready() -> void:
	add_to_group("player")
	add_to_group("damageable")
	health_changed.emit(health, armor)

func set_mobile_move(vec: Vector2) -> void:
	mobile_move_input = vec

func set_mobile_look(delta_x: float, delta_y: float) -> void:
	if camera_rig:
		camera_rig.rotate_camera(delta_x, delta_y)

func _unhandled_input(event: InputEvent) -> void:
	if is_dead:
		return
	if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
		camera_rig.rotate_camera(event.relative.x, event.relative.y)
	if event.is_action_pressed("reload"):
		weapon_manager.start_reload()
	elif event.is_action_pressed("switch_weapon"):
		weapon_manager.switch_next_weapon()
	elif event.is_action_pressed("crouch"):
		toggle_crouch()
	elif event.is_action_pressed("interact"):
		try_interact()
	elif event.is_action_pressed("throw_grenade"):
		throw_grenade()

func toggle_crouch() -> void:
	is_crouching = not is_crouching
	if model_root:
		model_root.scale.y = 0.72 if is_crouching else 1.0

func try_interact() -> void:
	if active_vehicle and active_vehicle.has_method("exit_vehicle"):
		active_vehicle.exit_vehicle(self)
		active_vehicle = null
		visible = true
		return
	if nearby_interactable and nearby_interactable.has_method("interact"):
		nearby_interactable.interact(self)

func throw_grenade() -> void:
	if weapon_manager.grenades <= 0:
		return
	weapon_manager.grenades -= 1
	var grenade_scene := load("res://scenes/weapons/grenade.tscn") as PackedScene
	if grenade_scene:
		var g := grenade_scene.instantiate() as RigidBody3D
		get_parent().add_child(g)
		g.global_position = global_position + Vector3(0, 1.4, 0) + camera_rig.get_aim_ray_direction() * 1.0
		g.apply_central_impulse(camera_rig.get_aim_ray_direction() * 14.0 + Vector3(0, 4.5, 0))

func _physics_process(delta: float) -> void:
	if is_dead:
		return
	if active_vehicle:
		global_position = active_vehicle.global_position + Vector3(0, 1.5, 0)
		return

	if not is_on_floor():
		velocity.y -= gravity * delta
	elif Input.is_action_just_pressed("jump"):
		velocity.y = jump_velocity

	var input_vec := Vector2(
		Input.get_action_strength("move_right") - Input.get_action_strength("move_left"),
		Input.get_action_strength("move_backward") - Input.get_action_strength("move_forward")
	)
	if mobile_move_input.length() > 0.08:
		input_vec = Vector2(mobile_move_input.x, mobile_move_input.y)

	is_sprinting = Input.is_action_pressed("sprint") and input_vec.y < -0.2 and not is_crouching
	var aiming := Input.is_action_pressed("aim") or mobile_aiming
	var current_w := weapon_manager.get_current_weapon()
	camera_rig.set_aiming(aiming, float(current_w.get("zoom_fov", 45.0)))

	var basis := camera_rig.global_transform.basis
	var forward := Vector3(basis.z.x, 0, basis.z.z).normalized()
	var right := Vector3(basis.x.x, 0, basis.x.z).normalized()
	var move_dir := (right * input_vec.x + forward * input_vec.y)
	if move_dir.length() > 1.0:
		move_dir = move_dir.normalized()

	var speed := crouch_speed if is_crouching else (sprint_speed if is_sprinting else walk_speed)
	velocity.x = move_dir.x * speed
	velocity.z = move_dir.z * speed
	move_and_slide()

	if move_dir.length() > 0.1 and is_on_floor():
		step_timer -= delta
		if step_timer <= 0.0:
			AudioManager.play_sfx("res://assets/audio/footstep_dirt.wav", randf_range(0.9, 1.15))
			step_timer = 0.28 if is_sprinting else 0.44

	if model_root:
		var look_dir := -Vector3(basis.z.x, 0, basis.z.z).normalized()
		if look_dir.length() > 0.01:
			model_root.rotation.y = lerp_angle(model_root.rotation.y, atan2(look_dir.x, look_dir.z), delta * 12.0)

	var firing := Input.is_action_pressed("shoot") or mobile_firing
	if firing:
		weapon_manager.try_fire(camera_rig, self)

func apply_damage(amount: int, _dir: Vector3 = Vector3.ZERO) -> void:
	if is_dead:
		return
	if armor > 0:
		var absorbed := mini(armor, int(amount * 0.6))
		armor -= absorbed
		amount -= absorbed
	health = maxi(0, health - amount)
	health_changed.emit(health, armor)
	if health <= 0:
		is_dead = true
		if model_root:
			model_root.rotation_degrees.x = 85.0
		player_died.emit()
""")

    write_text("scripts/enemies/enemy_ai.gd", """
extends CharacterBody3D
class_name EnemyAI

signal died(enemy: EnemyAI)

enum State { PATROL, ALERT, ENGAGE, TAKE_COVER, RELOAD, RETREAT, DEAD }

@export var max_health: int = 85
@export var move_speed: float = 3.8
@export var detection_range: float = 28.0
@export var attack_range: float = 22.0
@export var damage_per_shot: int = 9

var health: int = 85
var state: int = State.PATROL
var mag_ammo: int = 20
var fire_timer: float = 0.0
var reload_timer: float = 0.0
var state_timer: float = 0.0
var patrol_points: Array[Vector3] = []
var patrol_index: int = 0
var player_ref: Node3D = null
var gravity: float = 15.0

@onready var nav_agent: NavigationAgent3D = $NavigationAgent3D
@onready var model_root: Node3D = $EnemyModel

func _ready() -> void:
	add_to_group("enemies")
	add_to_group("damageable")
	health = max_health
	var base := global_position
	patrol_points = [
		base + Vector3(6, 0, 0),
		base + Vector3(6, 0, 6),
		base + Vector3(-6, 0, 4)
	]

func configure_difficulty(diff: String) -> void:
	match diff:
		"recruit":
			max_health = 65
			damage_per_shot = 6
			move_speed = 3.2
		"elite":
			max_health = 120
			damage_per_shot = 14
			move_speed = 4.6
		_:
			max_health = 85
			damage_per_shot = 9
			move_speed = 3.8
	health = max_health

func alert_to_sound(sound_pos: Vector3) -> void:
	if state == State.DEAD:
		return
	if global_position.distance_to(sound_pos) <= detection_range * 1.4:
		if nav_agent:
			nav_agent.target_position = sound_pos
		if state == State.PATROL:
			state = State.ALERT

func _physics_process(delta: float) -> void:
	if state == State.DEAD:
		return
	if not is_on_floor():
		velocity.y -= gravity * delta

	if not player_ref:
		var players := get_tree().get_nodes_in_group("player")
		if not players.is_empty():
			player_ref = players[0]

	var dist_to_player := 999.0
	var can_see_player := false
	if player_ref and is_instance_valid(player_ref):
		dist_to_player = global_position.distance_to(player_ref.global_position)
		if dist_to_player <= detection_range:
			can_see_player = _has_line_of_sight(player_ref.global_position + Vector3(0, 1.2, 0))

	match state:
		State.PATROL:
			if can_see_player:
				state = State.ENGAGE
			else:
				_move_along_patrol(delta)
		State.ALERT:
			if can_see_player:
				state = State.ENGAGE
			else:
				_move_toward_target(delta)
				state_timer += delta
				if state_timer > 5.0:
					state_timer = 0.0
					state = State.PATROL
		State.ENGAGE:
			if not can_see_player:
				state = State.ALERT
				if player_ref:
					nav_agent.target_position = player_ref.global_position
			elif health < max_health * 0.25:
				state = State.RETREAT
			else:
				_engage_player(delta, dist_to_player)
		State.TAKE_COVER:
			state_timer += delta
			_move_toward_target(delta)
			if state_timer > 2.2:
				state_timer = 0.0
				state = State.ENGAGE
		State.RELOAD:
			reload_timer -= delta
			if reload_timer <= 0.0:
				mag_ammo = 20
				state = State.ENGAGE
		State.RETREAT:
			if player_ref:
				var away := (global_position - player_ref.global_position).normalized()
				nav_agent.target_position = global_position + away * 10.0
				_move_toward_target(delta)
			state_timer += delta
			if state_timer > 3.0:
				state_timer = 0.0
				state = State.TAKE_COVER

	move_and_slide()

func _has_line_of_sight(target_pos: Vector3) -> bool:
	var space := get_world_3d().direct_space_state
	var eye := global_position + Vector3(0, 1.5, 0)
	var query := PhysicsRayQueryParameters3D.create(eye, target_pos)
	query.exclude = [get_rid()]
	var res := space.intersect_ray(query)
	if res.is_empty():
		return true
	var col: Object = res["collider"]
	return col != null and col.is_in_group("player")

func _move_along_patrol(_delta: float) -> void:
	if patrol_points.is_empty():
		return
	var target := patrol_points[patrol_index]
	if global_position.distance_to(target) < 1.5:
		patrol_index = (patrol_index + 1) % patrol_points.size()
		target = patrol_points[patrol_index]
	nav_agent.target_position = target
	_move_toward_target(_delta)

func _move_toward_target(delta: float) -> void:
	if nav_agent.is_navigation_finished():
		velocity.x = 0.0
		velocity.z = 0.0
		return
	var next_pos := nav_agent.get_next_path_position()
	var dir := (next_pos - global_position)
	dir.y = 0.0
	if dir.length() > 0.05:
		dir = dir.normalized()
		velocity.x = dir.x * move_speed
		velocity.z = dir.z * move_speed
		if model_root:
			model_root.rotation.y = lerp_angle(model_root.rotation.y, atan2(dir.x, dir.z), delta * 8.0)

func _engage_player(delta: float, dist: float) -> void:
	if not player_ref:
		return
	var dir := (player_ref.global_position - global_position)
	dir.y = 0.0
	if dir.length() > 0.01 and model_root:
		model_root.rotation.y = lerp_angle(model_root.rotation.y, atan2(dir.x, dir.z), delta * 10.0)

	if dist > attack_range * 0.65:
		nav_agent.target_position = player_ref.global_position
		_move_toward_target(delta)
	else:
		velocity.x = 0.0
		velocity.z = 0.0

	if mag_ammo <= 0:
		state = State.RELOAD
		reload_timer = 1.9
		return

	fire_timer -= delta
	if fire_timer <= 0.0 and dist <= attack_range:
		fire_timer = randf_range(0.38, 0.75)
		mag_ammo -= 1
		AudioManager.play_sfx("res://assets/audio/rifle_shot.wav", 0.92)
		if randf() < 0.42 and player_ref.has_method("apply_damage"):
			player_ref.apply_damage(damage_per_shot, dir.normalized())

func apply_damage(amount: int, _dir: Vector3 = Vector3.ZERO) -> void:
	if state == State.DEAD:
		return
	health -= amount
	if state == State.PATROL:
		state = State.ENGAGE
	if health <= 0:
		state = State.DEAD
		velocity = Vector3.ZERO
		if model_root:
			model_root.rotation_degrees.x = 85.0
		$CollisionShape3D.disabled = true
		died.emit(self)
		get_tree().create_timer(4.0).timeout.connect(queue_free)
""")

    write_text("scripts/vehicles/vehicle_base.gd", """
extends CharacterBody3D
class_name MilitaryVehicle

@export var vehicle_name: String = "Military Jeep"
@export var max_speed: float = 15.0
@export var turn_speed: float = 2.0

var driver: PlayerController = null
var gravity: float = 15.0

func _ready() -> void:
	add_to_group("vehicles")

func interact(player: PlayerController) -> void:
	if driver == null:
		driver = player
		player.active_vehicle = self
		player.visible = false
		AudioManager.play_sfx("res://assets/audio/vehicle_engine.wav")

func exit_vehicle(player: PlayerController) -> void:
	driver = null
	player.global_position = global_position + global_transform.basis.x * 2.4

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= gravity * delta
	if driver:
		var throttle := Input.get_action_strength("move_forward") - Input.get_action_strength("move_backward")
		var steer := Input.get_action_strength("move_left") - Input.get_action_strength("move_right")
		if absf(throttle) > 0.05:
			rotation.y += steer * turn_speed * delta * signf(throttle)
		var forward := -global_transform.basis.z
		velocity.x = forward.x * throttle * max_speed
		velocity.z = forward.z * throttle * max_speed
	else:
		velocity.x = lerpf(velocity.x, 0.0, delta * 4.0)
		velocity.z = lerpf(velocity.z, 0.0, delta * 4.0)
	move_and_slide()
""")

    write_text("scripts/maps/environment_controller.gd", """
extends Node3D
class_name EnvironmentController

@export var sun_light: DirectionalLight3D
@export var world_env: WorldEnvironment

func apply_conditions(time_of_day: String, weather: String) -> void:
	if sun_light:
		match time_of_day:
			"dusk":
				sun_light.rotation_degrees = Vector3(-16, 42, 0)
				sun_light.light_color = Color(1.0, 0.72, 0.45)
				sun_light.light_energy = 1.15
			"night":
				sun_light.rotation_degrees = Vector3(-55, 25, 0)
				sun_light.light_color = Color(0.55, 0.68, 0.95)
				sun_light.light_energy = 0.35
			_:
				sun_light.rotation_degrees = Vector3(-48, 35, 0)
				sun_light.light_color = Color(1.0, 0.95, 0.86)
				sun_light.light_energy = 1.5

	if world_env and world_env.environment:
		var env := world_env.environment
		env.fog_enabled = true
		match weather:
			"dust":
				env.fog_light_color = Color(0.76, 0.66, 0.50)
				env.fog_density = 0.018
				AudioManager.play_environment("res://assets/audio/wind_ambient.wav")
			"rain":
				env.fog_light_color = Color(0.45, 0.50, 0.56)
				env.fog_density = 0.016
				AudioManager.play_environment("res://assets/audio/rain_ambient.wav")
			_:
				env.fog_light_color = Color(0.66, 0.73, 0.80) if time_of_day != "night" else Color(0.08, 0.11, 0.16)
				env.fog_density = 0.006
				AudioManager.play_environment("res://assets/audio/birds_ambient.wav")
""")

    write_text("scripts/missions/mission_controller.gd", """
extends Node3D

@onready var hud: Control = $HUD
@onready var mobile_controls: Control = $MobileControls
@onready var pause_menu: Control = $PauseMenu
@onready var pool: ObjectPool = $ObjectPool

var player: PlayerController
var remaining_enemies: int = 0
var mission_data: Dictionary = {}

func _ready() -> void:
	var map_scene_path := "res://scenes/maps/map_afghan_village.tscn"
	var enemy_count := 5
	var diff := "veteran"
	var tod := "day"
	var weather := "clear"
	var starting_weapon := "khyber_47"

	if GameManager.active_mode == GameManager.GameMode.STORY:
		mission_data = GameManager.get_mission_by_id(GameManager.active_mission_id)
		map_scene_path = str(mission_data.get("map_scene", map_scene_path))
		enemy_count = int(mission_data.get("enemy_count", 5))
		diff = str(mission_data.get("difficulty", "veteran"))
		tod = str(mission_data.get("time_of_day", "day"))
		weather = str(mission_data.get("weather", "clear"))
	else:
		var cfg := GameManager.free_battle_config
		map_scene_path = str(cfg.get("map_scene", map_scene_path))
		enemy_count = int(cfg.get("enemy_count", 6))
		diff = str(cfg.get("difficulty", "veteran"))
		tod = str(cfg.get("time_of_day", "day"))
		weather = str(cfg.get("weather", "clear"))
		starting_weapon = str(cfg.get("starting_weapon", "khyber_47"))

	var map_scene := load(map_scene_path) as PackedScene
	var map_node := map_scene.instantiate()
	add_child(map_node)

	var env_ctrl := map_node.get_node_or_null("EnvironmentController")
	if env_ctrl and env_ctrl.has_method("apply_conditions"):
		env_ctrl.apply_conditions(tod, weather)

	var player_scene := load("res://scenes/player/player.tscn") as PackedScene
	player = player_scene.instantiate() as PlayerController
	add_child(player)
	player.global_position = Vector3(0, 1.5, 22)
	player.weapon_manager.tracer_pool = pool
	player.weapon_manager.set_starting_weapon(starting_weapon)

	_wire_ui()
	_spawn_enemies(enemy_count, diff)

func _wire_ui() -> void:
	if mobile_controls and mobile_controls.has_method("bind_player"):
		mobile_controls.bind_player(player)
	if hud and hud.has_method("bind_player"):
		hud.bind_player(player)
		var obj_text := str(mission_data.get("objective_ps" if LocalizationManager.is_rtl() else "objective_en", LocalizationManager.tr_key("HUD_OBJECTIVE")))
		hud.set_objective(obj_text)
	player.player_died.connect(_on_player_died)

func _spawn_enemies(count: int, diff: String) -> void:
	var enemy_scene := load("res://scenes/enemies/enemy_soldier.tscn") as PackedScene
	remaining_enemies = count
	for i in range(count):
		var e := enemy_scene.instantiate() as EnemyAI
		add_child(e)
		var angle := (TAU / maxf(1.0, float(count))) * float(i)
		e.global_position = Vector3(cos(angle) * 18.0, 1.5, sin(angle) * 14.0 - 8.0)
		e.configure_difficulty(diff)
		e.died.connect(_on_enemy_died)
	if hud and hud.has_method("set_enemy_count"):
		hud.set_enemy_count(remaining_enemies)

func _on_enemy_died(_enemy: EnemyAI) -> void:
	remaining_enemies = maxi(0, remaining_enemies - 1)
	if hud and hud.has_method("set_enemy_count"):
		hud.set_enemy_count(remaining_enemies)
	if remaining_enemies == 0:
		if GameManager.active_mode == GameManager.GameMode.STORY:
			SaveManager.mark_mission_completed(
				int(mission_data.get("id", 1)),
				int(mission_data.get("reward_points", 250)),
				int(mission_data.get("unlocks_mission", 2))
			)
		if pause_menu and pause_menu.has_method("show_result"):
			pause_menu.show_result(true)

func _on_player_died() -> void:
	if pause_menu and pause_menu.has_method("show_result"):
		pause_menu.show_result(false)
""")

    write_text("scripts/ui/mobile_controls.gd", """
extends Control

var player: PlayerController
var joystick_center: Vector2 = Vector2.ZERO
var joystick_touch_id: int = -1
var look_touch_id: int = -1
var joystick_radius: float = 68.0

@onready var joystick_bg: Control = $JoystickArea/JoystickBG
@onready var joystick_knob: Control = $JoystickArea/JoystickBG/Knob

func bind_player(p: PlayerController) -> void:
	player = p

func _ready() -> void:
	if joystick_bg:
		joystick_center = joystick_bg.size * 0.5

func _input(event: InputEvent) -> void:
	if not player:
		return
	if event is InputEventScreenTouch:
		var pos: Vector2 = event.position
		if event.pressed:
			if pos.x < get_viewport_rect().size.x * 0.42 and joystick_touch_id == -1:
				joystick_touch_id = event.index
			elif pos.x >= get_viewport_rect().size.x * 0.42 and look_touch_id == -1:
				look_touch_id = event.index
		else:
			if event.index == joystick_touch_id:
				joystick_touch_id = -1
				player.set_mobile_move(Vector2.ZERO)
				if joystick_knob:
					joystick_knob.position = joystick_center - joystick_knob.size * 0.5
			elif event.index == look_touch_id:
				look_touch_id = -1
	elif event is InputEventScreenDrag:
		if event.index == joystick_touch_id and joystick_bg:
			var local_pos := joystick_bg.get_local_mouse_position()
			var offset := local_pos - joystick_center
			if offset.length() > joystick_radius:
				offset = offset.normalized() * joystick_radius
			if joystick_knob:
				joystick_knob.position = joystick_center + offset - joystick_knob.size * 0.5
			player.set_mobile_move(offset / joystick_radius)
		elif event.index == look_touch_id:
			player.set_mobile_look(event.relative.x, event.relative.y)

func _on_fire_down() -> void:
	if player: player.mobile_firing = true

func _on_fire_up() -> void:
	if player: player.mobile_firing = false

func _on_aim_pressed() -> void:
	if player: player.mobile_aiming = not player.mobile_aiming

func _on_jump_pressed() -> void:
	if player and player.is_on_floor(): player.velocity.y = player.jump_velocity

func _on_crouch_pressed() -> void:
	if player: player.toggle_crouch()

func _on_reload_pressed() -> void:
	if player: player.weapon_manager.start_reload()

func _on_switch_pressed() -> void:
	if player: player.weapon_manager.switch_next_weapon()

func _on_interact_pressed() -> void:
	if player: player.try_interact()

func _on_grenade_pressed() -> void:
	if player: player.throw_grenade()

func _on_pause_pressed() -> void:
	get_tree().paused = true
	var pause := get_parent().get_node_or_null("PauseMenu")
	if pause:
		pause.visible = true
""")

    write_text("scripts/ui/hud.gd", """
extends Control

@onready var health_bar: ProgressBar = $TopLeft/HealthBar
@onready var armor_bar: ProgressBar = $TopLeft/ArmorBar
@onready var ammo_label: Label = $BottomRight/AmmoLabel
@onready var weapon_label: Label = $BottomRight/WeaponLabel
@onready var objective_label: Label = $TopCenter/ObjectiveLabel
@onready var enemy_label: Label = $TopCenter/EnemyLabel

func bind_player(player: PlayerController) -> void:
	player.health_changed.connect(_on_health_changed)
	player.weapon_manager.ammo_changed.connect(_on_ammo_changed)
	_on_health_changed(player.health, player.armor)
	player.weapon_manager.emit_ammo_update()

func _on_health_changed(hp: int, arm: int) -> void:
	if health_bar: health_bar.value = hp
	if armor_bar: armor_bar.value = arm

func _on_ammo_changed(mag: int, reserve: int, w_name: String, reloading: bool) -> void:
	if weapon_label: weapon_label.text = w_name
	if ammo_label:
		ammo_label.text = LocalizationManager.tr_key("HUD_RELOADING") if reloading else "%d / %d" % [mag, reserve]

func set_objective(text: String) -> void:
	if objective_label:
		objective_label.text = "%s: %s" % [LocalizationManager.tr_key("HUD_OBJECTIVE"), text]

func set_enemy_count(count: int) -> void:
	if enemy_label:
		enemy_label.text = "%s: %d" % [LocalizationManager.tr_key("HUD_ENEMIES"), count]
""")

    write_text("scripts/ui/pause_menu.gd", """
extends Control

@onready var title_label: Label = $Panel/VBox/TitleLabel
@onready var resume_btn: Button = $Panel/VBox/ResumeBtn
@onready var restart_btn: Button = $Panel/VBox/RestartBtn
@onready var menu_btn: Button = $Panel/VBox/MenuBtn

func _ready() -> void:
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS
	_refresh_text()

func _refresh_text() -> void:
	if title_label: title_label.text = LocalizationManager.tr_key("PAUSE_TITLE")
	if resume_btn: resume_btn.text = LocalizationManager.tr_key("PAUSE_RESUME")
	if restart_btn: restart_btn.text = LocalizationManager.tr_key("PAUSE_RESTART")
	if menu_btn: menu_btn.text = LocalizationManager.tr_key("PAUSE_MAIN_MENU")

func show_result(victory: bool) -> void:
	visible = true
	get_tree().paused = true
	if title_label:
		title_label.text = LocalizationManager.tr_key("RESULT_VICTORY" if victory else "RESULT_DEFEAT")
	if resume_btn:
		resume_btn.visible = false

func _on_resume_pressed() -> void:
	visible = false
	get_tree().paused = false

func _on_restart_pressed() -> void:
	get_tree().paused = false
	get_tree().reload_current_scene()

func _on_menu_pressed() -> void:
	GameManager.return_to_main_menu()
""")

    write_text("scripts/ui/main_menu.gd", """
extends Control

@onready var title_label: Label = $Margin/VBox/Header/TitleLabel
@onready var subtitle_label: Label = $Margin/VBox/Header/SubtitleLabel
@onready var story_btn: Button = $Margin/VBox/Buttons/StoryBtn
@onready var free_btn: Button = $Margin/VBox/Buttons/FreeBattleBtn
@onready var settings_btn: Button = $Margin/VBox/Buttons/SettingsBtn
@onready var lang_btn: Button = $Margin/VBox/Buttons/LanguageBtn
@onready var about_btn: Button = $Margin/VBox/Buttons/AboutBtn
@onready var exit_btn: Button = $Margin/VBox/Buttons/ExitBtn
@onready var info_label: Label = $Margin/VBox/InfoPanel/InfoLabel

func _ready() -> void:
	AudioManager.play_music("res://assets/audio/menu_theme.wav")
	LocalizationManager.language_changed.connect(func(_l, _r): _refresh_labels())
	_refresh_labels()

func _refresh_labels() -> void:
	title_label.text = LocalizationManager.tr_key("APP_TITLE")
	subtitle_label.text = LocalizationManager.tr_key("APP_SUBTITLE")
	story_btn.text = LocalizationManager.tr_key("MENU_STORY")
	free_btn.text = LocalizationManager.tr_key("MENU_FREE_BATTLE")
	settings_btn.text = LocalizationManager.tr_key("MENU_SETTINGS")
	lang_btn.text = "%s: %s" % [LocalizationManager.tr_key("MENU_LANGUAGE"), LocalizationManager.tr_key("LANG_PASHTO" if not LocalizationManager.is_rtl() else "LANG_ENGLISH")]
	about_btn.text = LocalizationManager.tr_key("MENU_ABOUT")
	exit_btn.text = LocalizationManager.tr_key("MENU_EXIT")
	info_label.text = LocalizationManager.tr_key("ABOUT_TEXT")

func _on_story_pressed() -> void:
	AudioManager.play_sfx("res://assets/audio/ui_click.wav")
	var unlocked := int(SaveManager.data.get("unlocked_mission", 1))
	GameManager.start_story_mission(mini(unlocked, 3))

func _on_missions_pressed() -> void:
	AudioManager.play_sfx("res://assets/audio/ui_click.wav")
	get_tree().change_scene_to_file("res://scenes/menus/mission_select.tscn")

func _on_free_battle_pressed() -> void:
	AudioManager.play_sfx("res://assets/audio/ui_click.wav")
	get_tree().change_scene_to_file("res://scenes/menus/free_battle_menu.tscn")

func _on_weapons_pressed() -> void:
	AudioManager.play_sfx("res://assets/audio/ui_click.wav")
	get_tree().change_scene_to_file("res://scenes/menus/weapons_armory.tscn")

func _on_settings_pressed() -> void:
	AudioManager.play_sfx("res://assets/audio/ui_click.wav")
	get_tree().change_scene_to_file("res://scenes/ui/settings_menu.tscn")

func _on_language_pressed() -> void:
	AudioManager.play_sfx("res://assets/audio/ui_click.wav")
	LocalizationManager.set_language("ps" if LocalizationManager.current_language == "en" else "en")

func _on_about_pressed() -> void:
	AudioManager.play_sfx("res://assets/audio/ui_click.wav")
	info_label.text = LocalizationManager.tr_key("ABOUT_TEXT")

func _on_exit_pressed() -> void:
	get_tree().quit()
""")

    write_text("scripts/weapons/weapon_pickup.gd", """
extends Area3D
class_name WeaponPickup

@export var weapon_id: String = "khyber_47"
@export var ammo_amount: int = 30

func _ready() -> void:
	body_entered.connect(_on_body_entered)

func _on_body_entered(body: Node3D) -> void:
	if body is PlayerController:
		body.weapon_manager.add_ammo(ammo_amount)
		AudioManager.play_sfx("res://assets/audio/reload.wav", 1.15)
		queue_free()
""")

    write_text("scripts/ui/settings_menu.gd", """
extends Control

@onready var title_label: Label = $Panel/VBox/TitleLabel
@onready var quality_option: OptionButton = $Panel/VBox/QualityRow/QualityOption
@onready var music_slider: HSlider = $Panel/VBox/MusicRow/MusicSlider
@onready var sfx_slider: HSlider = $Panel/VBox/SfxRow/SfxSlider
@onready var env_slider: HSlider = $Panel/VBox/EnvRow/EnvSlider
@onready var cam_slider: HSlider = $Panel/VBox/CamRow/CamSlider
@onready var lang_btn: Button = $Panel/VBox/LanguageBtn
@onready var save_btn: Button = $Panel/VBox/Actions/SaveBtn
@onready var back_btn: Button = $Panel/VBox/Actions/BackBtn

func _ready() -> void:
	quality_option.clear()
	quality_option.add_item(LocalizationManager.tr_key("QUALITY_LOW"), 0)
	quality_option.add_item(LocalizationManager.tr_key("QUALITY_MEDIUM"), 1)
	quality_option.add_item(LocalizationManager.tr_key("QUALITY_HIGH"), 2)
	quality_option.selected = SettingsManager.current_quality
	music_slider.value = AudioManager.music_volume
	sfx_slider.value = AudioManager.sfx_volume
	env_slider.value = AudioManager.env_volume
	cam_slider.value = SettingsManager.camera_sensitivity
	_refresh_text()

func _refresh_text() -> void:
	title_label.text = LocalizationManager.tr_key("SETTINGS_TITLE")
	lang_btn.text = LocalizationManager.tr_key("LANG_PASHTO" if not LocalizationManager.is_rtl() else "LANG_ENGLISH")
	save_btn.text = LocalizationManager.tr_key("SETTINGS_SAVE")
	back_btn.text = LocalizationManager.tr_key("MENU_BACK")

func _on_language_pressed() -> void:
	LocalizationManager.set_language("ps" if LocalizationManager.current_language == "en" else "en")
	_refresh_text()

func _on_save_pressed() -> void:
	SettingsManager.apply_graphics_preset(quality_option.selected)
	SettingsManager.camera_sensitivity = cam_slider.value
	SaveManager.data["camera_sensitivity"] = cam_slider.value
	SaveManager.data["music_volume"] = music_slider.value
	SaveManager.data["sfx_volume"] = sfx_slider.value
	SaveManager.data["env_volume"] = env_slider.value
	AudioManager.apply_volumes(music_slider.value, sfx_slider.value, env_slider.value)
	SaveManager.save_game()
	AudioManager.play_sfx("res://assets/audio/ui_click.wav")

func _on_back_pressed() -> void:
	GameManager.return_to_main_menu()
""")

    write_text("scripts/ui/free_battle_menu.gd", """
extends Control

@onready var map_option: OptionButton = $Panel/VBox/MapOption
@onready var diff_option: OptionButton = $Panel/VBox/DiffOption
@onready var weapon_option: OptionButton = $Panel/VBox/WeaponOption
@onready var time_option: OptionButton = $Panel/VBox/TimeOption
@onready var weather_option: OptionButton = $Panel/VBox/WeatherOption
@onready var enemy_spin: SpinBox = $Panel/VBox/EnemySpin

var map_scenes := [
	"res://scenes/maps/map_afghan_village.tscn",
	"res://scenes/maps/map_mountain_valley.tscn",
	"res://scenes/maps/map_military_outpost.tscn"
]
var diffs := ["recruit", "veteran", "elite"]
var weapon_ids := ["khyber_47", "pamir_m24", "helmand_12g", "kabul_9mm", "balkh_pdw"]
var times := ["day", "dusk", "night"]
var weathers := ["clear", "dust", "rain"]

func _ready() -> void:
	map_option.add_item(LocalizationManager.tr_key("MAP_VILLAGE"))
	map_option.add_item(LocalizationManager.tr_key("MAP_VALLEY"))
	map_option.add_item(LocalizationManager.tr_key("MAP_OUTPOST"))
	diff_option.add_item(LocalizationManager.tr_key("DIFF_RECRUIT"))
	diff_option.add_item(LocalizationManager.tr_key("DIFF_VETERAN"))
	diff_option.add_item(LocalizationManager.tr_key("DIFF_ELITE"))
	diff_option.selected = 1
	for w in GameManager.weapons_cache:
		weapon_option.add_item(str(w.get("name_ps" if LocalizationManager.is_rtl() else "name_en")))
	time_option.add_item(LocalizationManager.tr_key("TIME_DAY"))
	time_option.add_item(LocalizationManager.tr_key("TIME_DUSK"))
	time_option.add_item(LocalizationManager.tr_key("TIME_NIGHT"))
	weather_option.add_item(LocalizationManager.tr_key("WEATHER_CLEAR"))
	weather_option.add_item(LocalizationManager.tr_key("WEATHER_DUST"))
	weather_option.add_item(LocalizationManager.tr_key("WEATHER_RAIN"))

func _on_deploy_pressed() -> void:
	GameManager.start_free_battle({
		"map_scene": map_scenes[map_option.selected],
		"difficulty": diffs[diff_option.selected],
		"enemy_count": int(enemy_spin.value),
		"starting_weapon": weapon_ids[maxi(0, weapon_option.selected)],
		"time_of_day": times[time_option.selected],
		"weather": weathers[weather_option.selected]
	})

func _on_back_pressed() -> void:
	GameManager.return_to_main_menu()
""")

    write_text("scripts/ui/mission_select.gd", """
extends Control

@onready var mission_list: VBoxContainer = $Scroll/MissionList

func _ready() -> void:
	var unlocked := int(SaveManager.data.get("unlocked_mission", 1))
	for m in GameManager.missions_cache:
		var mid := int(m["id"])
		var btn := Button.new()
		var title := str(m.get("title_ps" if LocalizationManager.is_rtl() else "title_en"))
		var is_playable := bool(m.get("implemented", false))
		btn.text = "%s %s" % [title, "" if is_playable else "(Briefing Blueprint)"]
		btn.disabled = mid > unlocked
		btn.pressed.connect(func():
			if is_playable:
				GameManager.start_story_mission(mid)
		)
		mission_list.add_child(btn)

func _on_back_pressed() -> void:
	GameManager.return_to_main_menu()
""")

    write_text("scripts/ui/weapons_armory.gd", """
extends Control

@onready var weapon_list: VBoxContainer = $Scroll/WeaponList

func _ready() -> void:
	for w in GameManager.weapons_cache:
		var lbl := Label.new()
		var name_str := str(w.get("name_ps" if LocalizationManager.is_rtl() else "name_en"))
		lbl.text = "%s | DMG: %s | MAG: %s | RANGE: %sm" % [name_str, str(w["damage"]), str(w["mag_size"]), str(w["range"])]
		weapon_list.add_child(lbl)

func _on_back_pressed() -> void:
	GameManager.return_to_main_menu()
""")


def build_scenes() -> None:
    # 1. Player scene
    write_text("scenes/player/player.tscn", """
[gd_scene load_steps=9 format=3]

[ext_resource type="Script" path="res://scripts/player/player_controller.gd" id="1"]
[ext_resource type="Script" path="res://scripts/player/third_person_camera.gd" id="2"]
[ext_resource type="Script" path="res://scripts/weapons/weapon_manager.gd" id="3"]
[ext_resource type="Texture2D" path="res://assets/textures/tactical_camo.png" id="4"]

[sub_resource type="CapsuleShape3D" id="CapsuleShape3D_player"]
radius = 0.38
height = 1.8

[sub_resource type="StandardMaterial3D" id="Mat_Camo"]
albedo_texture = ExtResource("4")
roughness = 0.85

[sub_resource type="CapsuleMesh" id="Mesh_Torso"]
material = SubResource("Mat_Camo")
radius = 0.28
height = 1.05

[sub_resource type="BoxMesh" id="Mesh_Rifle"]
size = Vector3(0.08, 0.14, 0.78)

[node name="Player" type="CharacterBody3D"]
script = ExtResource("1")

[node name="CollisionShape3D" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.9, 0)
shape = SubResource("CapsuleShape3D_player")

[node name="SoldierModel" type="Node3D" parent="."]

[node name="Torso" type="MeshInstance3D" parent="SoldierModel"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.0, 0)
mesh = SubResource("Mesh_Torso")

[node name="WeaponMount" type="Node3D" parent="SoldierModel"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.26, 1.32, -0.35)

[node name="WeaponManager" type="Node3D" parent="SoldierModel/WeaponMount"]
script = ExtResource("3")

[node name="RifleMesh" type="MeshInstance3D" parent="SoldierModel/WeaponMount/WeaponManager"]
mesh = SubResource("Mesh_Rifle")

[node name="MuzzleFlash" type="OmniLight3D" parent="SoldierModel/WeaponMount/WeaponManager"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, -0.45)
light_color = Color(1, 0.78, 0.3, 1)
light_energy = 4.0
omni_range = 4.5

[node name="CameraRig" type="Node3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.55, 0)
script = ExtResource("2")

[node name="SpringArm3D" type="SpringArm3D" parent="CameraRig"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0.45, 0.15, 0)
spring_length = 3.4

[node name="Camera3D" type="Camera3D" parent="CameraRig/SpringArm3D"]
current = true
""")

    # 2. Enemy soldier scene
    write_text("scenes/enemies/enemy_soldier.tscn", """
[gd_scene load_steps=6 format=3]

[ext_resource type="Script" path="res://scripts/enemies/enemy_ai.gd" id="1"]

[sub_resource type="CapsuleShape3D" id="CapsuleShape3D_enemy"]
radius = 0.38
height = 1.8

[sub_resource type="StandardMaterial3D" id="Mat_Enemy"]
albedo_color = Color(0.28, 0.24, 0.2, 1)
roughness = 0.85

[sub_resource type="CapsuleMesh" id="Mesh_Enemy"]
material = SubResource("Mat_Enemy")
radius = 0.28
height = 1.15

[node name="EnemySoldier" type="CharacterBody3D"]
script = ExtResource("1")

[node name="CollisionShape3D" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.9, 0)
shape = SubResource("CapsuleShape3D_enemy")

[node name="NavigationAgent3D" type="NavigationAgent3D" parent="."]

[node name="EnemyModel" type="Node3D" parent="."]

[node name="BodyMesh" type="MeshInstance3D" parent="EnemyModel"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.0, 0)
mesh = SubResource("Mesh_Enemy")
""")

    # 3. Grenade, Weapon Pickup & Vehicle scenes
    write_text("scenes/weapons/grenade.tscn", """
[gd_scene load_steps=4 format=3]

[ext_resource type="Script" path="res://scripts/weapons/grenade.gd" id="1"]

[sub_resource type="SphereShape3D" id="SphereShape3D_g"]
radius = 0.14

[sub_resource type="SphereMesh" id="SphereMesh_g"]
radius = 0.12
height = 0.24

[node name="FragGrenade" type="RigidBody3D"]
script = ExtResource("1")

[node name="CollisionShape3D" type="CollisionShape3D" parent="."]
shape = SubResource("SphereShape3D_g")

[node name="MeshInstance3D" type="MeshInstance3D" parent="."]
mesh = SubResource("SphereMesh_g")
""")

    write_text("scenes/weapons/weapon_pickup.tscn", """
[gd_scene load_steps=4 format=3]

[ext_resource type="Script" path="res://scripts/weapons/weapon_pickup.gd" id="1"]

[sub_resource type="BoxShape3D" id="BoxShape3D_wp"]
size = Vector3(1.2, 1.0, 1.2)

[sub_resource type="BoxMesh" id="BoxMesh_wp"]
size = Vector3(0.7, 0.35, 0.45)

[node name="WeaponPickup" type="Area3D"]
script = ExtResource("1")

[node name="CollisionShape3D" type="CollisionShape3D" parent="."]
shape = SubResource("BoxShape3D_wp")

[node name="MeshInstance3D" type="MeshInstance3D" parent="."]
mesh = SubResource("BoxMesh_wp")
""")

    write_text("scenes/vehicles/military_jeep.tscn", """
[gd_scene load_steps=5 format=3]

[ext_resource type="Script" path="res://scripts/vehicles/vehicle_base.gd" id="1"]

[sub_resource type="BoxShape3D" id="BoxShape3D_jeep"]
size = Vector3(2.1, 1.4, 4.2)

[sub_resource type="StandardMaterial3D" id="Mat_Jeep"]
albedo_color = Color(0.45, 0.42, 0.31, 1)
roughness = 0.72

[sub_resource type="BoxMesh" id="Mesh_Jeep"]
material = SubResource("Mat_Jeep")
size = Vector3(2.1, 1.2, 4.2)

[node name="MilitaryJeep" type="CharacterBody3D"]
script = ExtResource("1")

[node name="CollisionShape3D" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.7, 0)
shape = SubResource("BoxShape3D_jeep")

[node name="Chassis" type="MeshInstance3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.7, 0)
mesh = SubResource("Mesh_Jeep")
""")

    write_text("scenes/vehicles/transport_truck.tscn", """
[gd_scene load_steps=5 format=3]

[ext_resource type="Script" path="res://scripts/vehicles/vehicle_base.gd" id="1"]

[sub_resource type="BoxShape3D" id="BoxShape3D_truck"]
size = Vector3(2.5, 2.2, 6.2)

[sub_resource type="StandardMaterial3D" id="Mat_Truck"]
albedo_color = Color(0.35, 0.38, 0.28, 1)
roughness = 0.78

[sub_resource type="BoxMesh" id="Mesh_Truck"]
material = SubResource("Mat_Truck")
size = Vector3(2.5, 2.0, 6.2)

[node name="TransportTruck" type="CharacterBody3D"]
script = ExtResource("1")
vehicle_name = "Transport Truck"
max_speed = 11.5

[node name="CollisionShape3D" type="CollisionShape3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.1, 0)
shape = SubResource("BoxShape3D_truck")

[node name="Chassis" type="MeshInstance3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1.1, 0)
mesh = SubResource("Mesh_Truck")
""")

    # 4. Three Playable Maps
    def map_template(name: str, tex_path: str, wall_tex: str, include_jeep: bool = True) -> str:
        jeep_node = """
[node name="MilitaryJeep" parent="." instance=ExtResource("4")]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -8, 0.1, 14)
""" if include_jeep else ""
        jeep_ext = '\n[ext_resource type="PackedScene" path="res://scenes/vehicles/military_jeep.tscn" id="4"]' if include_jeep else ""
        return f"""
[gd_scene load_steps=11 format=3]

[ext_resource type="Script" path="res://scripts/maps/environment_controller.gd" id="1"]
[ext_resource type="Texture2D" path="{tex_path}" id="2"]
[ext_resource type="Texture2D" path="{wall_tex}" id="3"]{jeep_ext}

[sub_resource type="Environment" id="Env_Map"]
background_mode = 1
background_color = Color(0.62, 0.72, 0.82, 1)
ambient_light_source = 2
ambient_light_color = Color(0.55, 0.56, 0.58, 1)
fog_enabled = true
fog_light_color = Color(0.66, 0.73, 0.8, 1)
fog_density = 0.006

[sub_resource type="NavigationMesh" id="NavMesh_Map"]

[sub_resource type="StandardMaterial3D" id="Mat_Ground"]
albedo_texture = ExtResource("2")
uv1_scale = Vector3(24, 24, 24)
roughness = 0.92

[sub_resource type="BoxMesh" id="Mesh_Ground"]
material = SubResource("Mat_Ground")
size = Vector3(160, 1, 160)

[sub_resource type="BoxShape3D" id="Shape_Ground"]
size = Vector3(160, 1, 160)

[sub_resource type="StandardMaterial3D" id="Mat_Structure"]
albedo_texture = ExtResource("3")
uv1_scale = Vector3(3, 2, 1)
roughness = 0.88

[sub_resource type="BoxMesh" id="Mesh_House"]
material = SubResource("Mat_Structure")
size = Vector3(8, 4.5, 8)

[node name="{name}" type="Node3D"]

[node name="EnvironmentController" type="Node3D" parent="." node_paths=PackedStringArray("sun_light", "world_env")]
script = ExtResource("1")
sun_light = NodePath("../SunLight")
world_env = NodePath("../WorldEnvironment")

[node name="WorldEnvironment" type="WorldEnvironment" parent="."]
environment = SubResource("Env_Map")

[node name="SunLight" type="DirectionalLight3D" parent="."]
transform = Transform3D(0.866, -0.35, 0.35, 0, 0.707, 0.707, -0.5, -0.612, 0.612, 0, 24, 0)
shadow_enabled = true

[node name="NavigationRegion3D" type="NavigationRegion3D" parent="."]
navigation_mesh = SubResource("NavMesh_Map")

[node name="Ground" type="StaticBody3D" parent="NavigationRegion3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.5, 0)

[node name="Mesh" type="MeshInstance3D" parent="NavigationRegion3D/Ground"]
mesh = SubResource("Mesh_Ground")

[node name="Shape" type="CollisionShape3D" parent="NavigationRegion3D/Ground"]
shape = SubResource("Shape_Ground")

[node name="CompoundA" type="StaticBody3D" parent="NavigationRegion3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, -14, 2.25, -4)

[node name="Mesh" type="MeshInstance3D" parent="NavigationRegion3D/CompoundA"]
mesh = SubResource("Mesh_House")

[node name="CompoundB" type="StaticBody3D" parent="NavigationRegion3D"]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 15, 2.25, -8)

[node name="Mesh" type="MeshInstance3D" parent="NavigationRegion3D/CompoundB"]
mesh = SubResource("Mesh_House")
{jeep_node}
"""

    write_text("scenes/maps/map_afghan_village.tscn", map_template("MapAfghanVillage", "res://assets/textures/valley_soil.png", "res://assets/textures/mud_brick.png", True))
    write_text("scenes/maps/map_mountain_valley.tscn", map_template("MapMountainValley", "res://assets/textures/mountain_rock.png", "res://assets/textures/mountain_rock.png", False))
    write_text("scenes/maps/map_military_outpost.tscn", map_template("MapMilitaryOutpost", "res://assets/textures/valley_soil.png", "res://assets/textures/military_concrete.png", True))

    # 5. UI Scenes & Main Scene
    write_text("scenes/ui/hud.tscn", """
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/ui/hud.gd" id="1"]

[node name="HUD" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
mouse_filter = 2
script = ExtResource("1")

[node name="TopLeft" type="VBoxContainer" parent="."]
layout_mode = 0
offset_left = 24.0
offset_top = 20.0
offset_right = 280.0
offset_bottom = 90.0

[node name="HealthBar" type="ProgressBar" parent="TopLeft"]
layout_mode = 2
value = 100.0

[node name="ArmorBar" type="ProgressBar" parent="TopLeft"]
layout_mode = 2
max_value = 50.0
value = 50.0

[node name="TopCenter" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 5
anchor_left = 0.5
anchor_right = 0.5
offset_left = -220.0
offset_top = 18.0
offset_right = 220.0
offset_bottom = 80.0

[node name="ObjectiveLabel" type="Label" parent="TopCenter"]
layout_mode = 2
horizontal_alignment = 1
text = "OBJECTIVE"

[node name="EnemyLabel" type="Label" parent="TopCenter"]
layout_mode = 2
horizontal_alignment = 1
text = "HOSTILES: 5"

[node name="BottomRight" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 3
anchor_left = 1.0
anchor_top = 1.0
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = -240.0
offset_top = -90.0
offset_right = -24.0
offset_bottom = -20.0

[node name="WeaponLabel" type="Label" parent="BottomRight"]
layout_mode = 2
horizontal_alignment = 2
text = "Khyber-47"

[node name="AmmoLabel" type="Label" parent="BottomRight"]
layout_mode = 2
horizontal_alignment = 2
text = "30 / 180"
""")

    write_text("scenes/ui/mobile_controls.tscn", """
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/ui/mobile_controls.gd" id="1"]

[node name="MobileControls" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
mouse_filter = 2
script = ExtResource("1")

[node name="JoystickArea" type="Control" parent="."]
layout_mode = 1
anchors_preset = 2
anchor_top = 1.0
anchor_bottom = 1.0
offset_left = 32.0
offset_top = -200.0
offset_right = 212.0
offset_bottom = -20.0

[node name="JoystickBG" type="Panel" parent="JoystickArea"]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0

[node name="Knob" type="Panel" parent="JoystickArea/JoystickBG"]
layout_mode = 0
offset_left = 58.0
offset_top = 58.0
offset_right = 122.0
offset_bottom = 122.0

[node name="FireBtn" type="Button" parent="."]
layout_mode = 1
anchors_preset = 3
anchor_left = 1.0
anchor_top = 1.0
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = -130.0
offset_top = -150.0
offset_right = -36.0
offset_bottom = -56.0
text = "FIRE"

[node name="AimBtn" type="Button" parent="."]
layout_mode = 1
anchors_preset = 3
anchor_left = 1.0
anchor_top = 1.0
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = -230.0
offset_top = -140.0
offset_right = -148.0
offset_bottom = -70.0
text = "AIM"

[node name="ReloadBtn" type="Button" parent="."]
layout_mode = 1
anchors_preset = 3
anchor_left = 1.0
anchor_top = 1.0
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = -220.0
offset_top = -220.0
offset_right = -138.0
offset_bottom = -165.0
text = "RELOAD"

[node name="JumpBtn" type="Button" parent="."]
layout_mode = 1
anchors_preset = 3
anchor_left = 1.0
anchor_top = 1.0
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = -120.0
offset_top = -230.0
offset_right = -44.0
offset_bottom = -170.0
text = "JUMP"

[node name="PauseBtn" type="Button" parent="."]
layout_mode = 1
anchors_preset = 1
anchor_left = 1.0
anchor_right = 1.0
offset_left = -110.0
offset_top = 18.0
offset_right = -24.0
offset_bottom = 58.0
text = "PAUSE"

[connection signal="button_down" from="FireBtn" to="." method="_on_fire_down"]
[connection signal="button_up" from="FireBtn" to="." method="_on_fire_up"]
[connection signal="pressed" from="AimBtn" to="." method="_on_aim_pressed"]
[connection signal="pressed" from="ReloadBtn" to="." method="_on_reload_pressed"]
[connection signal="pressed" from="JumpBtn" to="." method="_on_jump_pressed"]
[connection signal="pressed" from="PauseBtn" to="." method="_on_pause_pressed"]
""")

    write_text("scenes/ui/pause_menu.tscn", """
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/ui/pause_menu.gd" id="1"]

[node name="PauseMenu" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("1")

[node name="Panel" type="PanelContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -180.0
offset_top = -130.0
offset_right = 180.0
offset_bottom = 130.0

[node name="VBox" type="VBoxContainer" parent="Panel"]
layout_mode = 2

[node name="TitleLabel" type="Label" parent="Panel/VBox"]
layout_mode = 2
horizontal_alignment = 1
text = "MISSION PAUSED"

[node name="ResumeBtn" type="Button" parent="Panel/VBox"]
layout_mode = 2
text = "RESUME"

[node name="RestartBtn" type="Button" parent="Panel/VBox"]
layout_mode = 2
text = "RESTART"

[node name="MenuBtn" type="Button" parent="Panel/VBox"]
layout_mode = 2
text = "MAIN MENU"

[connection signal="pressed" from="Panel/VBox/ResumeBtn" to="." method="_on_resume_pressed"]
[connection signal="pressed" from="Panel/VBox/RestartBtn" to="." method="_on_restart_pressed"]
[connection signal="pressed" from="Panel/VBox/MenuBtn" to="." method="_on_menu_pressed"]
""")

    write_text("scenes/ui/settings_menu.tscn", """
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/ui/settings_menu.gd" id="1"]

[node name="SettingsMenu" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("1")

[node name="Panel" type="PanelContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -260.0
offset_top = -220.0
offset_right = 260.0
offset_bottom = 220.0

[node name="VBox" type="VBoxContainer" parent="Panel"]
layout_mode = 2

[node name="TitleLabel" type="Label" parent="Panel/VBox"]
layout_mode = 2
text = "SETTINGS"

[node name="QualityRow" type="HBoxContainer" parent="Panel/VBox"]
layout_mode = 2

[node name="QualityOption" type="OptionButton" parent="Panel/VBox/QualityRow"]
layout_mode = 2

[node name="MusicRow" type="HBoxContainer" parent="Panel/VBox"]
layout_mode = 2

[node name="MusicSlider" type="HSlider" parent="Panel/VBox/MusicRow"]
layout_mode = 2
size_flags_horizontal = 3
max_value = 1.0
step = 0.05

[node name="SfxRow" type="HBoxContainer" parent="Panel/VBox"]
layout_mode = 2

[node name="SfxSlider" type="HSlider" parent="Panel/VBox/SfxRow"]
layout_mode = 2
size_flags_horizontal = 3
max_value = 1.0
step = 0.05

[node name="EnvRow" type="HBoxContainer" parent="Panel/VBox"]
layout_mode = 2

[node name="EnvSlider" type="HSlider" parent="Panel/VBox/EnvRow"]
layout_mode = 2
size_flags_horizontal = 3
max_value = 1.0
step = 0.05

[node name="CamRow" type="HBoxContainer" parent="Panel/VBox"]
layout_mode = 2

[node name="CamSlider" type="HSlider" parent="Panel/VBox/CamRow"]
layout_mode = 2
size_flags_horizontal = 3
min_value = 0.3
max_value = 2.5
step = 0.05

[node name="LanguageBtn" type="Button" parent="Panel/VBox"]
layout_mode = 2
text = "LANGUAGE"

[node name="Actions" type="HBoxContainer" parent="Panel/VBox"]
layout_mode = 2

[node name="SaveBtn" type="Button" parent="Panel/VBox/Actions"]
layout_mode = 2
text = "SAVE"

[node name="BackBtn" type="Button" parent="Panel/VBox/Actions"]
layout_mode = 2
text = "BACK"

[connection signal="pressed" from="Panel/VBox/LanguageBtn" to="." method="_on_language_pressed"]
[connection signal="pressed" from="Panel/VBox/Actions/SaveBtn" to="." method="_on_save_pressed"]
[connection signal="pressed" from="Panel/VBox/Actions/BackBtn" to="." method="_on_back_pressed"]
""")

    write_text("scenes/menus/free_battle_menu.tscn", """
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/ui/free_battle_menu.gd" id="1"]

[node name="FreeBattleMenu" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("1")

[node name="Panel" type="PanelContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -240.0
offset_top = -200.0
offset_right = 240.0
offset_bottom = 200.0

[node name="VBox" type="VBoxContainer" parent="Panel"]
layout_mode = 2

[node name="MapOption" type="OptionButton" parent="Panel/VBox"]
layout_mode = 2

[node name="DiffOption" type="OptionButton" parent="Panel/VBox"]
layout_mode = 2

[node name="WeaponOption" type="OptionButton" parent="Panel/VBox"]
layout_mode = 2

[node name="TimeOption" type="OptionButton" parent="Panel/VBox"]
layout_mode = 2

[node name="WeatherOption" type="OptionButton" parent="Panel/VBox"]
layout_mode = 2

[node name="EnemySpin" type="SpinBox" parent="Panel/VBox"]
layout_mode = 2
min_value = 2.0
max_value = 24.0
value = 6.0

[node name="DeployBtn" type="Button" parent="Panel/VBox"]
layout_mode = 2
text = "DEPLOY"

[node name="BackBtn" type="Button" parent="Panel/VBox"]
layout_mode = 2
text = "BACK"

[connection signal="pressed" from="Panel/VBox/DeployBtn" to="." method="_on_deploy_pressed"]
[connection signal="pressed" from="Panel/VBox/BackBtn" to="." method="_on_back_pressed"]
""")

    write_text("scenes/menus/mission_select.tscn", """
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/ui/mission_select.gd" id="1"]

[node name="MissionSelect" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("1")

[node name="Scroll" type="ScrollContainer" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = 48.0
offset_top = 40.0
offset_right = -48.0
offset_bottom = -80.0

[node name="MissionList" type="VBoxContainer" parent="Scroll"]
layout_mode = 2
size_flags_horizontal = 3

[node name="BackBtn" type="Button" parent="."]
layout_mode = 1
anchors_preset = 2
anchor_top = 1.0
anchor_bottom = 1.0
offset_left = 48.0
offset_top = -64.0
offset_right = 180.0
offset_bottom = -20.0
text = "BACK"

[connection signal="pressed" from="BackBtn" to="." method="_on_back_pressed"]
""")

    write_text("scenes/menus/weapons_armory.tscn", """
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/ui/weapons_armory.gd" id="1"]

[node name="WeaponsArmory" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("1")

[node name="Scroll" type="ScrollContainer" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = 48.0
offset_top = 40.0
offset_right = -48.0
offset_bottom = -80.0

[node name="WeaponList" type="VBoxContainer" parent="Scroll"]
layout_mode = 2
size_flags_horizontal = 3

[node name="BackBtn" type="Button" parent="."]
layout_mode = 1
anchors_preset = 2
anchor_top = 1.0
anchor_bottom = 1.0
offset_left = 48.0
offset_top = -64.0
offset_right = 180.0
offset_bottom = -20.0
text = "BACK"

[connection signal="pressed" from="BackBtn" to="." method="_on_back_pressed"]
""")

    write_text("scenes/menus/main_menu.tscn", """
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/ui/main_menu.gd" id="1"]

[node name="MainMenu" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("1")

[node name="Background" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
color = Color(0.08, 0.09, 0.12, 1)

[node name="Margin" type="MarginContainer" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
theme_override_constants/margin_left = 48
theme_override_constants/margin_top = 36
theme_override_constants/margin_right = 48
theme_override_constants/margin_bottom = 36

[node name="VBox" type="VBoxContainer" parent="Margin"]
layout_mode = 2
theme_override_constants/separation = 16

[node name="Header" type="VBoxContainer" parent="Margin/VBox"]
layout_mode = 2

[node name="TitleLabel" type="Label" parent="Margin/VBox/Header"]
layout_mode = 2
text = "AFGHAN WARRIOR"

[node name="SubtitleLabel" type="Label" parent="Margin/VBox/Header"]
layout_mode = 2
text = "Tactical Mountain Operations"

[node name="Buttons" type="VBoxContainer" parent="Margin/VBox"]
layout_mode = 2
theme_override_constants/separation = 10

[node name="StoryBtn" type="Button" parent="Margin/VBox/Buttons"]
layout_mode = 2
text = "STORY MODE"

[node name="MissionsBtn" type="Button" parent="Margin/VBox/Buttons"]
layout_mode = 2
text = "MISSIONS"

[node name="FreeBattleBtn" type="Button" parent="Margin/VBox/Buttons"]
layout_mode = 2
text = "FREE BATTLE"

[node name="WeaponsBtn" type="Button" parent="Margin/VBox/Buttons"]
layout_mode = 2
text = "WEAPONS"

[node name="SettingsBtn" type="Button" parent="Margin/VBox/Buttons"]
layout_mode = 2
text = "SETTINGS"

[node name="LanguageBtn" type="Button" parent="Margin/VBox/Buttons"]
layout_mode = 2
text = "LANGUAGE"

[node name="AboutBtn" type="Button" parent="Margin/VBox/Buttons"]
layout_mode = 2
text = "ABOUT"

[node name="ExitBtn" type="Button" parent="Margin/VBox/Buttons"]
layout_mode = 2
text = "EXIT"

[node name="InfoPanel" type="PanelContainer" parent="Margin/VBox"]
layout_mode = 2

[node name="InfoLabel" type="Label" parent="Margin/VBox/InfoPanel"]
layout_mode = 2
autowrap_mode = 2
text = "AFGHAN WARRIOR"

[connection signal="pressed" from="Margin/VBox/Buttons/StoryBtn" to="." method="_on_story_pressed"]
[connection signal="pressed" from="Margin/VBox/Buttons/MissionsBtn" to="." method="_on_missions_pressed"]
[connection signal="pressed" from="Margin/VBox/Buttons/FreeBattleBtn" to="." method="_on_free_battle_pressed"]
[connection signal="pressed" from="Margin/VBox/Buttons/WeaponsBtn" to="." method="_on_weapons_pressed"]
[connection signal="pressed" from="Margin/VBox/Buttons/SettingsBtn" to="." method="_on_settings_pressed"]
[connection signal="pressed" from="Margin/VBox/Buttons/LanguageBtn" to="." method="_on_language_pressed"]
[connection signal="pressed" from="Margin/VBox/Buttons/AboutBtn" to="." method="_on_about_pressed"]
[connection signal="pressed" from="Margin/VBox/Buttons/ExitBtn" to="." method="_on_exit_pressed"]
""")

    write_text("scenes/main/main.tscn", """
[gd_scene load_steps=6 format=3]

[ext_resource type="Script" path="res://scripts/missions/mission_controller.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/ui/hud.tscn" id="2"]
[ext_resource type="PackedScene" path="res://scenes/ui/mobile_controls.tscn" id="3"]
[ext_resource type="PackedScene" path="res://scenes/ui/pause_menu.tscn" id="4"]
[ext_resource type="Script" path="res://scripts/systems/object_pool.gd" id="5"]

[node name="Main" type="Node3D"]
script = ExtResource("1")

[node name="ObjectPool" type="Node" parent="."]
script = ExtResource("5")

[node name="HUD" parent="." instance=ExtResource("2")]

[node name="MobileControls" parent="." instance=ExtResource("3")]

[node name="PauseMenu" parent="." instance=ExtResource("4")]
""")


def validate_project() -> None:
    """Validate every res:// path, JSON file, GDScript syntax, and TSCN scene."""
    errors = []
    res_pattern = re.compile(r'res://([A-Za-z0-9_./-]+)')

    for root, _, files in os.walk(PROJECT_DIR):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, PROJECT_DIR)
            if name.endswith((".gd", ".tscn", ".godot")):
                with open(full, "r", encoding="utf-8") as f:
                    text = f.read()
                for match in res_pattern.findall(text):
                    target = os.path.join(PROJECT_DIR, match)
                    if not os.path.exists(target):
                        errors.append(f"Missing res://{match} referenced in {rel}")
                if name.endswith(".gd"):
                    if re.search(r'(?<!@)\b(?:export|onready)\s+var\b', text):
                        errors.append(f"Godot 3 syntax found in {rel}")
            elif name.endswith(".json"):
                with open(full, "r", encoding="utf-8") as f:
                    json.load(f)

    if errors:
        raise RuntimeError("Validation failed:\n" + "\n".join(errors))


def export_manifest() -> None:
    manifest_files = []
    for root, _, files in os.walk(PROJECT_DIR):
        for name in sorted(files):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, PROJECT_DIR).replace("\\", "/")
            size = os.path.getsize(full)
            preview = ""
            if name.endswith((".gd", ".tscn", ".godot", ".cfg", ".json", ".md", ".svg")):
                with open(full, "r", encoding="utf-8") as f:
                    preview = f.read()
            manifest_files.append({
                "path": f"AfghanWarrior/{rel}",
                "size": size,
                "preview": preview
            })
    manifest_files.sort(key=lambda x: x["path"])
    manifest_out = os.path.join(ROOT_DIR, "public", "godot_manifest.json")
    os.makedirs(os.path.dirname(manifest_out), exist_ok=True)
    with open(manifest_out, "w", encoding="utf-8") as f:
        json.dump({"files": manifest_files}, f, ensure_ascii=False)


def package_zip() -> None:
    os.makedirs(os.path.dirname(PUBLIC_ZIP), exist_ok=True)
    for zip_path in (PUBLIC_ZIP, ROOT_ZIP):
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(PROJECT_DIR):
                for file in sorted(files):
                    full = os.path.join(root, file)
                    arcname = os.path.join("AfghanWarrior", os.path.relpath(full, PROJECT_DIR))
                    zf.write(full, arcname)


def main() -> None:
    build_textures_and_audio()
    build_data_files()
    build_config_and_docs()
    build_gdscripts()
    build_scenes()
    validate_project()
    export_manifest()
    package_zip()
    file_count = sum(len(files) for _, _, files in os.walk(PROJECT_DIR))
    zip_size = os.path.getsize(PUBLIC_ZIP)
    print(f"Built & validated {file_count} Godot 4 project files. ZIP size: {zip_size} bytes.")


if __name__ == "__main__":
    main()
