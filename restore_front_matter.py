#!/usr/bin/env python3
"""
Full front-matter restoration:
  - Replace ALL cover/half-title/title/copyright/toc/foreword/abbrev/part/sourceintro CSS
    with exact values from the section files.
  - Replace sections 2 and 3 HTML (half-title, title page) with section-file structure
    (they use completely different CSS class names in the book vs section files).
  - Keep sections 4-9 HTML as-is; CSS fixes alone are sufficient for them.
  - Leave sections 10, 12, 13 (chapters + indices) completely untouched.
"""
import re
from pathlib import Path

DIR = Path(r'C:\Users\zande\Documents\AI Workspace\Analyzing Islam\book-design\vol1-quran')
BOOK = next(f for f in DIR.iterdir() if 'Analyzing' in f.name and f.suffix == '.html' and 'Vol' in f.name)
html = BOOK.read_text(encoding='utf-8', errors='ignore')
print(f'Book: {BOOK.name}  ({len(html):,} chars)')

SEP = '=' * 54

# ─────────────────────────────────────────────────────────────────────────────
# 1.  REPLACE COVERS CSS BLOCK
# ─────────────────────────────────────────────────────────────────────────────
OLD_COVERS_CSS = """  /* ═══════════════════════════════════════
     COVERS
  ═══════════════════════════════════════ */
  .cf2-geo-origin { position: absolute; width: 0; height: 0; top: 472px; left: 332px; }
  .cf2-ring { position: absolute; border-radius: 50%; transform: translate(-50%, -50%); }
  .cf2-r1 { width: 800px; height: 800px; border: 1px solid rgba(255,255,255,0.025); }
  .cf2-r2 { width: 620px; height: 620px; border: 1px solid rgba(255,255,255,0.035); }
  .cf2-r3 { width: 440px; height: 440px; border: 1px solid rgba(255,255,255,0.045); }
  .cf2-r4 { width: 260px; height: 260px; border: 1px solid rgba(255,255,255,0.06); }
  .cf2-r5 { width: 100px; height: 100px; border: 1px solid rgba(255,255,255,0.08); }
  .cf2-top-rule { position: absolute; top: 40px; left: 0; right: 0; height: 1px; background: #161616; }
  .cf2-series { position: absolute; top: 24px; left: 0; right: 0; text-align: center; font-family: system-ui, sans-serif; font-size: 11px; letter-spacing: 0.32em; text-transform: uppercase; color: #787878; }
  .cf2-title-block { position: absolute; top: 325px; left: 0; right: 0; text-align: center; padding: 0 40px; }
  .cf2-word { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 82px; font-weight: bold; color: #f5f5f5; line-height: 1; letter-spacing: -0.02em; display: block; }
  .cf2-red-rule { display: block; width: calc(100% + 80px); margin-left: -40px; height: 1px; background: #e53935; margin-top: 22px; margin-bottom: 14px; }
  .cf2-info-block { position: absolute; top: 545px; left: 0; right: 0; text-align: center; padding: 0 52px; }
  .cf2-info-rule { width: 40px; height: 1px; background: #2a2a2a; margin: 0 auto 16px; }
  .cf2-volume { font-family: system-ui, sans-serif; font-size: 13px; letter-spacing: 0.3em; text-transform: uppercase; color: #787878; margin-bottom: 10px; }
  .cf2-sources { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 22px; font-style: italic; color: #9a9a9a; margin-bottom: 10px; }
  .cf2-descriptor { font-family: system-ui, sans-serif; font-size: 11px; letter-spacing: 0.22em; text-transform: uppercase; color: #787878; }
  .cf2-author-block { position: absolute; bottom: 110px; left: 0; right: 0; text-align: center; }
  .cf2-author-rule { width: 40px; height: 1px; background: #2a2a2a; margin: 0 auto 16px; }
  .cf2-author { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 20px; color: #f5f5f5; letter-spacing: 0.03em; }
  .cf2-footer { position: absolute; bottom: 0; left: 0; right: 0; }
  .cf2-footer-rule { width: 100%; height: 1px; background: #161616; }
  .cf2-pub { display: block; text-align: center; font-family: system-ui, sans-serif; font-size: 11px; letter-spacing: 0.28em; text-transform: uppercase; color: #787878; padding: 14px 0; }
  .bc2-inner { position: absolute; top: 68px; bottom: 72px; left: 64px; right: 64px; display: flex; flex-direction: column; align-items: center; text-align: center; }
  .bc2-logo-title { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 38px; font-weight: bold; color: #f5f5f5; letter-spacing: -0.01em; margin-bottom: 6px; }
  .bc2-logo-rule { width: 100%; height: 1px; background: #e53935; margin-bottom: 6px; }
  .bc2-logo-sub { font-family: system-ui, sans-serif; font-size: 11px; letter-spacing: 0.22em; text-transform: uppercase; color: #787878; margin-bottom: 28px; }
  .bc2-top-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 26px; }
  .bc2-blurb { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 14px; font-style: italic; line-height: 1.8; color: #c0c0c0; margin-bottom: 26px; max-width: 480px; }
  .bc2-features { width: 100%; margin-bottom: 24px; text-align: left; }
  .bc2-feat { font-family: system-ui, sans-serif; font-size: 13.5px; line-height: 1.85; color: #787878; padding-left: 16px; position: relative; }
  .bc2-feat::before { content: '·'; position: absolute; left: 0; color: #e53935; font-size: 14px; line-height: 1.4; }
  .bc2-mid-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 20px; }
  .bc2-author-label { font-family: system-ui, sans-serif; font-size: 11px; letter-spacing: 0.28em; text-transform: uppercase; color: #787878; margin-bottom: 10px; }
  .bc2-bio { font-family: system-ui, sans-serif; font-size: 13.5px; line-height: 1.8; color: #787878; max-width: 460px; }
  .bc2-bottom { position: absolute; bottom: 0; left: 64px; right: 64px; }
  .bc2-bottom-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 16px; }
  .bc2-bottom-row { display: flex; justify-content: space-between; align-items: flex-end; }
  .bc2-barcode-wrap { display: flex; flex-direction: column; align-items: flex-start; gap: 5px; }
  .bc2-barcode { width: 112px; height: 64px; background: repeating-linear-gradient(90deg,#fff 0px,#fff 1px,#000 1px,#000 3px,#fff 3px,#fff 4px,#000 4px,#000 7px,#fff 7px,#fff 8px,#000 8px,#000 10px,#fff 10px,#fff 13px,#000 13px,#000 15px,#fff 15px,#fff 16px,#000 16px,#000 19px,#fff 19px,#fff 21px,#000 21px,#000 23px,#fff 23px,#fff 25px,#000 25px,#000 27px,#fff 27px,#fff 28px,#000 28px,#000 32px,#fff 32px,#fff 34px,#000 34px,#000 36px,#fff 36px,#fff 38px,#000 38px,#000 40px,#fff 40px,#fff 41px,#000 41px,#000 44px,#fff 44px,#fff 46px,#000 46px,#000 48px,#fff 48px,#fff 50px,#000 50px,#000 52px,#fff 52px,#fff 53px,#000 53px,#000 57px,#fff 57px,#fff 59px,#000 59px,#000 62px,#fff 62px,#fff 65px,#000 65px,#000 67px,#fff 67px,#fff 70px,#000 70px,#000 74px,#fff 74px,#fff 76px,#000 76px,#000 79px,#fff 79px,#fff 81px,#000 81px,#000 83px,#fff 83px,#fff 85px,#000 85px,#000 88px,#fff 88px,#fff 89px,#000 89px,#000 92px,#fff 92px,#fff 94px,#000 94px,#000 96px,#fff 96px,#fff 98px,#000 98px,#000 101px,#fff 101px,#fff 102px,#000 102px,#000 105px,#fff 105px,#fff 107px,#000 107px,#000 109px,#fff 109px,#fff 110px,#000 110px,#000 112px); }
  .bc2-isbn { font-family: system-ui, sans-serif; font-size: 10px; color: #787878; letter-spacing: 0.08em; }
  .bc2-bottom-right { text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
  .bc2-price { font-family: system-ui, sans-serif; font-size: 11px; color: #787878; letter-spacing: 0.06em; }
  .bc2-pub-bottom { font-family: system-ui, sans-serif; font-size: 11px; letter-spacing: 0.28em; text-transform: uppercase; color: #787878; }"""

NEW_COVERS_CSS = """  /* ═══════════════════════════════════════
     COVERS
  ═══════════════════════════════════════ */
  .cf2-geo-origin { position: absolute; width: 0; height: 0; top: 430px; left: 332px; }
  .cf2-ring { position: absolute; border-radius: 50%; transform: translate(-50%, -50%); }
  .cf2-r1 { width: 800px; height: 800px; border: 1px solid rgba(255,255,255,0.025); }
  .cf2-r2 { width: 620px; height: 620px; border: 1px solid rgba(255,255,255,0.035); }
  .cf2-r3 { width: 440px; height: 440px; border: 1px solid rgba(255,255,255,0.045); }
  .cf2-r4 { width: 260px; height: 260px; border: 1px solid rgba(255,255,255,0.06); }
  .cf2-r5 { width: 100px; height: 100px; border: 1px solid rgba(255,255,255,0.08); }
  .cf2-top-rule { position: absolute; top: 40px; left: 0; right: 0; height: 1px; background: #161616; }
  .cf2-series { position: absolute; top: 24px; left: 0; right: 0; text-align: center; font-family: system-ui, sans-serif; font-size: 7.5px; letter-spacing: 0.32em; text-transform: uppercase; color: #2a2a2a; }
  .cf2-title-block { position: absolute; top: 270px; left: 0; right: 0; text-align: center; padding: 0 40px; }
  .cf2-word { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 82px; font-weight: bold; color: #f5f5f5; line-height: 1; letter-spacing: -0.02em; display: block; }
  .cf2-red-rule { display: block; width: calc(100% + 80px); margin-left: -40px; height: 1px; background: #e53935; margin-top: 18px; margin-bottom: 18px; }
  .cf2-info-block { position: absolute; top: 490px; left: 0; right: 0; text-align: center; padding: 0 52px; }
  .cf2-info-rule { width: 40px; height: 1px; background: #2a2a2a; margin: 0 auto 16px; }
  .cf2-volume { font-family: system-ui, sans-serif; font-size: 8.5px; letter-spacing: 0.3em; text-transform: uppercase; color: #4a4a4a; margin-bottom: 8px; }
  .cf2-sources { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 15px; font-style: italic; color: #6a6a6a; margin-bottom: 8px; letter-spacing: 0.01em; }
  .cf2-descriptor { font-family: system-ui, sans-serif; font-size: 8px; letter-spacing: 0.22em; text-transform: uppercase; color: #323232; }
  .cf2-author-block { position: absolute; bottom: 110px; left: 0; right: 0; text-align: center; }
  .cf2-author-rule { width: 40px; height: 1px; background: #2a2a2a; margin: 0 auto 16px; }
  .cf2-author { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 20px; color: #f5f5f5; letter-spacing: 0.03em; }
  .cf2-footer { position: absolute; bottom: 0; left: 0; right: 0; }
  .cf2-footer-rule { width: 100%; height: 1px; background: #161616; }
  .cf2-pub { display: block; text-align: center; font-family: system-ui, sans-serif; font-size: 7.5px; letter-spacing: 0.28em; text-transform: uppercase; color: #282828; padding: 14px 0; }
  .bc2-inner { position: absolute; top: 68px; bottom: 72px; left: 64px; right: 64px; display: flex; flex-direction: column; align-items: center; text-align: center; }
  .bc2-logo-title { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 28px; font-weight: bold; color: #f5f5f5; letter-spacing: -0.01em; margin-bottom: 6px; }
  .bc2-logo-rule { width: 100%; height: 1px; background: #e53935; margin-bottom: 6px; }
  .bc2-logo-sub { font-family: system-ui, sans-serif; font-size: 7.5px; letter-spacing: 0.22em; text-transform: uppercase; color: #4a4a4a; margin-bottom: 28px; }
  .bc2-top-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 26px; }
  .bc2-blurb { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 13px; font-style: italic; line-height: 1.8; color: #c0c0c0; margin-bottom: 26px; max-width: 480px; }
  .bc2-features { width: 100%; margin-bottom: 24px; text-align: left; }
  .bc2-feat { font-family: system-ui, sans-serif; font-size: 9.5px; line-height: 1.85; color: #6a6a6a; padding-left: 16px; position: relative; }
  .bc2-feat::before { content: '·'; position: absolute; left: 0; color: #e53935; font-size: 13px; line-height: 1.4; }
  .bc2-mid-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 20px; }
  .bc2-author-label { font-family: system-ui, sans-serif; font-size: 7.5px; letter-spacing: 0.28em; text-transform: uppercase; color: #4a4a4a; margin-bottom: 10px; }
  .bc2-bio { font-family: system-ui, sans-serif; font-size: 10px; line-height: 1.8; color: #6a6a6a; max-width: 460px; }
  .bc2-bottom { position: absolute; bottom: 0; left: 64px; right: 64px; }
  .bc2-bottom-rule { width: 100%; height: 1px; background: #1a1a1a; margin-bottom: 16px; }
  .bc2-bottom-row { display: flex; justify-content: space-between; align-items: flex-end; }
  .bc2-barcode-wrap { display: flex; flex-direction: column; align-items: flex-start; gap: 5px; }
  .bc2-barcode { width: 112px; height: 64px; background: repeating-linear-gradient(90deg,#fff 0px,#fff 1px,#000 1px,#000 3px,#fff 3px,#fff 4px,#000 4px,#000 7px,#fff 7px,#fff 8px,#000 8px,#000 10px,#fff 10px,#fff 13px,#000 13px,#000 15px,#fff 15px,#fff 16px,#000 16px,#000 19px,#fff 19px,#fff 21px,#000 21px,#000 23px,#fff 23px,#fff 25px,#000 25px,#000 27px,#fff 27px,#fff 28px,#000 28px,#000 32px,#fff 32px,#fff 34px,#000 34px,#000 36px,#fff 36px,#fff 38px,#000 38px,#000 40px,#fff 40px,#fff 41px,#000 41px,#000 44px,#fff 44px,#fff 46px,#000 46px,#000 48px,#fff 48px,#fff 50px,#000 50px,#000 52px,#fff 52px,#fff 53px,#000 53px,#000 57px,#fff 57px,#fff 59px,#000 59px,#000 62px,#fff 62px,#fff 65px,#000 65px,#000 67px,#fff 67px,#fff 70px,#000 70px,#000 74px,#fff 74px,#fff 76px,#000 76px,#000 79px,#fff 79px,#fff 81px,#000 81px,#000 83px,#fff 83px,#fff 85px,#000 85px,#000 88px,#fff 88px,#fff 89px,#000 89px,#000 92px,#fff 92px,#fff 94px,#000 94px,#000 96px,#fff 96px,#fff 98px,#000 98px,#000 101px,#fff 101px,#fff 102px,#000 102px,#000 105px,#fff 105px,#fff 107px,#000 107px,#000 109px,#fff 109px,#fff 110px,#000 110px,#000 112px); }
  .bc2-isbn { font-family: system-ui, sans-serif; font-size: 8px; color: #4a4a4a; letter-spacing: 0.08em; }
  .bc2-bottom-right { text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
  .bc2-price { font-family: system-ui, sans-serif; font-size: 11px; color: #4a4a4a; letter-spacing: 0.06em; }
  .bc2-pub-bottom { font-family: system-ui, sans-serif; font-size: 7.5px; letter-spacing: 0.28em; text-transform: uppercase; color: #2a2a2a; }"""

if OLD_COVERS_CSS in html:
    html = html.replace(OLD_COVERS_CSS, NEW_COVERS_CSS)
    print('1. Covers CSS replaced with section-file values.')
else:
    print('WARNING 1: covers CSS block not found.')

# ─────────────────────────────────────────────────────────────────────────────
# 2.  REPLACE HALF-TITLE & TITLE CSS BLOCK  +  ADD HALF-TITLE CLASS CSS
# ─────────────────────────────────────────────────────────────────────────────
OLD_HT_CSS = """  /* ═══════════════════════════════════════
     HALF-TITLE & TITLE
  ═══════════════════════════════════════ */
  .ht-title { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 36px; font-weight: bold; color: #f5f5f5; position: absolute; top: 50%; left: 0; transform: translateY(-50%); letter-spacing: -0.01em; line-height: 1.1; }
  .ht-volume { font-family: system-ui, sans-serif; font-size: 9px; letter-spacing: 0.28em; text-transform: uppercase; color: #5a5a5a; margin-bottom: 10px; position: absolute; top: calc(50% - 60px); left: 0; }
  .ht-source-label { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-style: italic; font-size: 13px; color: #5a5a5a; position: absolute; top: calc(50% + 60px); left: 0; }
  .title-block { position: absolute; top: 50%; left: 0; right: 0; transform: translateY(-50%); }
  .title-main { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 64px; font-weight: bold; color: #f5f5f5; line-height: 1; letter-spacing: -0.03em; margin-bottom: 6px; }
  .title-red-rule { width: 100%; height: 1px; background: #e53935; margin: 16px 0; }
  .title-source-subtitle { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 26px; font-weight: bold; color: #f5f5f5; letter-spacing: -0.01em; line-height: 1.1; margin-bottom: 6px; }
  .title-source-descriptor { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-style: italic; font-size: 14px; color: #6a6a6a; }
  .title-colophon { position: absolute; bottom: 0; left: 0; right: 0; }
  .title-colophon-rule { width: 100%; height: 1px; background: #1e1e1e; margin-bottom: 14px; }
  .title-colophon-row { display: flex; justify-content: space-between; }
  .title-colophon-text { font-family: system-ui, sans-serif; font-size: 9px; letter-spacing: 0.15em; text-transform: uppercase; color: #3a3a3a; }"""

NEW_HT_CSS = """  /* ═══════════════════════════════════════
     HALF-TITLE
  ═══════════════════════════════════════ */
  .half-title-block { margin-top: 180px; }
  .book-title { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 42px; font-weight: bold; line-height: 1.05; letter-spacing: -0.01em; color: #f5f5f5; }
  .volume-label { margin-top: 18px; font-family: system-ui,sans-serif; font-size: 11px; letter-spacing: 0.22em; text-transform: uppercase; color: #9a9a9a; }
  .source-label { margin-top: 6px; font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 13px; font-style: italic; color: #5a5a5a; }
  .ht-rule { margin-top: 16px; width: 40px; height: 1px; background: #3a3a3a; }

  /* ═══════════════════════════════════════
     TITLE PAGE
  ═══════════════════════════════════════ */
  .title-block { margin-top: 140px; }
  .main-title { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 52px; font-weight: bold; line-height: 1.0; letter-spacing: -0.015em; color: #f5f5f5; }
  .title-divider { margin-top: 20px; width: 100%; height: 1px; background: #1e1e1e; }
  .title-volume-line { margin-top: 18px; font-family: system-ui,sans-serif; font-size: 11px; letter-spacing: 0.22em; text-transform: uppercase; color: #9a9a9a; }
  .title-source-subtitle { margin-top: 20px; font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 26px; font-weight: bold; color: #f5f5f5; letter-spacing: -0.01em; }
  .title-source-descriptor { margin-top: 10px; font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 14px; font-style: italic; color: #6a6a6a; letter-spacing: 0.01em; }
  .title-colophon { position: absolute; bottom: 0; left: 0; right: 0; }
  .title-colophon-rule { width: 100%; height: 1px; background: #1e1e1e; margin-bottom: 16px; }
  .title-colophon-site { font-family: system-ui,sans-serif; font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: #5a5a5a; }
  .title-colophon-year { margin-top: 6px; font-family: system-ui,sans-serif; font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: #5a5a5a; }"""

if OLD_HT_CSS in html:
    html = html.replace(OLD_HT_CSS, NEW_HT_CSS)
    print('2. Half-title & title CSS replaced with section-file values.')
else:
    print('WARNING 2: half-title/title CSS block not found.')

# ─────────────────────────────────────────────────────────────────────────────
# 3.  FIX COPYRIGHT FONT SIZES
# ─────────────────────────────────────────────────────────────────────────────
OLD_CR_CSS = """  /* ═══════════════════════════════════════
     COPYRIGHT
  ═══════════════════════════════════════ */
  .copyright-block { position: absolute; bottom: 0; left: 0; right: 0; }
  .copyright-line { font-family: system-ui, sans-serif; font-size: 13.5px; color: #f5f5f5; line-height: 1.7; margin-bottom: 20px; }
  .copyright-line strong { color: #f5f5f5; font-weight: 600; }
  .cr-rule { width: 100%; height: 1px; background: #1e1e1e; margin-bottom: 20px; }
  .notice { font-family: system-ui, sans-serif; font-size: 13.5px; color: #9a9a9a; line-height: 1.8; margin-bottom: 16px; }
  .notice em { font-style: italic; }
  .isbn-line { font-family: system-ui, sans-serif; font-size: 11px; color: #5a5a5a; letter-spacing: 0.05em; margin-top: 20px; }"""

NEW_CR_CSS = """  /* ═══════════════════════════════════════
     COPYRIGHT
  ═══════════════════════════════════════ */
  .copyright-block { position: absolute; bottom: 0; left: 0; right: 0; }
  .copyright-line { font-family: system-ui, sans-serif; font-size: 11px; color: #f5f5f5; line-height: 1.7; margin-bottom: 20px; }
  .copyright-line strong { color: #f5f5f5; font-weight: 600; }
  .cr-rule { width: 100%; height: 1px; background: #1e1e1e; margin-bottom: 20px; }
  .notice { font-family: system-ui, sans-serif; font-size: 10px; color: #9a9a9a; line-height: 1.8; margin-bottom: 16px; }
  .notice em { font-style: italic; }
  .isbn-line { font-family: system-ui, sans-serif; font-size: 10px; color: #5a5a5a; letter-spacing: 0.05em; margin-top: 20px; }"""

if OLD_CR_CSS in html:
    html = html.replace(OLD_CR_CSS, NEW_CR_CSS)
    print('3. Copyright CSS font sizes corrected.')
else:
    print('WARNING 3: copyright CSS block not found.')

# ─────────────────────────────────────────────────────────────────────────────
# 4.  FIX TOC FONT SIZES
# ─────────────────────────────────────────────────────────────────────────────
OLD_TOC_CSS = """  /* ═══════════════════════════════════════
     TOC
  ═══════════════════════════════════════ */
  .toc-heading { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 36px; font-weight: bold; color: #f5f5f5; margin-bottom: 24px; letter-spacing: -0.01em; }
  .toc-rule { width: 100%; height: 1px; background: #1e1e1e; margin-bottom: 22px; }
  .toc-item { display: flex; align-items: baseline; margin-bottom: 8px; }
  .toc-item-label { font-size: 13.5px; color: #9a9a9a; white-space: nowrap; }
  .toc-dots { flex: 1; border-bottom: 1px dotted #2a2a2a; margin: 0 8px 3px; }
  .toc-page { font-size: 12px; color: #5a5a5a; white-space: nowrap; font-style: italic; }
  .toc-section { margin: 18px 0 10px; }
  .toc-section-label { font-size: 9px; letter-spacing: 0.28em; text-transform: uppercase; color: #5a5a5a; }
  .toc-chapter { display: flex; align-items: baseline; margin-bottom: 7px; }
  .toc-ch-num { font-size: 11px; color: #3a3a3a; min-width: 28px; }
  .toc-ch-label { font-size: 12px; color: #d0d0d0; white-space: nowrap; }
  .toc-ch-dots { flex: 1; border-bottom: 1px dotted #2a2a2a; margin: 0 8px 3px; }
  .toc-ch-page { font-size: 12px; color: #5a5a5a; white-space: nowrap; font-style: italic; }
  .toc-continued { font-size: 9px; letter-spacing: 0.22em; text-transform: uppercase; color: #5a5a5a; margin-bottom: 18px; }"""

NEW_TOC_CSS = """  /* ═══════════════════════════════════════
     TOC
  ═══════════════════════════════════════ */
  .toc-heading { font-family: "Didot","GFS Didot","Bodoni 72","Bodoni MT","Playfair Display",Georgia,serif; font-size: 36px; font-weight: bold; color: #f5f5f5; margin-bottom: 24px; letter-spacing: -0.01em; }
  .toc-rule { width: 100%; height: 1px; background: #1e1e1e; margin-bottom: 22px; }
  .toc-item { display: flex; align-items: baseline; margin-bottom: 8px; }
  .toc-item-label { font-family: system-ui,sans-serif; font-size: 11px; color: #9a9a9a; white-space: nowrap; }
  .toc-dots { flex: 1; border-bottom: 1px dotted #2a2a2a; margin: 0 8px 3px; }
  .toc-page { font-family: system-ui,sans-serif; font-size: 11px; color: #5a5a5a; white-space: nowrap; font-style: italic; }
  .toc-section { margin: 18px 0 10px; }
  .toc-section-label { font-family: system-ui,sans-serif; font-size: 9px; letter-spacing: 0.28em; text-transform: uppercase; color: #5a5a5a; }
  .toc-chapter { display: flex; align-items: baseline; margin-bottom: 7px; }
  .toc-ch-num { font-family: system-ui,sans-serif; font-size: 10px; color: #3a3a3a; min-width: 28px; }
  .toc-ch-label { font-family: system-ui,sans-serif; font-size: 11px; color: #d0d0d0; white-space: nowrap; }
  .toc-ch-dots { flex: 1; border-bottom: 1px dotted #2a2a2a; margin: 0 8px 3px; }
  .toc-ch-page { font-family: system-ui,sans-serif; font-size: 11px; color: #5a5a5a; white-space: nowrap; font-style: italic; }
  .toc-continued { font-family: system-ui,sans-serif; font-size: 9px; letter-spacing: 0.22em; text-transform: uppercase; color: #5a5a5a; margin-bottom: 18px; }"""

if OLD_TOC_CSS in html:
    html = html.replace(OLD_TOC_CSS, NEW_TOC_CSS)
    print('4. TOC CSS font sizes corrected.')
else:
    print('WARNING 4: TOC CSS block not found.')

# ─────────────────────────────────────────────────────────────────────────────
# 5.  FIX PART OPENER .part-desc FONT SIZE
# ─────────────────────────────────────────────────────────────────────────────
OLD_PART_DESC = '  .part-desc { font-size: 13.5px; line-height: 1.8; color: #9a9a9a; max-width: 420px; }'
NEW_PART_DESC = '  .part-desc { font-family: system-ui,sans-serif; font-size: 11px; line-height: 1.8; color: #9a9a9a; max-width: 420px; }'
if OLD_PART_DESC in html:
    html = html.replace(OLD_PART_DESC, NEW_PART_DESC)
    print('5. .part-desc font-size corrected: 13.5px -> 11px.')
else:
    print('WARNING 5: .part-desc rule not found.')

# ─────────────────────────────────────────────────────────────────────────────
# 6.  REPLACE SECTION 2 HTML (half-title) with section-file structure
# ─────────────────────────────────────────────────────────────────────────────
OLD_SEC2 = """<!-- ══════════════════════════════════════════════════════
     SECTION 2 — HALF-TITLE
     ══════════════════════════════════════════════════════ -->
<div class="section-divider">Section 2 — Half-Title</div>

<div class="page">
  <div class="page-inner">
    <div class="ht-volume">Volume I</div>
    <div class="ht-title">Analyzing Islam</div>
    <div class="ht-source-label">The Quran</div>
    <span class="running-page">i</span>
  </div>
</div>"""

NEW_SEC2 = """<!-- ══════════════════════════════════════════════════════
     SECTION 2 — HALF-TITLE
     ══════════════════════════════════════════════════════ -->
<div class="section-divider">Section 2 — Half-Title</div>

<div class="page">
  <div class="page-inner">
    <div class="half-title-block">
      <div class="book-title">Analyzing Islam</div>
      <div class="volume-label">Volume I</div>
      <div class="source-label">The Quran</div>
      <div class="ht-rule"></div>
    </div>
    <span class="running-page">i</span>
  </div>
</div>"""

if OLD_SEC2 in html:
    html = html.replace(OLD_SEC2, NEW_SEC2)
    print('6. Section 2 (half-title) HTML replaced with section-file structure.')
else:
    print('WARNING 6: section 2 HTML not found.')

# ─────────────────────────────────────────────────────────────────────────────
# 7.  REPLACE SECTION 3 HTML (title page) with section-file structure
# ─────────────────────────────────────────────────────────────────────────────
OLD_SEC3 = """<!-- ══════════════════════════════════════════════════════
     SECTION 3 — TITLE PAGE
     ══════════════════════════════════════════════════════ -->
<div class="section-divider">Section 3 — Title Page</div>

<div class="page">
  <div class="page-inner">
    <div class="title-block">
      <div class="title-main">Analyzing Islam</div>
      <div class="title-red-rule"></div>
      <div class="title-source-subtitle">The Quran</div>
      <div class="title-source-descriptor">A Critical Reference Guide</div>
    </div>
    <div class="title-colophon">
      <div class="title-colophon-rule"></div>
      <div class="title-colophon-row">
        <div class="title-colophon-text">analyzingislam.com</div>
        <div class="title-colophon-text">2026</div>
      </div>
    </div>
    <span class="running-page">ii</span>
  </div>
</div>"""

NEW_SEC3 = """<!-- ══════════════════════════════════════════════════════
     SECTION 3 — TITLE PAGE
     ══════════════════════════════════════════════════════ -->
<div class="section-divider">Section 3 — Title Page</div>

<div class="page">
  <div class="page-inner">
    <div class="title-block">
      <div class="main-title">Analyzing Islam</div>
      <div class="title-divider"></div>
      <div class="title-volume-line">Volume I</div>
      <div class="title-source-subtitle">The Quran</div>
      <div class="title-source-descriptor">A Critical Reference Guide</div>
    </div>
    <div class="title-colophon">
      <div class="title-colophon-rule"></div>
      <div class="title-colophon-site">analyzingislam.com</div>
      <div class="title-colophon-year">2026</div>
    </div>
    <span class="running-page">ii</span>
  </div>
</div>"""

if OLD_SEC3 in html:
    html = html.replace(OLD_SEC3, NEW_SEC3)
    print('7. Section 3 (title page) HTML replaced with section-file structure.')
else:
    print('WARNING 7: section 3 HTML not found.')

# ─────────────────────────────────────────────────────────────────────────────
# Write
# ─────────────────────────────────────────────────────────────────────────────
BOOK.write_text(html, encoding='utf-8')
print(f'\nDone. New length: {len(html):,}')
