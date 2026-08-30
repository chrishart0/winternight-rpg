from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import urllib.request
from pathlib import Path

import yaml
from PIL import Image

from .build_report import sha256, tree_hash

WEB_ADAPTER_VERSION = "1.1"
RUNTIME_DIRECTORIES = ("data", "engine", "events", "utilities")
BROWSERFS_URL = "https://pygame-web.github.io/archives/0.9/browserfs.min.js"
BROWSERFS_SHA256 = "ba01fda78db31a7ba579afe74b8b56cf4636381ca1b6c54ffba20467756a627f"
BROKEN_BROWSERFS_SCRIPT = (
    '<script src="https://pygame-web.github.io/cdn/0.9.3//browserfs.min.js"></script>'
)
LOCAL_BROWSERFS_SCRIPT = '<script src="browserfs.min.js"></script>'
DEBUG_TERMINAL_CONFIG = 'data-os="vtx,snd,gui"'
PRODUCTION_TERMINAL_CONFIG = 'data-os="snd,gui"'
PWA_HEAD = """    <meta id="winternight-viewport" name="viewport"
          content="width=device-width, height=device-height, initial-scale=1,
                   viewport-fit=cover, interactive-widget=resizes-content">
    <meta id="winternight-theme" name="theme-color" content="#10151b">
    <meta id="winternight-mobile-capable" name="mobile-web-app-capable" content="yes">
    <meta id="winternight-apple-capable" name="apple-mobile-web-app-capable" content="yes">
    <meta id="winternight-apple-status" name="apple-mobile-web-app-status-bar-style"
          content="black-translucent">
    <link id="winternight-manifest" rel="manifest" href="manifest.webmanifest">
    <link id="winternight-apple-icon" rel="apple-touch-icon" href="pwa-icon-192.png">
"""
PWA_MANIFEST = {
    "name": "Eye of the World",
    "short_name": "Eye of the World",
    "description": "A six-chapter tactical RPG vertical slice.",
    "start_url": "./index.html",
    "scope": "./",
    "display": "fullscreen",
    "display_override": ["fullscreen", "standalone"],
    "orientation": "any",
    "background_color": "#03070c",
    "theme_color": "#10151b",
    "icons": [
        {"src": "pwa-icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "pwa-icon-512.png", "sizes": "512x512", "type": "image/png"},
    ],
}
PWA_CACHE_NAME = f"winternight-pwa-v{WEB_ADAPTER_VERSION}"
PWA_SERVICE_WORKER = (
    f'const CACHE_NAME = "{PWA_CACHE_NAME}";\n'
    """const CORE_FILES = [
    "./index.html",
    "./manifest.webmanifest",
    "./favicon.png",
    "./pwa-icon-192.png",
    "./pwa-icon-512.png",
    "./browserfs.min.js",
    "./cutscene-wide/manifest.json",
    "./winternight-splash.png",
    "./web-app.tar.gz",
    "./web-app.apk",
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(CORE_FILES))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys()
            .then((names) => Promise.all(
                names.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", (event) => {
    if (event.request.method !== "GET" ||
            new URL(event.request.url).origin !== self.location.origin) return;
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                if (response.ok) {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
                }
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});
"""
)
WEB_SHELL_STYLE = """    <style id="winternight-web-shell">
        :root {
            --winternight-game-width: 480px;
            --winternight-game-height: 320px;
            --winternight-sp-scale: 1;
            --winternight-cutscene-width: 480px;
            --winternight-cutscene-height: 320px;
            --sp-alloy-light: #b9bac0;
            --sp-alloy: #8e9099;
            --sp-alloy-shadow: #555862;
            --sp-bezel: #10151b;
            --sp-control: #58486b;
            --sp-control-shadow: #30283c;
            --sp-power: #d7df65;
            color-scheme: dark;
        }
        html, body {
            width: 100%;
            height: 100%;
            overflow: hidden;
        }
        body {
            background:
                radial-gradient(circle at 50% 44%, #213047 0%, #0b1421 44%, #03070c 100%)
                !important;
            font-family: "Arial Narrow", "Trebuchet MS", sans-serif;
        }
        #winternight-sp {
            width: 620px;
            height: 798px;
            position: fixed;
            left: 50%;
            top: 50%;
            z-index: 4;
            transform: translate(-50%, -50%) scale(var(--winternight-sp-scale));
            transform-origin: center;
            filter: drop-shadow(0 34px 38px rgba(0, 0, 0, 0.62));
            user-select: none;
            -webkit-user-select: none;
            touch-action: none;
        }
        .sp-lid,
        .sp-controls {
            box-sizing: border-box;
            width: 620px;
            position: relative;
            background:
                linear-gradient(115deg, rgba(255, 255, 255, 0.2), transparent 24%),
                linear-gradient(
                    160deg,
                    var(--sp-alloy-light),
                    var(--sp-alloy) 54%,
                    var(--sp-alloy-shadow)
                );
            border: 2px solid #4b4e57;
            box-shadow:
                inset 0 2px 1px rgba(255, 255, 255, 0.55),
                inset 0 -5px 8px rgba(40, 42, 50, 0.38);
        }
        .sp-lid {
            height: 440px;
            border-radius: 30px 30px 14px 14px;
        }
        .sp-lid::before,
        .sp-controls::before {
            content: "";
            position: absolute;
            inset: 8px;
            border: 1px solid rgba(50, 53, 62, 0.38);
            border-radius: inherit;
            pointer-events: none;
        }
        .sp-screen-frame {
            box-sizing: border-box;
            width: 536px;
            height: 390px;
            position: absolute;
            left: 40px;
            top: 23px;
            padding: 20px 26px 48px;
            background:
                linear-gradient(145deg, #26303b, var(--sp-bezel) 38%, #080b0f);
            border: 2px solid #424b56;
            border-radius: 18px 18px 36px 36px;
            box-shadow:
                inset 0 0 0 3px rgba(0, 0, 0, 0.7),
                0 3px 2px rgba(255, 255, 255, 0.35);
        }
        .sp-screen-glass {
            width: 480px;
            height: 320px;
            position: relative;
            overflow: hidden;
            background: #020508;
            border: 2px solid #05070a;
            box-shadow:
                0 0 0 2px #65717c,
                inset 0 0 20px rgba(91, 132, 159, 0.18);
        }
        .sp-cutscene-backdrop {
            display: none;
            pointer-events: none;
        }
        .sp-screen-glass::after {
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            background: linear-gradient(118deg, rgba(255, 255, 255, 0.075), transparent 22%);
            z-index: 6;
        }
        #transfer,
        #infobox {
            display: none !important;
        }
        .sp-loading-splash {
            position: absolute;
            inset: 0;
            z-index: 0;
            display: grid;
            place-content: center;
            justify-items: center;
            gap: 12px;
            overflow: hidden;
            background:
                radial-gradient(circle at 50% 42%, #17243a 0 20%, #080f1c 48%, #020508 78%);
            pointer-events: none;
        }
        .sp-loading-mark {
            width: 154px;
            height: 154px;
            object-fit: contain;
            image-rendering: pixelated;
            filter: drop-shadow(0 8px 12px rgba(0, 0, 0, 0.72));
        }
        .sp-loading-title {
            color: #e2b14e;
            font: 700 18px/1 "Arial Narrow", "Trebuchet MS", sans-serif;
            letter-spacing: 0.28em;
            text-indent: 0.28em;
            text-shadow: 0 2px #06080c;
        }
        .sp-loading-status {
            color: #91a3b9;
            font: 700 9px/1 ui-monospace, monospace;
            letter-spacing: 0.18em;
            text-indent: 0.18em;
            text-transform: uppercase;
        }
        .sp-screen-label {
            position: absolute;
            left: 0;
            right: 0;
            bottom: 12px;
            color: #abb3ba;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.22em;
            text-align: center;
            text-transform: uppercase;
            text-shadow: 0 1px #000;
        }
        .sp-screen-label span {
            color: #738291;
            font-size: 9px;
            letter-spacing: 0.12em;
        }
        .sp-touch-label {
            display: none;
        }
        .sp-hinge {
            box-sizing: border-box;
            width: 570px;
            height: 38px;
            margin: -2px auto;
            position: relative;
            z-index: 2;
            background:
                linear-gradient(
                    180deg,
                    #4c4f59 0 12%,
                    #a5a7ae 16% 42%,
                    #5b5e68 48% 66%,
                    #aeb0b6 71% 86%,
                    #4b4e58 92%
                );
            border: 2px solid #454851;
            border-radius: 19px;
            box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.13);
        }
        .sp-hinge::before,
        .sp-hinge::after {
            content: "";
            width: 74px;
            height: 42px;
            position: absolute;
            top: -4px;
            background: linear-gradient(180deg, #b9bbc0, #60636d);
            border: 2px solid #444750;
            border-radius: 19px;
        }
        .sp-hinge::before { left: -16px; }
        .sp-hinge::after { right: -16px; }
        .sp-controls {
            height: 324px;
            border-radius: 14px 14px 38px 38px;
        }
        .sp-controls::after {
            content: "EYE OF THE WORLD  /  FIELD UNIT 01";
            position: absolute;
            left: 0;
            right: 0;
            bottom: 23px;
            color: rgba(57, 59, 69, 0.78);
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.19em;
            text-align: center;
            text-shadow: 0 1px rgba(255, 255, 255, 0.32);
        }
        .sp-dpad {
            width: 154px;
            height: 154px;
            position: absolute;
            left: 66px;
            top: 58px;
            filter: drop-shadow(0 7px 2px rgba(47, 42, 54, 0.42));
        }
        .sp-dpad::before,
        .sp-dpad::after {
            content: "";
            position: absolute;
            background: linear-gradient(
                145deg,
                #6b587e,
                var(--sp-control) 46%,
                var(--sp-control-shadow)
            );
            border: 2px solid #352b40;
            border-radius: 9px;
            box-shadow: inset 2px 2px 2px rgba(255, 255, 255, 0.16);
        }
        .sp-dpad::before { left: 0; top: 50px; width: 150px; height: 50px; }
        .sp-dpad::after { left: 50px; top: 0; width: 50px; height: 150px; }
        .sp-dpad-center {
            width: 48px;
            height: 48px;
            position: absolute;
            left: 52px;
            top: 52px;
            z-index: 2;
            border-radius: 50%;
            background: radial-gradient(circle, #372e43 0 24%, #4e405f 27% 54%, #312839 58%);
            pointer-events: none;
        }
        .sp-key {
            position: absolute;
            z-index: 3;
            border: 0;
            background: transparent;
            color: rgba(224, 220, 230, 0.72);
            font: 700 17px/1 sans-serif;
            cursor: pointer;
            -webkit-tap-highlight-color: transparent;
        }
        .sp-key-up { width: 50px; height: 50px; left: 52px; top: 1px; }
        .sp-key-down { width: 50px; height: 50px; left: 52px; bottom: 1px; }
        .sp-key-left { width: 50px; height: 50px; left: 1px; top: 52px; }
        .sp-key-right { width: 50px; height: 50px; right: 1px; top: 52px; }
        .sp-key:active,
        .sp-key.is-pressed { transform: translateY(2px); color: #fff; }
        .sp-actions {
            width: 210px;
            height: 140px;
            position: absolute;
            right: 46px;
            top: 54px;
            transform: rotate(-12deg);
        }
        .sp-action {
            width: 76px;
            height: 76px;
            position: absolute;
            border: 2px solid #342a3e;
            border-radius: 50%;
            background:
                radial-gradient(circle at 34% 28%, #79668c, var(--sp-control) 46%, #33293e 76%);
            box-shadow:
                0 7px 2px rgba(47, 42, 54, 0.42),
                inset 2px 2px 3px rgba(255, 255, 255, 0.22);
            color: #d8cfdf;
            font: italic 800 25px/1 "Trebuchet MS", sans-serif;
            cursor: pointer;
            -webkit-tap-highlight-color: transparent;
        }
        .sp-action-b { left: 12px; top: 55px; }
        .sp-action-a { right: 12px; top: 4px; }
        .sp-action:active,
        .sp-action.is-pressed {
            transform: translateY(3px);
            box-shadow: 0 3px 1px rgba(47, 42, 54, 0.5), inset 2px 2px 4px #2f2638;
        }
        .sp-system-buttons {
            position: absolute;
            left: 239px;
            top: 207px;
            display: flex;
            gap: 12px;
        }
        .sp-system-button {
            width: 62px;
            height: 18px;
            border: 1px solid #41434d;
            border-radius: 10px;
            background: linear-gradient(180deg, #70727b, #4b4e57);
            box-shadow: 0 3px 1px rgba(45, 47, 55, 0.45), inset 0 1px rgba(255, 255, 255, 0.24);
            color: #30323a;
            font: 700 8px/1 sans-serif;
            letter-spacing: 0.08em;
            cursor: pointer;
        }
        .sp-system-button:active,
        .sp-system-button.is-pressed { transform: translateY(2px); }
        .sp-speaker {
            width: 93px;
            height: 62px;
            position: absolute;
            right: 78px;
            bottom: 48px;
            display: grid;
            grid-template-columns: repeat(5, 8px);
            grid-auto-rows: 8px;
            gap: 7px 10px;
            transform: rotate(-12deg);
        }
        .sp-speaker i {
            width: 7px;
            height: 7px;
            display: block;
            border-radius: 50%;
            background: #4b4e57;
            box-shadow: inset 1px 1px 2px #24262c, 0 1px rgba(255, 255, 255, 0.2);
        }
        .sp-power {
            position: absolute;
            left: 36px;
            bottom: 31px;
            color: #555862;
            font-size: 8px;
            font-weight: 700;
            letter-spacing: 0.12em;
        }
        .sp-power::before {
            content: "";
            width: 7px;
            height: 7px;
            display: inline-block;
            margin-right: 7px;
            border-radius: 50%;
            background: var(--sp-power);
            box-shadow: 0 0 8px rgba(215, 223, 101, 0.82);
        }
        .sp-help {
            position: fixed;
            left: 50%;
            bottom: 12px;
            z-index: 3;
            transform: translateX(-50%);
            color: #718095;
            font-size: 10px;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .sp-help kbd {
            margin: 0 2px;
            padding: 3px 6px;
            border: 1px solid #4f5f73;
            border-radius: 4px;
            background: #101923;
            box-shadow: 0 2px 0 #02060b;
            color: #c9d2dc;
            font: inherit;
            letter-spacing: 0.05em;
        }
        canvas#canvas.emscripten {
            width: 480px !important;
            height: 320px !important;
            max-width: none !important;
            max-height: none !important;
            position: relative !important;
            display: block !important;
            margin: 0 !important;
            /* Pygbag's backing canvas is already 480x320. Keep its desktop CSS
               size at that native resolution so the browser never enlarges the
               engine's deliberately low-resolution art a second time. */
            image-rendering: auto;
            outline: 0;
            box-shadow: none;
            touch-action: none;
        }
        canvas#canvas.emscripten:focus-visible {
            outline: 2px solid #d8b86f;
            outline-offset: -2px;
        }
        @media (pointer: coarse), (max-width: 680px), (max-height: 600px) {
            body {
                min-height: 100dvh;
                overscroll-behavior: none;
            }
            #winternight-sp {
                width: 100%;
                height: 100dvh;
                inset: 0;
                display: flex;
                flex-direction: column;
                transform: none;
                filter: none;
            }
            .sp-lid,
            .sp-controls {
                width: 100%;
                border-left: 0;
                border-right: 0;
            }
            .sp-lid {
                height: calc((100vw - 16px) * 2 / 3 + 50px);
                min-height: 246px;
                max-height: 382px;
                flex: 0 0 auto;
                border-radius: 0 0 14px 14px;
            }
            .sp-screen-frame {
                width: calc(100% - 16px);
                height: auto;
                left: 8px;
                top: max(8px, env(safe-area-inset-top));
                padding: 0 0 34px;
                border-radius: 12px 12px 24px 24px;
            }
            .sp-screen-glass {
                width: 100%;
                height: auto;
                aspect-ratio: 3 / 2;
                box-sizing: border-box;
            }
            .sp-screen-label {
                bottom: 10px;
                font-size: 10px;
            }
            .sp-hinge {
                width: calc(100% - 36px);
                height: 24px;
                min-height: 24px;
                margin: -2px auto;
            }
            .sp-hinge::before,
            .sp-hinge::after {
                width: 48px;
                height: 28px;
            }
            .sp-controls {
                height: auto;
                min-height: 270px;
                flex: 1 1 auto;
                border-radius: 10px 10px 0 0;
            }
            .sp-dpad {
                width: 140px;
                height: 140px;
                left: max(18px, calc(25% - 70px));
                top: 38px;
            }
            .sp-dpad::before { left: 0; top: 46px; width: 136px; height: 46px; }
            .sp-dpad::after { left: 46px; top: 0; width: 46px; height: 136px; }
            .sp-dpad-center { width: 44px; height: 44px; left: 48px; top: 48px; }
            .sp-key-up { width: 46px; height: 48px; left: 47px; top: 0; }
            .sp-key-down { width: 46px; height: 48px; left: 47px; bottom: 0; }
            .sp-key-left { width: 48px; height: 46px; left: 0; top: 47px; }
            .sp-key-right { width: 48px; height: 46px; right: 0; top: 47px; }
            .sp-actions {
                width: 166px;
                height: 126px;
                right: max(8px, calc(25% - 83px));
                top: 36px;
            }
            .sp-action {
                width: 70px;
                height: 70px;
            }
            .sp-action-b { left: 6px; top: 50px; }
            .sp-action-a { right: 6px; top: 2px; }
            .sp-system-buttons {
                left: 50%;
                top: auto;
                bottom: max(28px, calc(env(safe-area-inset-bottom) + 18px));
                gap: 16px;
                transform: translateX(-50%);
            }
            .sp-system-button {
                width: 76px;
                height: 44px;
            }
            .sp-speaker,
            .sp-power,
            .sp-controls::after,
            .sp-help {
                display: none;
            }
            .sp-desktop-label {
                display: none;
            }
            .sp-touch-label {
                display: inline;
            }
            canvas#canvas.emscripten {
                width: 100% !important;
                height: 100% !important;
            }
        }
        @media (orientation: landscape) and (max-height: 600px) {
            #winternight-sp {
                width: 100vw;
                height: 100dvh;
                inset: 0;
                display: block;
                transform: none;
                filter: none;
                background: #020508;
            }
            #winternight-sp .sp-lid {
                width: 100%;
                height: 100%;
                min-height: 0;
                max-height: none;
                position: absolute;
                inset: 0;
                margin: 0;
                aspect-ratio: auto;
                background: #020508;
                border: 0;
                border-radius: 0;
            }
            #winternight-sp .sp-lid::before,
            #winternight-sp .sp-screen-glass::after,
            #winternight-sp .sp-screen-label,
            #winternight-sp .sp-hinge,
            #winternight-sp .sp-speaker,
            #winternight-sp .sp-power,
            #winternight-sp .sp-controls::before,
            #winternight-sp .sp-controls::after {
                display: none;
            }
            #winternight-sp .sp-screen-frame {
                width: 100%;
                height: 100%;
                position: absolute;
                inset: 0;
                padding: 0;
                background: #020508;
                border: 0;
                border-radius: 0;
                box-shadow: none;
            }
            #winternight-sp .sp-screen-glass {
                width: 100%;
                height: 100%;
                display: grid;
                place-items: center;
                aspect-ratio: auto;
                background: #020508;
                border: 0;
                box-shadow: none;
            }
            #winternight-sp canvas#canvas.emscripten {
                width: var(--winternight-game-width) !important;
                height: var(--winternight-game-height) !important;
                outline: 0;
            }
            #winternight-sp .sp-controls {
                width: 100%;
                height: 100%;
                min-width: 0;
                min-height: 0;
                z-index: 8;
                position: fixed;
                inset: 0;
                background: transparent;
                border: 0;
                border-radius: 0;
                box-shadow: none;
                pointer-events: none;
            }
            #winternight-sp .sp-dpad,
            #winternight-sp .sp-actions,
            #winternight-sp .sp-system-buttons {
                pointer-events: auto;
            }
            #winternight-sp .sp-dpad {
                left: max(10px, env(safe-area-inset-left));
                top: auto;
                bottom: max(12px, env(safe-area-inset-bottom));
                transform: none;
            }
            #winternight-sp .sp-actions {
                right: max(2px, env(safe-area-inset-right));
                top: auto;
                bottom: max(40px, calc(env(safe-area-inset-bottom) + 28px));
                transform: rotate(-12deg);
            }
            #winternight-sp .sp-system-buttons {
                left: auto;
                right: max(6px, env(safe-area-inset-right));
                top: auto;
                bottom: max(4px, env(safe-area-inset-bottom));
                gap: 5px;
                transform: none;
            }
            #winternight-sp .sp-system-button {
                width: 46px;
                height: 22px;
                border-radius: 6px;
                font-size: 6px;
            }
        }
        .sp-fullscreen-toggle {
            min-width: 112px;
            min-height: 44px;
            position: fixed;
            top: max(10px, env(safe-area-inset-top));
            right: max(10px, env(safe-area-inset-right));
            z-index: 12;
            display: none;
            padding: 0 14px;
            border: 1px solid #657588;
            border-radius: 22px;
            background: rgba(5, 11, 18, 0.88);
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.45);
            color: #dce5ee;
            font: 700 11px/1 sans-serif;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            cursor: pointer;
            -webkit-tap-highlight-color: transparent;
        }
        @media (pointer: coarse), (max-width: 680px), (max-height: 600px) {
            .sp-fullscreen-toggle {
                display: block;
            }
        }
        #winternight-sp.is-play-mode {
            width: 100vw;
            height: 100dvh;
            inset: 0;
            display: block;
            transform: none;
            filter: none;
            background: #020508;
        }
        #winternight-sp.is-play-mode .sp-lid {
            width: 100%;
            height: 100%;
            min-height: 0;
            max-height: none;
            position: absolute;
            inset: 0;
            margin: 0;
            background: #020508;
            border: 0;
            border-radius: 0;
        }
        #winternight-sp.is-play-mode .sp-lid::before,
        #winternight-sp.is-play-mode .sp-screen-glass::after,
        #winternight-sp.is-play-mode .sp-screen-label,
        #winternight-sp.is-play-mode .sp-hinge,
        #winternight-sp.is-play-mode .sp-speaker,
        #winternight-sp.is-play-mode .sp-power,
        #winternight-sp.is-play-mode .sp-controls::before,
        #winternight-sp.is-play-mode .sp-controls::after {
            display: none;
        }
        #winternight-sp.is-play-mode .sp-screen-frame {
            width: 100%;
            height: 100%;
            position: absolute;
            inset: 0;
            padding: 0;
            background: #020508;
            border: 0;
            border-radius: 0;
            box-shadow: none;
        }
        #winternight-sp.is-play-mode .sp-screen-glass {
            width: 100%;
            height: 100%;
            display: grid;
            place-items: center;
            aspect-ratio: auto;
            background: #020508;
            border: 0;
            box-shadow: none;
        }
        #winternight-sp.is-play-mode canvas#canvas.emscripten {
            width: var(--winternight-game-width) !important;
            height: var(--winternight-game-height) !important;
            outline: 0;
        }
        #winternight-sp.is-play-mode .sp-controls {
            width: 100%;
            height: 100%;
            min-width: 0;
            min-height: 0;
            z-index: 8;
            position: fixed;
            inset: 0;
            background: transparent;
            border: 0;
            border-radius: 0;
            box-shadow: none;
            pointer-events: none;
        }
        #winternight-sp.is-play-mode .sp-dpad,
        #winternight-sp.is-play-mode .sp-actions,
        #winternight-sp.is-play-mode .sp-system-buttons {
            pointer-events: auto;
        }
        #winternight-sp.is-play-mode .sp-dpad {
            left: max(12px, env(safe-area-inset-left));
            top: auto;
            bottom: max(70px, calc(env(safe-area-inset-bottom) + 58px));
            transform: none;
        }
        #winternight-sp.is-play-mode .sp-actions {
            right: max(4px, env(safe-area-inset-right));
            top: auto;
            bottom: max(68px, calc(env(safe-area-inset-bottom) + 56px));
            transform: rotate(-12deg);
        }
        #winternight-sp.is-play-mode .sp-system-buttons {
            left: 50%;
            top: auto;
            bottom: max(10px, env(safe-area-inset-bottom));
            transform: translateX(-50%);
        }
        @media (orientation: landscape) and (max-height: 600px) {
            #winternight-sp.is-play-mode .sp-system-buttons {
                left: auto;
                right: max(6px, env(safe-area-inset-right));
                bottom: max(4px, env(safe-area-inset-bottom));
                gap: 5px;
                transform: none;
            }
            #winternight-sp.is-play-mode .sp-system-button {
                width: 46px;
                height: 22px;
                border-radius: 6px;
                font-size: 6px;
            }
            #winternight-sp.is-cutscene .sp-cutscene-backdrop {
                width: 100%;
                height: var(--winternight-cutscene-height);
                position: absolute;
                left: 0;
                top: 50%;
                z-index: 0;
                display: grid;
                grid-template-columns:
                    minmax(0, 1fr)
                    var(--winternight-cutscene-width)
                    minmax(0, 1fr);
                transform: translateY(-50%);
            }
            #winternight-sp.is-cutscene .sp-cutscene-backdrop img {
                width: 100%;
                height: var(--winternight-cutscene-height);
                display: block;
                object-fit: fill;
                image-rendering: pixelated;
            }
            #winternight-sp.is-cutscene .sp-cutscene-backdrop img[hidden] {
                display: none;
            }
            #winternight-sp.is-cutscene .sp-cutscene-backdrop-left {
                grid-column: 1;
            }
            #winternight-sp.is-cutscene .sp-cutscene-backdrop-right {
                grid-column: 3;
            }
            #winternight-sp.is-cutscene canvas#canvas.emscripten {
                z-index: 1;
                width: var(--winternight-cutscene-width) !important;
                height: var(--winternight-cutscene-height) !important;
                image-rendering: pixelated;
                outline: 1px solid rgba(216, 184, 111, 0.28);
                box-shadow: 0 0 28px rgba(0, 0, 0, 0.72);
            }
        }
        .sp-orientation-hint {
            width: min(350px, calc(100vw - 24px));
            min-height: 58px;
            box-sizing: border-box;
            position: fixed;
            left: 50%;
            bottom: max(12px, env(safe-area-inset-bottom));
            z-index: 20;
            display: none;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 10px 10px 10px 16px;
            transform: translateX(-50%);
            border: 1px solid #657588;
            border-radius: 14px;
            background: rgba(5, 11, 18, 0.94);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
            color: #e2e9f0;
            font: 700 12px/1.35 sans-serif;
            letter-spacing: 0.02em;
        }
        .sp-orientation-hint button {
            min-width: 64px;
            min-height: 44px;
            border: 1px solid #7d8da0;
            border-radius: 10px;
            background: #273545;
            color: #fff;
            font: 700 11px/1 sans-serif;
        }
        .sp-orientation-hint[hidden] {
            display: none;
        }
        @media (orientation: portrait) and (max-width: 680px) {
            /* The dismissible rotate hint used to own the bottom band. The
               Full screen pill needs that band now, and portrait has no third
               row that clears the D-pad, so the hint moves to the top edge. */
            .sp-orientation-hint:not([hidden]) {
                display: flex;
                top: max(12px, env(safe-area-inset-top));
                bottom: auto;
            }
            /* The pill used to sit at the bottom left, directly under the left
               thumb's D-pad arc, and it overlapped the down key outright on
               short viewports. Centre it on the bottom edge, below the
               Log/Start row, where neither thumb rests. */
            .sp-fullscreen-toggle {
                top: auto;
                left: 50%;
                right: auto;
                bottom: max(10px, env(safe-area-inset-bottom));
                transform: translateX(-50%);
            }
            .sp-system-buttons {
                left: auto;
                right: max(10px, env(safe-area-inset-right));
                bottom: max(88px, calc(env(safe-area-inset-bottom) + 78px));
                gap: 8px;
                transform: none;
            }
            /* Play mode packs every control onto the bottom edge, so the pill
               moves into the empty letterbox band above the 3:2 canvas. */
            #winternight-sp.is-play-mode .sp-fullscreen-toggle {
                top: max(10px, env(safe-area-inset-top));
                left: max(10px, env(safe-area-inset-left));
                right: auto;
                bottom: auto;
                transform: none;
            }
            #winternight-sp.is-play-mode .sp-system-buttons {
                left: auto;
                right: max(10px, env(safe-area-inset-right));
                bottom: max(10px, env(safe-area-inset-bottom));
                gap: 8px;
                transform: none;
            }
            #winternight-sp.is-play-mode .sp-dpad,
            #winternight-sp.is-play-mode .sp-actions {
                bottom: max(74px, calc(env(safe-area-inset-bottom) + 64px));
            }
            #winternight-sp.is-play-mode .sp-orientation-hint:not([hidden]) {
                display: none;
            }
        }
        @media (max-height: 650px) {
            .sp-help { display: none; }
        }
        @media (prefers-reduced-motion: no-preference) {
            .sp-power::before,
            .sp-loading-mark { animation: sp-power-breathe 3.2s ease-in-out infinite; }
        }
        @keyframes sp-power-breathe {
            0%, 100% { opacity: 0.65; }
            50% { opacity: 1; }
        }
    </style>
"""
WEB_SHELL_SCRIPT = """    <script id="winternight-integer-scaling">
        (() => {
            // Pygbag's Emscripten runtime opens its audio device during engine
            // start-up, long before the player can gesture, so the browser
            // creates that AudioContext suspended. The runtime's only unlock is
            // Emscripten's autoResumeAudioContext, which arms one-shot
            // keydown/mousedown/touchstart listeners on the document and the
            // canvas. This shell burns all of them without ever unlocking
            // anything: the touch controls below dispatch synthetic mouse and
            // keyboard events, which are untrusted and carry no user
            // activation, and a real "touchstart" is not an activation
            // triggering input event either. Once those listeners are spent
            // nothing can start the audio device again, which left phones
            // silent until a tap on a plain button produced a compatibility
            // mousedown. Own the unlock here instead.
            const audioContexts = new Set();
            for (const name of ["AudioContext", "webkitAudioContext"]) {
                const Original = window[name];
                if (typeof Original !== "function") continue;
                const Tracked = function (...args) {
                    const context = new Original(...args);
                    audioContexts.add(context);
                    return context;
                };
                Tracked.prototype = Original.prototype;
                window[name] = Tracked;
            }
            function resumeGameAudio() {
                for (const context of audioContexts) {
                    if (context.state === "suspended") {
                        context.resume().catch(() => {});
                    }
                }
            }
            function unlockGameAudio(event) {
                // Synthetic events cannot grant user activation, so resuming
                // from one is always refused. Ignore them instead of spending
                // resume attempts on them.
                if (!event.isTrusted) return;
                resumeGameAudio();
            }
            // Touch input grants user activation on release, not on press, so
            // bind the release and click events. Never use {once: true}: an
            // early attempt can be refused and the unlock must stay armed,
            // including after the browser suspends audio in a background tab.
            for (const type of ["pointerup", "touchend", "mousedown", "click", "keydown"]) {
                window.addEventListener(type, unlockGameAudio, {
                    capture: true,
                    passive: true
                });
            }
            // Each page instance runs its own engine and its own audio device,
            // and a hidden tab keeps its device running, so a duplicate tab,
            // an installed window, or a tab left open behind this one plays a
            // second song underneath the visible game with no way to reach it.
            // The visible instance is the only music owner: suspend the device
            // while this page is hidden and resume it when it comes back. A
            // resume that the autoplay policy refuses stays covered by the
            // trusted-gesture unlock above, which is never spent.
            document.addEventListener("visibilitychange", () => {
                if (document.hidden) {
                    for (const context of audioContexts) {
                        if (context.state === "running") {
                            context.suspend().catch(() => {});
                        }
                    }
                    return;
                }
                resumeGameAudio();
            });
        })();
        (() => {
            const canvas = document.getElementById("canvas");
            if (!canvas || document.getElementById("winternight-sp")) return;

            const shell = document.createElement("main");
            shell.id = "winternight-sp";
            shell.setAttribute("aria-label", "Eye of the World handheld game console");
            shell.innerHTML = `
                <section class="sp-lid" aria-label="Game screen">
                    <div class="sp-screen-frame">
                        <div class="sp-screen-glass">
                            <div class="sp-cutscene-backdrop" aria-hidden="true">
                                <img class="sp-cutscene-backdrop-left" alt="" hidden>
                                <img class="sp-cutscene-backdrop-right" alt="" hidden>
                            </div>
                            <div class="sp-loading-splash" role="status"
                                 aria-label="Eye of the World is loading">
                                <img class="sp-loading-mark" src="winternight-splash.png"
                                     alt="" aria-hidden="true">
                                <div class="sp-loading-title">EYE OF THE WORLD</div>
                                <div class="sp-loading-status">Turning the Wheel</div>
                            </div>
                        </div>
                        <div class="sp-screen-label">
                            Eye of the World
                            <span class="sp-desktop-label">tactical story system</span>
                            <span class="sp-touch-label">tap screen to choose</span>
                        </div>
                    </div>
                </section>
                <div class="sp-hinge" aria-hidden="true"></div>
                <section class="sp-controls" aria-label="Game controls">
                    <div class="sp-dpad">
                        <button class="sp-key sp-key-up" data-key="ArrowUp"
                                data-code="ArrowUp" aria-label="Move up">▲</button>
                        <button class="sp-key sp-key-left" data-key="ArrowLeft"
                                data-code="ArrowLeft" aria-label="Move left">◀</button>
                        <span class="sp-dpad-center"></span>
                        <button class="sp-key sp-key-right" data-key="ArrowRight"
                                data-code="ArrowRight" aria-label="Move right">▶</button>
                        <button class="sp-key sp-key-down" data-key="ArrowDown"
                                data-code="ArrowDown" aria-label="Move down">▼</button>
                    </div>
                    <div class="sp-actions">
                        <button class="sp-action sp-action-b" data-key="z"
                                data-code="KeyZ" aria-label="Back">B</button>
                        <button class="sp-action sp-action-a" data-key="x"
                                data-code="KeyX" aria-label="Confirm">A</button>
                    </div>
                    <div class="sp-system-buttons">
                        <button class="sp-system-button" data-key="c"
                                data-code="KeyC" aria-label="Open dialogue log">Log</button>
                        <button class="sp-system-button" data-key="s"
                                data-code="KeyS">Start</button>
                    </div>
                    <div class="sp-speaker" aria-hidden="true">${"<i></i>".repeat(20)}</div>
                    <div class="sp-power">Power</div>
                </section>
                <button class="sp-fullscreen-toggle" type="button" aria-pressed="false"
                        aria-label="Enter fullscreen play mode">Full screen</button>
                <aside class="sp-orientation-hint" role="status">
                    <span>Rotate your phone for a wider view.</span>
                    <button type="button" aria-label="Dismiss orientation suggestion">
                        Dismiss
                    </button>
                </aside>`;

            const glass = shell.querySelector(".sp-screen-glass");
            glass.append(canvas);
            document.body.append(shell);
            const backdropImages = {
                left: glass.querySelector(".sp-cutscene-backdrop-left"),
                right: glass.querySelector(".sp-cutscene-backdrop-right")
            };
            let backdropManifest = {};
            let cutsceneBackground = null;
            function updateCutsceneBackdrop() {
                const entry = backdropManifest[cutsceneBackground];
                for (const [side, image] of Object.entries(backdropImages)) {
                    image.hidden = !entry;
                    if (entry) image.src = entry[side];
                    else image.removeAttribute("src");
                }
            }
            fetch("./cutscene-wide/manifest.json")
                .then((response) => {
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    return response.json();
                })
                .then((manifest) => {
                    backdropManifest = manifest;
                    updateCutsceneBackdrop();
                })
                .catch((error) => {
                    console.error("Could not load wide cutscene backdrops", error);
                });
            const fullscreenToggle = shell.querySelector(".sp-fullscreen-toggle");
            const orientationHint = shell.querySelector(".sp-orientation-hint");
            const dismissOrientationHint = orientationHint.querySelector("button");
            const orientationHintKey = "winternight-rpg:orientation-hint-dismissed:v1";
            try {
                orientationHint.hidden = localStorage.getItem(orientationHintKey) === "1";
            } catch {
                orientationHint.hidden = false;
            }
            dismissOrientationHint.addEventListener("click", (event) => {
                event.preventDefault();
                orientationHint.hidden = true;
                try {
                    localStorage.setItem(orientationHintKey, "1");
                } catch {
                    // The hint still dismisses when browser storage is unavailable.
                }
            });

            const splash = glass.querySelector(".sp-loading-splash");
            const canvasObserver = new MutationObserver(() => {
                if (canvas.width < 480 || canvas.height < 320) return;
                fitGameFrames();
                canvasObserver.disconnect();
                window.requestAnimationFrame(() => {
                    window.requestAnimationFrame(() => splash.remove());
                });
            });
            canvasObserver.observe(canvas, {
                attributes: true,
                attributeFilter: ["width", "height"]
            });

            const help = document.createElement("div");
            help.className = "sp-help";
            help.innerHTML = [
                "Move <kbd>Arrow keys</kbd>",
                "A <kbd>X</kbd>",
                "B <kbd>Z</kbd>",
                "Start <kbd>S</kbd>",
                "Log <kbd>C</kbd>"
            ].join(" · ");
            document.body.append(help);

            const compactShell = window.matchMedia(
                "(pointer: coarse), (max-width: 680px)"
            );

            function fitWinternightShell() {
                const scale = compactShell.matches
                    ? 1
                    : Math.min(
                        1,
                        Math.max(0.2, (window.innerWidth - 24) / 620),
                        Math.max(0.2, (window.innerHeight - 24) / 798)
                    );
                document.documentElement.style.setProperty("--winternight-sp-scale", scale);
            }
            function fitGameFrames() {
                const frameWidth = Math.max(canvas.width, 480);
                const frameHeight = Math.max(canvas.height, 320);
                const fit = Math.min(
                    window.innerWidth / frameWidth,
                    window.innerHeight / frameHeight
                );
                const scale = fit >= 1 ? Math.floor(fit) : fit;
                const width = `${frameWidth * scale}px`;
                const height = `${frameHeight * scale}px`;
                const rootStyle = document.documentElement.style;
                rootStyle.setProperty("--winternight-game-width", width);
                rootStyle.setProperty("--winternight-game-height", height);
                rootStyle.setProperty("--winternight-cutscene-width", width);
                rootStyle.setProperty("--winternight-cutscene-height", height);
            }
            window.winternightSetCutsceneMode = (enabled, background) => {
                shell.classList.toggle("is-cutscene", enabled);
                cutsceneBackground = enabled ? background : null;
                updateCutsceneBackdrop();
                fitGameFrames();
            };
            function updatePlayMode(enabled) {
                shell.classList.toggle("is-play-mode", enabled);
                fullscreenToggle.setAttribute("aria-pressed", String(enabled));
                fullscreenToggle.setAttribute(
                    "aria-label",
                    enabled ? "Exit fullscreen play mode" : "Enter fullscreen play mode"
                );
                fullscreenToggle.textContent = enabled ? "Exit full screen" : "Full screen";
                fitWinternightShell();
                fitGameFrames();
            }

            async function setPlayMode(enabled) {
                updatePlayMode(enabled);
                if (enabled) {
                    if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
                        await document.documentElement
                            .requestFullscreen({navigationUI: "hide"})
                            .catch(() => {});
                    }
                    try {
                        await window.screen.orientation?.lock?.("landscape");
                    } catch {
                        // Orientation lock is optional outside installed/fullscreen PWAs.
                    }
                } else {
                    window.screen.orientation?.unlock?.();
                    if (document.fullscreenElement) {
                        await document.exitFullscreen().catch(() => {});
                    }
                }
            }

            const keyCodes = {
                ArrowUp: 38,
                ArrowDown: 40,
                ArrowLeft: 37,
                ArrowRight: 39,
                KeyX: 88,
                KeyZ: 90,
                KeyS: 83,
                KeyC: 67
            };

            function dispatchKeyboardEvent(type, key, code, repeat = false) {
                canvas.dispatchEvent(new KeyboardEvent(type, {
                    key,
                    code,
                    keyCode: keyCodes[code],
                    which: keyCodes[code],
                    repeat,
                    bubbles: true,
                    cancelable: true
                }));
            }

            function dispatchGameKey(button) {
                canvas.focus({preventScroll: true});
                for (const type of ["keydown", "keyup"]) {
                    dispatchKeyboardEvent(type, button.dataset.key, button.dataset.code);
                }
            }

            for (const type of ["keydown", "keyup"]) {
                window.addEventListener(type, (event) => {
                    if (
                        event.key !== "Enter" ||
                        event.target.closest?.("#winternight-sp button")
                    ) return;
                    event.preventDefault();
                    event.stopImmediatePropagation();
                    canvas.focus({preventScroll: true});
                    dispatchKeyboardEvent(type, "x", "KeyX", event.repeat);
                }, {capture: true});
            }

            function dispatchGamePointer(type, event) {
                canvas.focus({preventScroll: true});
                const pressed = type === "mousedown" ||
                    (type === "mousemove" && canvasPointer !== null);
                canvas.dispatchEvent(new MouseEvent(type, {
                    clientX: event.clientX,
                    clientY: event.clientY,
                    button: 0,
                    buttons: pressed ? 1 : 0,
                    bubbles: true,
                    cancelable: true,
                    view: window
                }));
            }

            // LT's danger-zone display is a sticky toggle: selecting an enemy
            // keeps its red attack range drawn until that very tile is selected
            // again. A pointer that leaves the screen, releases off it, a
            // blurred page, and a full-screen exit all end the gesture that
            // could switch it back off, so report them to the runtime.
            let pendingOverlayClear = false;
            function requestOverlayClear() {
                pendingOverlayClear = true;
            }
            window.winternightTakeOverlayClear = () => {
                const pending = pendingOverlayClear;
                pendingOverlayClear = false;
                return pending ? 1 : 0;
            };
            function pointerLeftCanvas(event) {
                const rect = canvas.getBoundingClientRect();
                return (
                    event.clientX < rect.left ||
                    event.clientX > rect.right ||
                    event.clientY < rect.top ||
                    event.clientY > rect.bottom
                );
            }
            canvas.addEventListener("pointerleave", (event) => {
                // Touch and pen pointers stop existing after every tap, which
                // is not the player leaving the game screen.
                if (event.pointerType !== "mouse") return;
                requestOverlayClear();
            });
            window.addEventListener("blur", requestOverlayClear);

            let canvasPointer = null;
            canvas.addEventListener("pointerdown", (event) => {
                if (!event.isPrimary || event.button !== 0) return;
                event.preventDefault();
                canvasPointer = event.pointerId;
                canvas.setPointerCapture(event.pointerId);
                dispatchGamePointer("mousemove", event);
                dispatchGamePointer("mousedown", event);
                navigator.vibrate?.(8);
            });
            canvas.addEventListener("pointermove", (event) => {
                if (event.pointerType !== "mouse" && event.pointerId !== canvasPointer) return;
                event.preventDefault();
                dispatchGamePointer("mousemove", event);
            });
            const releaseCanvasPointer = (event) => {
                if (event.pointerId !== canvasPointer) return;
                event.preventDefault();
                dispatchGamePointer("mousemove", event);
                dispatchGamePointer("mouseup", event);
                canvasPointer = null;
                if (pointerLeftCanvas(event)) requestOverlayClear();
            };
            canvas.addEventListener("pointerup", releaseCanvasPointer);
            canvas.addEventListener("pointercancel", releaseCanvasPointer);
            canvas.addEventListener("lostpointercapture", releaseCanvasPointer);
            canvas.addEventListener("click", (event) => event.preventDefault());

            const repeaters = new WeakMap();
            shell.querySelectorAll("button[data-key]").forEach((button) => {
                button.addEventListener("pointerdown", (event) => {
                    if (
                        button.dataset.code === "KeyS" &&
                        compactShell.matches &&
                        !shell.classList.contains("is-play-mode")
                    ) {
                        void setPlayMode(true);
                    }
                    event.preventDefault();
                    button.setPointerCapture(event.pointerId);
                    button.classList.add("is-pressed");
                    dispatchGameKey(button);
                    if (button.classList.contains("sp-key")) {
                        repeaters.set(button, window.setInterval(
                            () => dispatchGameKey(button),
                            140
                        ));
                    }
                });
                const release = (event) => {
                    event.preventDefault();
                    button.classList.remove("is-pressed");
                    window.clearInterval(repeaters.get(button));
                    repeaters.delete(button);
                };
                button.addEventListener("pointerup", release);
                button.addEventListener("pointercancel", release);
                button.addEventListener("lostpointercapture", release);
            });
            fullscreenToggle.addEventListener("click", (event) => {
                event.preventDefault();
                void setPlayMode(!shell.classList.contains("is-play-mode"));
            });
            document.addEventListener("fullscreenchange", () => {
                requestOverlayClear();
                if (!document.fullscreenElement && shell.classList.contains("is-play-mode")) {
                    updatePlayMode(false);
                    window.screen.orientation?.unlock?.();
                }
            });

            window.addEventListener("resize", () => {
                fitWinternightShell();
                fitGameFrames();
            }, {passive: true});
            fitWinternightShell();
            fitGameFrames();
            window.requestAnimationFrame(fitWinternightShell);
        })();
        if ("serviceWorker" in navigator) {
            window.addEventListener("load", () => {
                navigator.serviceWorker.register("./sw.js");
            });
        }
    </script>
"""


def _copytree(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests", "test", "demo_code"),
    )


def stage_web_application(
    root: Path,
    project: Path,
    engine_root: Path,
    output: Path,
    engine_commit: str,
) -> dict[str, object]:
    root = root.resolve()
    output = output.resolve()
    build_root = (root / "build").resolve()
    if output == build_root or not output.is_relative_to(build_root):
        raise ValueError(f"web stage must be a child of {build_root}: {output}")
    if not project.is_dir():
        raise FileNotFoundError(f"compiled project is missing: {project}")
    runtime_main = root / "web" / "runtime_main.py"
    if not runtime_main.is_file():
        raise FileNotFoundError(f"browser runtime is missing: {runtime_main}")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    app_source = engine_root / "app"
    app_output = output / "app"
    app_output.mkdir()
    for source in sorted(app_source.iterdir()):
        if source.is_file() and source.suffix == ".py":
            shutil.copy2(source, app_output / source.name)
        elif source.is_dir() and source.name in RUNTIME_DIRECTORIES:
            _copytree(source, app_output / source.name)

    # One runtime menu helper imports this small editor-independent math module.
    math_source = app_source / "editor" / "lib" / "math"
    math_output = app_output / "editor" / "lib" / "math"
    math_output.parent.mkdir(parents=True)
    _copytree(math_source, math_output)
    for package in (app_output / "editor", app_output / "editor" / "lib"):
        (package / "__init__.py").touch()

    _copytree(engine_root / "sprites", output / "sprites")
    _copytree(engine_root / "resources" / "platforms", output / "resources" / "platforms")
    _copytree(project, output / "winternight.ltproj")
    shutil.copy2(runtime_main, output / "main.py")
    shutil.copy2(engine_root / "favicon.ico", output / "favicon.ico")
    shutil.copy2(engine_root / "LICENSE.txt", output / "LEX_TALIONIS_LICENSE.txt")

    typing_extensions = importlib.util.find_spec("typing_extensions")
    if typing_extensions and typing_extensions.origin:
        shutil.copy2(typing_extensions.origin, output / "typing_extensions.py")

    manifest = {
        "adapter_version": WEB_ADAPTER_VERSION,
        "engine_commit": engine_commit,
        "project_tree_hash": tree_hash(project),
        "project_manifest_sha256": sha256(project / "build_manifest.json"),
        "entry_point": "main.py",
    }
    (output / "web_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _write_wide_cutscene_backdrops(root: Path, output: Path) -> dict[str, dict[str, str]]:
    manifest_path = root / "design" / "asset_manifest.yaml"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"asset manifest is missing: {manifest_path}")
    assets = yaml.safe_load(manifest_path.read_text(encoding="utf-8")).get("assets", [])
    backdrop_root = output / "cutscene-wide"
    if backdrop_root.exists():
        shutil.rmtree(backdrop_root)
    backdrop_root.mkdir()

    manifest: dict[str, dict[str, str]] = {}
    for asset in sorted(assets, key=lambda entry: entry["id"]):
        source_path = asset.get("source_path")
        if (
            asset.get("type") != "background"
            or asset.get("approval_status") != "approved"
            or not source_path
        ):
            continue
        asset_id = asset["id"]
        if not re.fullmatch(r"[A-Za-z0-9_-]+", asset_id):
            raise ValueError(f"background ID is not web-path safe: {asset_id}")
        source_file = (root / source_path).resolve()
        if not source_file.is_relative_to(root) or not source_file.is_file():
            raise FileNotFoundError(f"background source is missing: {source_file}")

        with Image.open(source_file) as opened:
            source = opened.convert("RGB")
        crop_width = source.height * 1.5
        if source.width <= crop_width:
            continue
        crop_left = (source.width - crop_width) / 2
        crop_right = crop_left + crop_width
        crops = {
            "left": (0, 0, crop_left, source.height),
            "right": (crop_right, 0, source.width, source.height),
        }
        entry: dict[str, str] = {}
        for side, crop in crops.items():
            rail_width = max(1, round((crop[2] - crop[0]) * 160 / source.height))
            rail = source.crop(crop).resize(
                (rail_width, 160),
                Image.Resampling.LANCZOS,
            )
            rail = rail.quantize(
                colors=64,
                method=Image.Quantize.MEDIANCUT,
                dither=Image.Dither.NONE,
            ).convert("RGB")
            filename = f"{asset_id}-{side}.png"
            rail.save(
                backdrop_root / filename,
                format="PNG",
                optimize=False,
                compress_level=9,
            )
            entry[side] = f"./cutscene-wide/{filename}"
        manifest[asset_id] = entry

    (backdrop_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def finalize_pygbag_build(
    root: Path,
    output: Path,
    *,
    browserfs_bytes: bytes | None = None,
) -> dict[str, object]:
    """Make Pygbag 0.9.3's browser output self-consistent and deployable.

    Pygbag 0.9.3 emits a BrowserFS URL that no longer exists. We vendor the
    exact archived script into the generated site and verify its pinned hash.
    """
    root = root.resolve()
    output = output.resolve()
    build_root = (root / "build").resolve()
    if output == build_root or not output.is_relative_to(build_root):
        raise ValueError(f"web output must be a child of {build_root}: {output}")

    index_path = output / "index.html"
    if not index_path.is_file():
        raise FileNotFoundError(f"Pygbag index is missing: {index_path}")

    if browserfs_bytes is None:
        with urllib.request.urlopen(BROWSERFS_URL, timeout=30) as response:  # noqa: S310
            browserfs_bytes = response.read()
    actual_hash = hashlib.sha256(browserfs_bytes).hexdigest()
    if actual_hash != BROWSERFS_SHA256:
        raise RuntimeError(
            f"BrowserFS hash mismatch: expected {BROWSERFS_SHA256}, found {actual_hash}"
        )

    index = index_path.read_text(encoding="utf-8")
    if index.count(BROKEN_BROWSERFS_SCRIPT) == 1:
        index = index.replace(BROKEN_BROWSERFS_SCRIPT, LOCAL_BROWSERFS_SCRIPT)
    elif index.count(LOCAL_BROWSERFS_SCRIPT) != 1:
        raise RuntimeError("Pygbag BrowserFS script reference changed; update the web adapter")
    if index.count(DEBUG_TERMINAL_CONFIG) == 1:
        index = index.replace(DEBUG_TERMINAL_CONFIG, PRODUCTION_TERMINAL_CONFIG)
    elif index.count(PRODUCTION_TERMINAL_CONFIG) != 1:
        raise RuntimeError("Pygbag terminal configuration changed; update the web adapter")
    if index.count("</head>") != 1 or index.count("</body>") != 1:
        raise RuntimeError("Pygbag document structure changed; update the web adapter")
    index = re.sub(r'\s*<meta name="viewport"[^>]*>\s*', "\n", index)
    index = re.sub(
        r'\s*<(?:meta|link) id="winternight-[^"]+"[^>]*>\s*',
        "\n",
        index,
    )
    index, style_count = re.subn(
        r'\s*<style id="winternight-web-shell">.*?</style>\s*',
        "\n",
        index,
        flags=re.DOTALL,
    )
    index, script_count = re.subn(
        r'\s*<script id="winternight-integer-scaling">.*?</script>\s*',
        "\n",
        index,
        flags=re.DOTALL,
    )
    if style_count > 1 or script_count > 1:
        raise RuntimeError("duplicate Winternight web shell markers found")
    index_path.write_text(
        index.replace("</head>", f"{PWA_HEAD}{WEB_SHELL_STYLE}</head>").replace(
            "</body>", f"{WEB_SHELL_SCRIPT}</body>"
        ),
        encoding="utf-8",
    )
    (output / "manifest.webmanifest").write_text(
        json.dumps(PWA_MANIFEST, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "sw.js").write_text(PWA_SERVICE_WORKER, encoding="utf-8")
    with Image.open(output / "favicon.png") as favicon:
        icon = favicon.convert("RGBA")
        for size in (192, 512):
            icon.resize((size, size), Image.Resampling.LANCZOS).save(
                output / f"pwa-icon-{size}.png",
                optimize=True,
            )
    browserfs_path = output / "browserfs.min.js"
    browserfs_path.write_bytes(browserfs_bytes)
    splash_source = root / "assets" / "generated_sources" / "title_dragon_wheel-v1.png"
    if not splash_source.is_file():
        raise FileNotFoundError(f"web splash source is missing: {splash_source}")
    splash_path = output / "winternight-splash.png"
    shutil.copyfile(splash_source, splash_path)
    cutscene_backdrops = _write_wide_cutscene_backdrops(root, output)
    return {
        "browserfs_sha256": actual_hash,
        "splash_sha256": sha256(splash_path),
        "cutscene_backdrops": len(cutscene_backdrops),
        "cutscene_backdrop_manifest_sha256": sha256(
            output / "cutscene-wide" / "manifest.json"
        ),
        "browserfs_url": BROWSERFS_URL,
        "web_output": str(output),
    }
