#!/usr/bin/env bash
# 来雪亭 :: render-png.sh —— 用本机 Chrome 的无头模式把 deck 逐页截成 PNG（2026-11-23 自写）
#
# 用法：
#   render-png.sh <html>               只截第 1 页
#   render-png.sh <html> all           先数页，再逐页截
#   render-png.sh <html> <N>           截 1..N 页
#   render-png.sh <html> <N> <out>     指定输出目录（或 .png 单文件）
# 环境：CHROME_BIN 指定浏览器；FORCE=1 覆盖已有文件。
#
# 四条判据（都是真踩过才写下来的）：
#   ① 数页不能直接 grep `<section class="slide"` —— 内联的 runtime 与总览克隆都会带这行，
#      要先剥 <script>/<style> 再数，且用词界匹配，免得 `slides` 之类被算进来；
#   ② Chrome 写不出文件时**也返回 0**，所以成败只认「目标文件是否非空」，不看退出码；
#   ③ 已有且非空的 PNG 默认跳过，要重出得显式 FORCE=1（避免手滑覆盖上一版的证据图）；
#   ④ 逐页靠 `#/N` 深链落位，不靠键盘模拟 —— 无头环境里没有按键这回事；
#      查询串带 `?render`：runtime 见到它就掐掉 CSS 过渡与入场动效（过渡不吃虚拟时间，
#      不掐会截在 opacity 0.5 的过渡半路上，整页发灰）。

set -euo pipefail

CHROME="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
if [[ ! -x "$CHROME" ]]; then
  if [[ -x "/Applications/Chromium.app/Contents/MacOS/Chromium" ]]; then
    CHROME="/Applications/Chromium.app/Contents/MacOS/Chromium"
  else
    echo "error: 找不到 Chrome/Chromium（可用 CHROME_BIN 指定）" >&2
    exit 1
  fi
fi

FILE="${1:-}"
if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "usage: render-png.sh <html> [N|all] [out-dir]" >&2
  exit 1
fi

COUNT="${2:-1}"
OUT="${3:-}"
ABS="$(cd "$(dirname "$FILE")" && pwd)/$(basename "$FILE")"
STEM="$(basename "${FILE%.*}")"

count_slides() {
  python3 - "$1" <<'PY'
import re, sys
html = open(sys.argv[1], encoding='utf-8', errors='replace').read()
html = re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.S | re.I)
html = re.sub(r'<style\b[^>]*>.*?</style>', '', html, flags=re.S | re.I)
pat = r'<section\b[^>]*class="[^"]*(?<![A-Za-z0-9_-])slide(?![A-Za-z0-9_-])[^"]*"'
print(len(re.findall(pat, html, flags=re.I)))
PY
}

if [[ "$COUNT" == "all" ]]; then
  COUNT="$(count_slides "$FILE")"
  [[ "$COUNT" -ge 1 ]] 2>/dev/null || COUNT=1
fi
if ! [[ "$COUNT" =~ ^[0-9]+$ ]] || [[ "$COUNT" -lt 1 ]]; then
  echo "error: 页数要是正整数或 all（收到：$COUNT）" >&2
  exit 1
fi
if [[ -z "$OUT" && "$COUNT" -gt 1 ]]; then
  OUT="$(dirname "$FILE")/${STEM}-png"
fi
if [[ -n "$OUT" && "$OUT" != *.png ]]; then
  mkdir -p "$OUT"
fi

shoot() {
  local url="$1" target="$2"
  if [[ -s "$target" && "${FORCE:-0}" != "1" ]]; then
    echo "  = 已存在，跳过 $target"
    return 0
  fi
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-sandbox \
    --virtual-time-budget=4000 --run-all-compositor-stages-before-draw \
    --window-size=1920,1080 --screenshot="$target" "$url" >/dev/null 2>&1 || true
  if [[ ! -s "$target" ]]; then
    echo "  ✗ $target — 没写出来" >&2
    return 1
  fi
  echo "  ✔ $target"
}

FAILED=0
if [[ "$COUNT" == "1" ]]; then
  if [[ -z "$OUT" ]]; then OUT_FILE="$(dirname "$FILE")/${STEM}.png"
  elif [[ "$OUT" == *.png ]]; then OUT_FILE="$OUT"
  else OUT_FILE="$OUT/${STEM}.png"; fi
  shoot "file://$ABS?render" "$OUT_FILE" || FAILED=$((FAILED + 1))
else
  for i in $(seq 1 "$COUNT"); do
    shoot "file://$ABS?render#/$i" "$OUT/${STEM}_$(printf '%02d' "$i").png" || FAILED=$((FAILED + 1))
  done
fi

if [[ "$FAILED" -gt 0 ]]; then
  echo "error: $FAILED/$COUNT 页没截出来：$FILE" >&2
  exit 1
fi
echo "done: $FILE → $COUNT 页"
