#!/usr/bin/env python3
"""把 skill 的字体声明 + 指定主题 CSS 内联进预览版式，生成自包含单文件预览页。

用法：python3 scripts/gen-theme-preview.py <主题名> <中文名> <英文名> [输出html] [--dark|--aero]
例：  python3 scripts/gen-theme-preview.py century-sq 世纪广场 "Century Sq"
      python3 scripts/gen-theme-preview.py century-ave   世纪大道 "Century Ave" --dark
      python3 scripts/gen-theme-preview.py guanglan-rd   广兰路   "Guanglan Rd" --aero

默认输出：examples/previews/<主题名>-theme-preview.html（目录自动创建）

模板存在 skill 内部 scripts/preview-template.html，脚本自定位，不依赖工作区。
--dark  追加暗色预览版式覆盖（世纪大道：暖灯箱夜景）。
--aero  广兰路专用分支：
        1) 主题 CSS 里的 Google Fonts @import 提到 <style> 最前（CSS 规范要求），
           否则内联到样式表中段会被浏览器忽略；
        2) 补模板依赖但广兰路没有的 token 别名（--primary/--line-4 等）；
        3) 跳过世纪主题的按钮居中覆盖（广兰路 padding 10/14 本就正确，
           且 ::before 高光胶囊依赖按钮高度）；
        4) 跳过 Line 2 → Line 9 替换，并把 LINE 线路标签整体换成广兰路四色语义
           （Primary/Violet/Coral/Success；广兰路是 2 号线主题，不继承世纪的线路叙事）；
        5) 覆盖 body/board 硬编码背景与材质圆，回到 Aqua 蓝玻璃调；
        6) 换掉模板的世纪广场「概念层」：材质圆词与纹理（混凝土/大理石/钢 →
           玻璃/气泡/白瓷）、几何（模度 → 圆角/气泡）、导视栏目、卡片正文、
           浮层文案（磨砂不做折射 → Aqua 玻璃厚倒角强折射）、页眉 meta 与组件卡底纹。
"""
import importlib.util
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TPL = SKILL / 'scripts/preview-template.html'
DEFAULT_OUTDIR = SKILL / 'examples/previews'

PILL_ALIGN_OVERRIDE = r'''
/* ============ 按钮文字垂直居中（亮/暗世纪主题；总高与点击区域不变） ============
   字体基线排查：智造黑 line-height:normal 下字墨已居中，模板沿用的旧 CJK 行盒补偿
   （上 7/9、6/8、10/14）反而把字往上推 1px。改为对称内距，总和保持原值。 */
.pill,.pill-accent,.pill-good{padding-top:12px;padding-bottom:12px}
.board .pill{padding-top:8px;padding-bottom:8px}
.g-nav .pill{padding-top:7px;padding-bottom:7px}
'''

GHOST_BTN_OVERRIDE = r'''
/* ============ 次按钮＝描边幽灵（预览层；不改主题本体） ============
   主题 .cp-btn-2 是实心蓝，与主黄按钮并排时两枚满饱和互相抢层级，
   也违反主题自己写的铁则「单视图最多主色 + 一个次色」。次色只做描边与文字。 */
.cp-btn-2{
  color:var(--line-2);
  background:rgba(255,255,255,.72);
  border:1.5px solid var(--line-2);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.85);
}
'''

LIGHT_STEEL_OVERRIDE = r'''
/* ============ 亮色版不锈钢强化（仅世纪广场；与主题 cp-steel 共用 token） ============ */
.d-steel{
  background-color:var(--steel-mid);
  background-image:
    linear-gradient(108deg,transparent 0 14%,rgba(255,255,255,.62) 26%,rgba(255,255,255,.14) 33%,transparent 40% 60%,rgba(255,255,255,.34) 72%,transparent 82%),
    repeating-linear-gradient(90deg,
      rgba(255,255,255,.70) 0 .6px,
      rgba(96,108,118,.26) .6px 1.2px,
      rgba(255,255,255,.16) 1.2px 1.8px,
      transparent 1.8px 3px),
    linear-gradient(180deg,var(--steel-hi) 0%,#eef2f4 20%,var(--steel-mid) 50%,var(--steel-lo) 82%,#cfd7dc 100%);
  border-color:rgba(96,108,118,.46);
  box-shadow:inset 0 1px 0 var(--steel-rim),inset 0 -2px 4px rgba(96,108,118,.18),0 6px 14px rgba(30,44,56,.16);
}
'''

LIGHT_MARBLE_OVERRIDE = r'''
/* ============ 亮色版白大理石材质圆（仅世纪广场；与主题 cp-marble 同纹理，方案1） ============ */
.d-marble{
  background-color:var(--marble);
  background-image:
    radial-gradient(at 30% 20%,rgba(255,255,255,.70) 0px,transparent 50%),
    radial-gradient(at 80% 70%,rgba(241,245,249,.50) 0px,transparent 50%),
    /* 脉纹在 82px 圆里必须够粗够深，否则整枚读成白球 */
    linear-gradient(125deg,transparent 42%,rgba(120,126,130,.34) 46%,rgba(120,126,130,.10) 50%,transparent 54%),
    linear-gradient(-45deg,transparent 34%,rgba(120,126,130,.24) 42%,rgba(255,255,255,.70) 50%,transparent 58%);
  background-size:100% 100%,100% 100%,120px 120px,96px 96px;
}
'''


# ============================================================================
# 友谊大厦 Friendship Bldg —— 预览板专属覆盖
# 主题本体（assets/themes/friendship-bldg.css）已把 token 与组件写全，这里只做三件事：
#   1) 把预览板的「世纪广场硬编码」换成友谊大厦的语汇（色板 / 材质 / 几何 / 页眉）
#   2) 修掉预览页专用版式里 body 背景的硬编码（它排在主题之后，会盖掉米黄底）
#   3) 材质圆改用主题自带的 .fb-* 材质，不再借用混凝土/大理石/钢
# ============================================================================
FRIENDSHIP_OVERRIDE = r"""
/* ---- 预览页底色：模板 body 硬编码 #e9eef3 排在主题之后，必须让位 ---- */
body{background:linear-gradient(180deg,#f7efdd 0%,#f2e8d2 46%,#efe4cb 100%)}
.wrap{color:var(--text-1)}

/* ---- 色板：鎏金主色 + 红玻璃 + 墨绿 + 薄荷，比例按主题铁则「鎏金为主，次色小面积」---- */
.spec-bar{box-shadow:inset 0 0 0 1px rgba(90,74,48,.22),0 5px 12px rgba(80,62,30,.10)}
.spec-bar i + i{box-shadow:inset 1px 0 0 rgba(251,246,236,.72)}
.spec-legend .r1 i{border:1px solid rgba(90,74,48,.24)}
.spec-legend b,.spec-legend span{font-family:var(--font-mono)}
.spec-legend em{color:var(--text-3)}

/* ---- 材质圆：换成友谊大厦自己的六种实景材质 ---- */
.mat .disc{
  border-radius:50%;
  border:1px solid rgba(90,74,48,.20);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.70),0 6px 16px rgba(80,62,30,.12);
}
/* 统一镜面弧收窄，只占左上一条，不洗白材质本色 */
.mat .disc::after{
  background:
    radial-gradient(circle at 30% 20%,rgba(255,255,255,.34) 0,rgba(255,255,255,.07) 16%,transparent 30%),
    radial-gradient(circle at 74% 86%,rgba(80,62,30,.14) 0,transparent 52%);
}
/* 1 乳黄水刷石 */
.d-concrete{
  background-color:var(--stone);
  background-image:
    var(--fb-grain),
    var(--fb-grain),
    radial-gradient(ellipse 5px 4px at 24% 32%,rgba(120,96,60,.14) 0%,rgba(120,96,60,0) 100%),
    radial-gradient(ellipse 4px 5px at 71% 74%,rgba(120,96,60,.12) 0%,rgba(120,96,60,0) 100%),
    linear-gradient(180deg,rgba(255,255,255,.30),rgba(214,190,147,.20));
  background-size:96px 96px,58px 58px,97px 89px,73px 101px,auto;
}
/* 2 汉白玉台基：脉纹加粗到 82px 圆里能看见（原 2% 宽度几乎不可辨） */
.d-marble{
  background-color:var(--marble);
  background-image:
    linear-gradient(112deg,transparent 0 26%,rgba(150,138,112,.34) 28%,rgba(150,138,112,.10) 33%,transparent 36% 56%,rgba(150,138,112,.24) 58%,transparent 62%),
    linear-gradient(96deg,transparent 0 62%,rgba(150,138,112,.18) 64%,transparent 68%),
    radial-gradient(120% 90% at 30% 10%,rgba(255,255,255,.92),rgba(255,255,255,0) 62%),
    linear-gradient(180deg,#fffdf8,#f2ebdc);
}
/* 3 鎏金塔身 */
.d-steel{
  background-color:var(--gold);
  background-image:
    linear-gradient(104deg,rgba(255,255,255,0) 28%,rgba(255,255,255,.34) 46%,rgba(255,255,255,0) 64%),
    linear-gradient(180deg,#e8d086 0%,#cda845 38%,#b08a2b 74%,#8a6a18 100%);
  border-color:rgba(90,66,10,.40);
}
/* 4 彩色水磨石地坪：石子必须放大到 82px 圆里能数出来（原 170px 平铺只剩半块） */
.d-frost{
  background-color:var(--terrazzo);
  background-image:
    radial-gradient(circle 5px at 22% 28%,rgba(176,138,43,.55) 0 100%,transparent 100%),
    radial-gradient(circle 4px at 62% 18%,rgba(156,34,38,.42) 0 100%,transparent 100%),
    radial-gradient(circle 6px at 78% 62%,rgba(62,110,88,.48) 0 100%,transparent 100%),
    radial-gradient(circle 4px at 34% 74%,rgba(120,96,60,.40) 0 100%,transparent 100%),
    radial-gradient(circle 3px at 52% 46%,rgba(176,138,43,.38) 0 100%,transparent 100%),
    radial-gradient(circle 5px at 14% 58%,rgba(62,110,88,.34) 0 100%,transparent 100%),
    radial-gradient(circle 3px at 86% 34%,rgba(120,96,60,.34) 0 100%,transparent 100%),
    radial-gradient(circle 4px at 44% 90%,rgba(156,34,38,.30) 0 100%,transparent 100%),
    var(--fb-grain),
    linear-gradient(180deg,#dfe6d8,#c9d3c4);
  background-size:auto,auto,auto,auto,auto,auto,auto,auto,150px 150px,auto;
  border-color:rgba(90,110,84,.30);
}
/* 5 薄荷绿穹顶：四十道辐射在 82px 圆里会糊成一片，改成 8 道可数的金肋 */
.d-tile{
  background-color:var(--mint);
  background-image:
    repeating-conic-gradient(from 0deg at 50% 92%,
      rgba(176,138,43,.42) 0deg 1.6deg,transparent 1.6deg 22.5deg),
    radial-gradient(88% 56% at 50% 6%,rgba(255,255,255,.88) 0%,rgba(255,255,255,0) 58%),
    radial-gradient(96% 92% at 50% 44%,rgba(62,110,88,0) 38%,rgba(62,110,88,.26) 100%);
  border-color:rgba(62,110,88,.30);
}
/* 6 红玻璃五角星：真五角星。原先旋转 45° 的方块读作菱形，不是星。
   .mat .disc 的 border-radius:50% 与 ::after 高光都要压掉，否则星被裁成圆。
   用 clip-path 切星形，金边靠 drop-shadow 描一圈（clip-path 吃 border）。 */
.mat .disc.d-square{
  --fb-star-shape:polygon(50% 0%,61.8% 34.5%,98% 34.5%,68.6% 56.6%,79.4% 90.5%,50% 69.4%,20.6% 90.5%,31.4% 56.6%,2% 34.5%,38.2% 34.5%);
  background:linear-gradient(180deg,#c23a36 0%,#9c2226 46%,#6f1013 100%);
  border:none;
  border-radius:0;
  transform:scale(.96);
  clip-path:var(--fb-star-shape);
  filter:drop-shadow(0 0 1px rgba(176,138,43,.95)) drop-shadow(0 3px 6px rgba(156,34,38,.30));
}
/* 星面不要圆形高光弧，会读成球 */
.mat .disc.d-square::after{background:none}
/* 7 白桦木饰面 */
.d-lawn{
  background-color:var(--stone-deep);
  background-image:
    repeating-linear-gradient(92deg,rgba(255,255,255,.42) 0 1px,rgba(120,96,60,.16) 1px 2px,rgba(255,255,255,.18) 2px 4px,transparent 4px 7px),
    linear-gradient(180deg,#e6d4b0,#c9ab7c);
  border-color:rgba(120,96,60,.30);
}
/* 8 漫射顶光（暖白，不刺眼） */
.d-day{
  background:
    radial-gradient(circle at 32% 22%,rgba(255,255,255,.96),transparent 46%),
    linear-gradient(158deg,#fdf6e6 0%,#f4e6c8 52%,#e8d3aa 100%);
  border-color:rgba(90,74,48,.20);
}

/* ---- 模度阶梯：最长条（100）必须是主色鎏金，越短越轻。
   原顺序把最浅的乳黄给了最长条，主次颠倒，读作「越重要越淡」。 ---- */
.mod-scale .ms:nth-child(1) i{background:linear-gradient(90deg,var(--gold-lo),var(--gold))}
.mod-scale .ms:nth-child(2) i{background:var(--gold-hi)}
.mod-scale .ms:nth-child(3) i{background:var(--mint)}
.mod-scale .ms:nth-child(4) i{background:var(--terrazzo-deep)}
.geo-grid i{background:var(--stone);border-color:rgba(90,74,48,.18)}
.geo-grid i.on{background:var(--gold);border-color:rgba(90,66,10,.40)}
.geo-grid i.gl{background:rgba(156,34,38,.16);border-color:rgba(156,34,38,.42)}

/* ---- 组件：次按钮 ----
   主题本体（friendship-bldg.css）已给出完整的 .cp-btn-2 规则（display / padding / 色值）。
   预览层不要再写一条只含颜色的同名规则——它排在主题之后，会把 padding 与 display
   整套盖掉，按钮塌成 26px 高、文字贴边。这里只做必要的尺寸微调。 */
/* 分类标签用墨绿 accent-3（图例里已声明「分类标签用墨绿」）；
   红玻璃 accent-2 只留给警示与星标，不能拿来当分类色，否则图例与实物自相矛盾。 */
/* 分类标签：模板给的是 999px 胶囊，与主题铁则「直角为主」冲突，改 --radius-lg。
   字体也换成按钮字体栈——标签是 UI 元素，不是正文，不该走宋体。 */
/* 分类标签：模板给的是 999px 胶囊 + 宋体 + 700 伪粗，三样都与主题铁则冲突
   （直角为主 / UI 元素走黑体 / 智造黑单字重禁伪粗）。用 !important 压过模板。 */
.tag-chip{background:var(--accent-3);color:#fff;box-shadow:0 3px 8px rgba(62,110,88,.22);
  border-radius:var(--radius)!important;font-family:var(--font-button)!important;
  font-weight:400!important;font-size:12px;letter-spacing:.04em}
.pill-ghost{color:var(--gold-lo);background:rgba(255,253,248,.92);border:1.5px solid rgba(176,138,43,.80);box-shadow:none}
.pill-ghost::before{display:none}

/* ---- 面板 / 卡片：乳黄石墙底 + 汉白玉面，直角为主 ---- */
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow)}
.sec-h{color:var(--text-2)}
.titlebar{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius)}

/* ---- 02 组件规范卡：模板的混凝土灰底 + 点阵是世纪广场语汇，换成乳黄石墙 ---- */
.spec-cell{
  background:
    radial-gradient(rgba(120,96,60,.05) .7px,transparent .7px) 0 0/4px 4px,
    linear-gradient(180deg,#f4ebd6,#eee2c7);
  border:1px solid rgba(90,74,48,.16);
  box-shadow:0 6px 14px rgba(80,62,30,.08);
}
/* 磨砂玻璃面板：主题铁则明令禁止强折射玻璃，换成汉白玉嵌板 */
.glass{
  background:linear-gradient(180deg,#fffdf8 0%,#f7f0e0 58%,#f0e6d0 100%);
  -webkit-backdrop-filter:none;backdrop-filter:none;
  border:1px solid rgba(176,138,43,.42);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.92),0 4px 12px rgba(80,62,30,.10);
}
.glass .sub{color:var(--text-2)}

/* ---- 几何网格：中轴对称（镜像），不是随机散布 ---- */
.geo-grid i{background:var(--stone);border-color:rgba(90,74,48,.18)}
.geo-grid i.on{background:var(--gold);border-color:rgba(90,66,10,.40)}
.geo-grid i.gl{background:rgba(62,110,88,.18);border-color:rgba(62,110,88,.44)}

/* ---- 警示条：红玻璃只做细条，不铺大面积。
   模板只在 .comp-row 里给了尺寸，02 屏的 .spec-cell 里没有，会渲染成 0 高。 ---- */
.cp-alert{width:150px;height:6px;border-radius:0;background:var(--accent-2)}
.comp-row .cp-alert{width:112px;height:6px;border-radius:0}

/* ============ 苏联时期艺术构成层（2026-11-20） ============
   取什么、拒什么，先说清楚：

   友谊大厦是斯大林式（社会主义现实主义），铁律是「严格中轴对称、直角为主」。
   构成主义（Rodchenko / Lissitzky）的核心构图原则恰恰是「对角线 + 不对称 +
   红黑对立」——直接照搬会和主题铁律打架，把中轴拆掉。所以不搬构图，只搬三样：

   取 1｜几何纪律：构成主义把画面还原为矩形、圆、直线的精确关系，反对装饰性曲线。
        落到这里 = 模度阶梯与几何网格必须读作「结构」，不是「花纹」。
   取 2｜结构诚实：骨架露出来，不贴假装饰。落到这里 = 檐带与柱列按结构逻辑排，
        不做无意义的重复纹样。
   取 3｜装饰母题：斯大林式把古典形式与苏维埃符号并置（五角星、谷穗、镰刀锤子，
        见 Stalinist architecture 的装饰清单）。落到这里 = 五角星 + 谷穗檐带 +
        阶梯收分（wedding-cake silhouette）。

   拒 1｜对角线构图：会破坏中轴对称。
   拒 2｜红黑对立：红玻璃是 accent-2 小面积标记，黑会压掉鎏金主色。
   拒 3｜构成主义的「绘画已死」式平涂：这里要的是石墙与鎏金的材质层次。

   历史依据：后构成主义（Postconstructivism, 1932–1938）正是这条缝——保留构成主义
   的矩形体量与几何精确，同时叠加古典柱廊与装饰。友谊大厦是这条线的产物。 ---- */

/* 标题台的角标：模板是 16px 实心方块（世纪广场的铺装语汇）。
   换成五角星——斯大林式塔顶的符号，小面积、只做标记。 */
/* 星形在 12–14px 时五个尖角被抗锯齿吃掉，读作模糊红点。标题台提到 20px。 */
.titlebar .mark{
  width:20px;height:20px;background:none;
  --fb-star-shape:polygon(50% 0%,61.8% 34.5%,98% 34.5%,68.6% 56.6%,79.4% 90.5%,50% 69.4%,20.6% 90.5%,31.4% 56.6%,2% 34.5%,38.2% 34.5%);
  clip-path:var(--fb-star-shape);
  background:linear-gradient(180deg,#c23a36,#8a1a1e);
  filter:drop-shadow(0 0 1px rgba(176,138,43,.9));
}
/* 导览头空间小，给 16px——再小就读不出星形。 */
.g-head .mark{
  width:16px;height:16px;background:none;
  --fb-star-shape:polygon(50% 0%,61.8% 34.5%,98% 34.5%,68.6% 56.6%,79.4% 90.5%,50% 69.4%,20.6% 90.5%,31.4% 56.6%,2% 34.5%,38.2% 34.5%);
  clip-path:var(--fb-star-shape);
  background:linear-gradient(180deg,#c23a36,#8a1a1e);
  filter:drop-shadow(0 0 1px rgba(176,138,43,.9));
}

/* 几何网格：模板是 6 列 × 2 行随机散布的 on/gl 格，读作噪声。
   构成主义的纪律是「关系必须可读」——改成中轴镜像的对称构图：
   中央两列为主轴（鎏金实心），两侧逐级退为描边，最外两列留空。
   这样读作「立面开间」，不是「随机铺装」。 */
.geo-grid{
  grid-template-columns:repeat(8,1fr);
  gap:4px;
}
.geo-grid i{height:20px;background:var(--stone);border:1px solid rgba(90,74,48,.16)}
/* 中轴两列：鎏金实心 */
.geo-grid i.on{background:var(--gold);border-color:rgba(90,66,10,.42)}
/* 次轴两列：金描边幽灵 */
.geo-grid i.gl{background:rgba(176,138,43,.10);border-color:rgba(176,138,43,.52)}
/* 外翼：墨绿细边（结构线，不是装饰） */
.geo-grid i.wing{background:rgba(62,110,88,.07);border-color:rgba(62,110,88,.34)}

/* 模度阶梯：构成主义把比例当结构。加一条中轴基准线，
   让四条读作「同一模度的四个刻度」，不是四根孤立的条。 */
.mod-scale{position:relative}
.mod-scale::before{
  content:"";position:absolute;left:0;top:-2px;bottom:-2px;width:1px;
  background:rgba(176,138,43,.46);pointer-events:none;
}
.mod-scale .ms b{font-family:var(--font-mono);letter-spacing:.04em}

/* 谷穗檐带：斯大林式装饰母题（ears of corn）。只挂在标题台下方，
   不横贯整板——整板横贯会读作条码。节奏放宽到 34px，读作檐口花饰。 */
.titlebar{position:relative}
.titlebar .rule{display:none}
.titlebar::after{
  content:"";position:absolute;left:24px;right:24px;bottom:-8px;height:7px;
  border-top:1px solid rgba(176,138,43,.50);
  background:
    repeating-linear-gradient(90deg,
      rgba(176,138,43,.44) 0 1px,transparent 1px 9px,
      rgba(176,138,43,.26) 9px 11px,transparent 11px 17px,
      rgba(176,138,43,.44) 17px 18px,transparent 18px 34px),
    linear-gradient(180deg,rgba(176,138,43,.14),rgba(176,138,43,.02));
  pointer-events:none;
}

/* ---- 第三屏天际线：模板是世纪广场的城市轮廓（28 个错落方盒），
   友谊大厦是严格中轴对称的塔楼群。原 svg 由生成器整段替换成 .fb-skyline。 ---- */
.skyline{display:none}
.fb-skyline{
  position:absolute;left:50%;bottom:14px;transform:translateX(-50%);
  width:700px;height:104px;z-index:0;opacity:.24;pointer-events:none;
}
/* 第三屏浮层：模板绝对定位在 left:392px，压住中间卡片正文；
   原先改成 right:32px/top:312px 也仍在卡片行内（卡片自 186 起、高 252），
   实际压住「提示信息」卡的正文。改挂到面板下缘之外，浮在天际线上方，
   既演示汉白玉嵌板材质，又不压任何正文。
   ⚠️ 2026-11-20 补校准：原 top:442 距卡片行底边（440）只有 2px，实测含描边 4px，
   比模板的 8px 紧一半，读作「贴着」而不是「浮起」。改 448，与模板净距对齐。 */
.g-modal{
  left:auto;right:32px;top:448px;width:236px;height:118px;
  padding:12px 16px;
  background:linear-gradient(180deg,#fffdf8 0%,#f7f0e0 58%,#f0e6d0 100%);
  -webkit-backdrop-filter:none;backdrop-filter:none;
  border:1px solid rgba(176,138,43,.44);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.92),0 10px 26px rgba(80,62,30,.16);
}
.g-modal h4{font-weight:400;font-size:15px;margin:2px 0 1px}
.g-modal .sub{font-size:12px;letter-spacing:.06em}
.g-modal p{font-size:12px;line-height:1.6;margin:4px 0 0}
.g-modal .x{top:6px;right:12px;font-size:14px}

/* 彩虹光斑：模板 .g-glow 是玫红/蓝/黄三色径向渐变，那是世纪广场的彩色玻璃概念。
   友谊大厦没有彩色光，删掉（保留元素但清空背景，不动 DOM 结构）。 */
.g-glow{background:none}

/* 分类标签：模板 .g-card .tag 用 --line-4（紫），而友谊大厦主题里没有 --line-4，
   背景会解析成透明。必须用同等或更高的选择器压回去。 */
.tag,
/* 卡内分类标签：模板给 999px 胶囊 + 宋体 + 700 伪粗，与主题「直角为主 / UI 走黑体」冲突。
   圆角与字重必须带 !important 才压得过模板的 .g-card .tag 规则。 */
.g-card .tag{background:var(--accent-3);color:#fff;font-weight:400!important;
  border-radius:var(--radius)!important;font-family:var(--font-button)!important;
  letter-spacing:.04em}
/* 提示卡顶条：模板用 --line-6（玫红），换成红玻璃 accent-2 */
.g-card.alert-card{border-top:3px solid var(--accent-2)}
/* 导览面板本体：模板是半透明冷蓝，换成乳黄石墙 */
.guide-panel{
  background:linear-gradient(180deg,rgba(249,243,228,.94),rgba(239,228,203,.94));
  border:1px solid rgba(90,74,48,.18);
  box-shadow:0 22px 48px rgba(80,62,30,.16);
}
.g-head{background:linear-gradient(180deg,#fdf9f0,#f4ebd6)}
.g-nav{background:linear-gradient(180deg,#f7efdd,#efe4cb)}
.g-card{background:linear-gradient(180deg,#fffdf8,#f8f1e2);border:1px solid rgba(176,138,43,.28)}
.g-foot{color:var(--text-3)}

/* ---- 环境层：模板 .deck 是「浅蓝天光 + 底部草绿带」，那是世纪广场的公园概念。
   友谊大厦换成「乳黄石墙漫射 + 底部一道彩色水磨石剖带 + 金线门槛」。
   注意：模板的草地带挂在 .deck::after（不是 ::before），必须按实际选择器覆盖。 ---- */
.deck{
  background:
    radial-gradient(120% 44% at 50% -10%,rgba(255,255,255,.94) 0%,rgba(251,246,236,.52) 46%,rgba(251,246,236,0) 76%),
    linear-gradient(180deg,rgba(247,239,221,.58) 0%,rgba(242,232,210,.62) 40%,rgba(239,228,203,.66) 74%,rgba(236,224,198,.70) 100%),
    var(--fb-terrazzo-tile),
    linear-gradient(180deg,#f7efdd 0%,#f2e8d2 40%,#efe4cb 74%,#ece0c6 100%);
  background-size:auto,auto,110px 110px,auto;
}
/* 板面本体：模板 .board 是「浅蓝天光 + 底部草绿带」，那是世纪广场的公园概念。
   友谊大厦改成「彩色水磨石主背景」——上海展览中心的门厅与回廊就是水磨石地坪，
   用户点名要它当主背景。关键是压对比：石子只做低对比暗示，不压字。
   做法：乳黄半透明罩层盖在水磨石铺贴片之上，罩层 76–82% 不透明度，
   石子仍可见但退成肌理，正文对比度不受影响。 */
.board{
  background:
    linear-gradient(180deg,rgba(249,243,228,.54) 0%,rgba(244,235,214,.58) 42%,rgba(239,228,203,.62) 100%),
    var(--fb-terrazzo-tile),
    linear-gradient(180deg,#f9f3e4 0%,#f4ebd6 42%,#efe4cb 100%);
  background-size:auto,110px 110px,auto;
  border:1px solid rgba(90,74,48,.16);
  box-shadow:0 22px 54px rgba(80,62,30,.14);
}
/* 下角两块瓷砖网格是模板的 .tile-corner.cp-tile 元素（不是 .deck 伪元素）。
   它们带 cp-tile 类，会被上面的薄荷穹顶规则染成两块绿方块，读作贴纸。
   友谊大厦没有公园铺装语汇，换成水磨石地坪收口：只留骨料，压淡，读作地面。 */
.tile-corner.cp-tile{
  background-color:transparent;
  background-image:
    var(--fb-terrazzo-tile),
    linear-gradient(180deg,rgba(239,228,203,0) 0%,rgba(239,228,203,.90) 58%,rgba(236,224,198,.96) 100%);
  background-size:110px 110px,auto;
  opacity:.46;
}

/* 底部草地带 -> 鎏金门槛线。
   水磨石已经升为主背景，原来那条 14px 水磨石剖带就重复了，改成一道门槛：
   1px 金线 + 3px 渐隐，读作「地坪收口」，不吞页脚。 */
.board::after{
  content:"";position:absolute;left:0;right:0;bottom:0;height:4px;z-index:1;pointer-events:none;
  background:linear-gradient(180deg,rgba(176,138,43,.52) 0 1px,rgba(176,138,43,.10) 1px 2px,rgba(176,138,43,0) 2px);
}
/* 第三屏导览面板：模板是浅蓝天空，换成乳黄石墙 */
.guide-board{
  background:
    linear-gradient(180deg,rgba(247,239,221,.58) 0%,rgba(242,232,210,.62) 34%,rgba(239,228,203,.66) 72%,rgba(236,224,198,.70) 100%),
    var(--fb-terrazzo-tile),
    linear-gradient(180deg,#f7efdd 0%,#f2e8d2 34%,#efe4cb 72%,#ece0c6 100%);
  background-size:auto,110px 110px,auto;
}
"""

QIU_OVERRIDE = r"""
/* ============ 虬江预览适配（学术纸面，仅 qiu-r）============
   模板的几何全部保留，只把材质与色换掉：黄/紫/玫红 → 河青/靛蓝/砖红，
   混凝土/钢/草坪圆盘 → 青砖/河埠石/河面水线/方格稿纸方片。 */
body{
  background-color:var(--bg);
  background-image:
    radial-gradient(120% 40% at 50% -8%,rgba(255,255,255,.94),rgba(226,232,224,.50) 46%,rgba(226,232,224,0) 76%),
    repeating-linear-gradient(0deg,transparent 0 25px,rgba(29,36,33,.020) 25px 26px),
    repeating-linear-gradient(90deg,transparent 0 25px,rgba(29,36,33,.016) 25px 26px);
}
.g-glow{background:none}
.titlebar{background:#fbfaf3;border-bottom:1px solid var(--border);box-shadow:none}
.titlebar .mark{background:var(--water);border-radius:1px}
.titlebar .rule{background:var(--water);height:2px}
.lead h1{font-family:var(--font-display);font-weight:400;color:var(--text-1)}
.lead .sub{color:var(--text-2)}
.spec-title .rule{background:var(--water);height:2px}
.spec-title h2{font-family:var(--font-display);font-weight:400}
/* 材质圆一律改方片：纸、砖、石都是直角，圆盘读作另一套年代 */
.mat .disc{border-radius:2px;box-shadow:inset 0 0 0 1px rgba(29,36,33,.18)}
.mat .disc::after{background:none}
.mat .n{color:var(--text-3)}
.pill-ghost{color:var(--water-lo);background:rgba(251,250,243,.92);border:1px solid rgba(60,117,126,.55);box-shadow:none}
.tag-chip{background:var(--brick);color:#fbf3e9}
/* 导览面板：整块换纸面，不加毛玻璃 */
.guide-panel{background:var(--surface);border:1px solid var(--border);box-shadow:0 18px 40px rgba(29,36,33,.10)}
.g-head .mark{background:var(--brick);border-radius:1px}
.g-head .rule{background:var(--water);height:2px}
.g-card{background:var(--surface-2);border:1px solid var(--border);border-radius:2px;box-shadow:inset 0 1px 0 #fff}
.g-card h3{font-family:var(--font-display);font-weight:400}
.g-card p{color:var(--text-2)}
.g-card .note{color:var(--text-3)}
.g-card .tag{background:var(--brick);color:#fbf3e9;font-weight:400}
.g-card.alert-card{border-top:3px solid var(--brick)}
.g-modal{background:var(--surface);border:1px solid var(--border);border-radius:2px;box-shadow:0 18px 40px rgba(29,36,33,.12)}
.g-modal p{color:var(--text-1)}
.g-modal .x,.g-modal .sub{color:var(--text-2)}
.g-foot{color:var(--text-3)}
/* 环境层：模板 .board 是「浅蓝天光 + 底部草绿带」，那是世纪广场的公园概念。
   虬江换成纸面 + 底部河面水线带（横向等距细线，本主题的几何母题）。 */
.board{background:linear-gradient(180deg,#fbfaf3 0%,#f6f2e4 46%,#f4f1e7 100%)}
.board::after{
  height:52px;
  background:
    repeating-linear-gradient(0deg,rgba(60,117,126,.20) 0 1px,transparent 1px 6px),
    linear-gradient(180deg,rgba(60,117,126,.10),rgba(42,84,92,.16));
  border-top:1px solid rgba(60,117,126,.34);
}
.guide-board{background:linear-gradient(180deg,#fbfaf3 0%,#f6f2e4 40%,#efebde 100%)}
/* 圆角：模板 .board .card{6px} / .board .glass{14px} 是世纪广场的直角语法，
   选择器优先级(0,2,0) 高过主题的 .g-card(0,1,0)，会把纸面直角顶回去。
   纸、砖、石都是直角，14px 圆角浮层读作另一套年代——这里按主题收回 2px。 */
.board .card,.board .g-card{border-radius:2px}
.board .glass,.board .g-modal{border-radius:2px}
/* 字号：模板把材质名压到 9.5px、图注压到 10px——1080px 板上中文 9.5px 已不可读，
   且 12/16 两档挤在 25% 级差线内（浮龟「相邻级差 ≥25%」）。中文最小 12px 起。 */
.mat .n{font-size:12px;letter-spacing:0}
.sec-h{font-size:12px}
.g-foot{font-size:12px}
.g-card .note{font-size:12px}
.spec-legend .lg em{font-size:12px}
.spec-legend .lg span{font-size:12px}
.g-modal .sub{font-size:12px}
.spec-cell .glass .sub{font-size:12px}
"""


WANHANG_OVERRIDE = r"""
/* ============ 万航渡预览适配（纸绘动画，仅 wanhang-fy）============
   模板的环境层是三件「别的年代」：蓝渐变天空、56px 硬边草坪带、钢面导航与
   半透明玻璃面板。这里不换几何，只把它们翻成纸、水彩与缓坡——
   ⛔ 不给硬投影、不给玻璃模糊（那是番禺路的语汇）。 */
body{
  background-color:var(--bg);
  background-image:
    radial-gradient(120% 40% at 50% -10%,rgba(255,255,255,.90),rgba(214,226,224,.34) 48%,rgba(214,226,224,0) 78%),
    repeating-linear-gradient(90deg,transparent 0 2px,rgba(90,74,58,.028) 2px 3px),
    repeating-linear-gradient(0deg,transparent 0 2px,rgba(90,74,58,.020) 2px 3px);
}
.g-glow{background:radial-gradient(60% 60% at 50% 50%,rgba(159,188,198,.28),rgba(159,188,198,0) 72%)}
.lead{border-bottom:1.5px solid rgba(90,74,58,.22)}
.lead h1{font-family:var(--font-display);font-weight:400;color:var(--text-1)}
.titlebar{
  background:
    radial-gradient(90% 120% at 12% 0%,rgba(159,188,198,.20),rgba(159,188,198,0) 62%),
    var(--surface);
  border:1.5px solid rgba(90,74,58,.26);
  border-radius:10px;
  box-shadow:0 14px 30px rgba(70,55,40,.10);
}
.titlebar .mark{background:var(--lawn-lo);border-radius:60% 60% 55% 55%/70% 70% 40% 40%;box-shadow:0 2px 6px rgba(70,55,40,.18)}
.titlebar h2,.spec-title h2,.g-head h2,.g-card h3{font-family:var(--font-display);font-weight:400}
.titlebar .rule,.spec-title .rule{
  height:3px;border-radius:999px;
  background:linear-gradient(90deg,rgba(63,100,73,.92),rgba(63,100,73,.66) 58%,rgba(63,100,73,.24) 84%,rgba(63,100,73,0));
}
.spec-title .rule{height:3px}
/* 材质圆：柔边、棕灰细线、无镜面洗白 */
.mat .disc{
  border:1.5px solid rgba(90,74,58,.30);
  box-shadow:inset 0 1px 2px rgba(255,255,255,.55),0 10px 22px rgba(70,55,40,.10);
}
.mat .disc::after{background:radial-gradient(circle at 32% 22%,rgba(255,255,255,.30),transparent 34%)}
.mat .n{color:var(--text-3)}
.spec-cell{
  background:
    radial-gradient(90% 80% at 20% 0%,rgba(159,188,198,.12),rgba(159,188,198,0) 66%),
    var(--surface-2);
  border:1.5px solid rgba(90,74,58,.22);
  border-radius:var(--radius-sm);
  box-shadow:0 8px 20px rgba(70,55,40,.07);
}
.spec-cell.glass-cell::before{
  background:
    radial-gradient(circle at 30% 40%,rgba(139,163,112,.55),transparent 56%),
    radial-gradient(circle at 70% 60%,rgba(159,188,198,.60),transparent 56%),
    radial-gradient(circle at 55% 30%,rgba(166,127,92,.38),transparent 56%);
  filter:blur(7px);
}
/* ⚠️ 2026-11-21：模板 .panel 固定 height:150px，内容（两行 comp-row 39+64 + margin 8 + padding 22）
   刚好 133px。这里原写 border:1.5px，比模板的 1px 多占 1px，把 .mini-glass 底边顶出 panel 0.5px，
   浮层看着「掉」在边框线上。border 收回 1px，与模板同口径。 */
.panel{background:rgba(253,250,241,.62);border:1px solid rgba(90,74,58,.20);border-radius:var(--radius-sm)}
.pill-ghost{color:var(--text-1);background:rgba(253,250,241,.92);border:1.5px solid rgba(90,74,58,.34);box-shadow:none}
/* 分类标记＝河青底＋墨字（8.37:1）。⛔ 不用纸白字：河青对纸白字只有 1.85:1。
   这条与组件卡标签 CATEGORY / RIVER 必须一致——标签写什么色，实物就得是什么色。
   ⚠️ 2026-11-21：原写 var(--sky)/var(--umber)，是吉祥寺时期的 token 名，改名时漏改，
   两个变量在 wanhang-fy.css 里都不存在，分类标签因此丢了底色（透明）。
   吉祥寺 → 万航渡的映射：--sky → --river、--umber → --sepia、--grass-lo → --lawn-lo。 */
.tag-chip,.g-card .tag{background:var(--river);color:var(--sepia)}
/* 标题台挂角标记：模板是 16×16 方点。原写椭圆 radius（60%/70% 那串），16px 下读作
   一团模糊的绿斑，不像标记。万航渡的母题是「画稿纸上的定位角」，方点更贴。 */
.titlebar .mark,.g-head .mark{background:var(--lawn-lo);border-radius:2px}
/* 色阶条：本主题五个纸色相邻 ΔL* 只有 3–6（纸色阶本该如此，闸门的 chroma 门槛也放行），
   但并排 15×15 方块时边界读不出来。加一道深描边把「这是五个色」说清楚，不改色值。 */
.mini i{border:1px solid rgba(59,50,42,.34);box-shadow:inset 0 0 0 1px rgba(255,255,255,.55)}
/* 几何格：模板 .geo-grid i.gl 是 rgba(0,144,205,…) 亮蓝（世纪广场的玻璃幕墙概念），
   落在纸面上读作一块电子蓝，与「纸绘动画」完全无关。换成河青低透（本主题的水线色）。 */
.geo-grid i{background:var(--surface-2);border-color:rgba(59,50,42,.18)}
.geo-grid i.on{background:var(--plane);border-color:rgba(63,100,73,.46)}
.geo-grid i.gl{background:rgba(127,159,176,.22);border-color:rgba(127,159,176,.52)}
/* 卡片标题：走喜脉体（2026-11-21 用户定：h1–h3 一律喜脉体）。
   ⚠️ 两条历史坑，改这条前先读：
   ① 原写 var(--font-body)，但九个主题都没定义 --font-body（只有 --font-sans），
      声明被浏览器丢弃 → 字体走继承，既非喜脉也非正文，静默错。已改 --font-display。
   ② 手写体同字号下视觉比黑体/宋体小，24px 读着偏弱，故放大到 34px。
      原注释「24px 及以下走正文字体」的纪律已作废——用户要求 h3 也用手写体。 */
.g-card h3,.g-card h4{font-family:var(--font-display);font-weight:400;letter-spacing:0;font-size:34px}
/* 预览页 h1/h2 放大：主题的 104/78 档写在 `h1.title,.h1` 上，但预览页的
   h1/h2 没有 .title 类（模板直接写 <h1>/<h2>），主题档位一条都没命中，
   实际吃的是模板的 .lead h1{30px} / .titlebar h2{44px}。
   ⚠️ 手写体同字号视觉偏小，这里按主题档位的比例补上：
   .lead h1 是页眉小标（不是 hero），只微调到 40px；
   三个 h2 是真正的版面标题，44/36/34 → 60/52/46。 */
.lead h1{font-size:40px}
.titlebar h2{font-size:60px}
.spec-title h2{font-size:52px}
.g-head h2{font-size:46px}
/* ⚠️ 标题台高度必须跟着 h2 走。模板 .titlebar 是固定 height:104px，而 .rule
   用 position:absolute;bottom:12px 钉在底部——h2 从 44px 涨到 60px 后，内容
   高度 8.5+63.6+5+18.5≈96px 顶满 104px 的盒子，.en（WANHANG FY）被挤到底边，
   正好压在横条上（实测重叠 3px，2026-11-21）。
   改成 min-height + 底部留出横条净空：横条占 bottom:12px + 高 4px = 16px，
   再给 8px 呼吸，故 padding-bottom 24px。⛔ 别再用固定 height。 */
.titlebar{height:auto;min-height:132px;padding-bottom:24px}
.titlebar .rule{bottom:12px}
/* ⚠️ 2026-11-21：喜脉体（手写）下伸部大，行盒底边比墨迹低 6px——
   实测 60px 字号下 hhea ascent/descent = 1061/1173（upem 2048），
   基线在行盒 30.16px 处，墨迹底缘 57.56px，行盒却高 63.6px。
   模板原本 margin-top:5px 叠上去，视觉间隙变成 10.9px，读着「飘」。
   收到 -2px：视觉间隙 ≈ 4px，与手写体的墨迹贴合。
   ⛔ 这是手写体专属调整；黑体/宋体主题不需要，别抄到别处。 */
.titlebar .en{margin-top:-2px}
/* 另外两处标题台是同一个手写体、同一个 .en 结构，同样要收：
   .g-head 实测视觉间隙 8.5px（模板 margin-top:3px），收到 -1px → ≈4.5px；
   .spec-title 的 line-height 是 normal（量不出精确行盒），按同比例收到 0。 */
.g-head .en{margin-top:-1px}
.spec-title .en{margin-top:0}
/* 组件规范卡的标题台同理：模板 .spec-title 固定 height:96px，.rule 钉在 bottom:8px。
   h2 涨到 52px 后 .en 被推到底边压住横条（实测重叠，2026-11-21）。 */
.spec-title{height:auto;min-height:112px;padding-bottom:22px}
.spec-title .rule{bottom:8px}
/* 导览浮层：模板给 height:186px（世纪广场的四行文案刚好填满）。本主题文案只有三行，
   186px 里空掉近一半，读作一块空白卡。收到 150px，让内容与卡片同高。
   ⚠️ 2026-11-21：h4 涨到 26px 后内容 157px 装不下、溢出 10px（.x 与 h4 重叠）。
   改用 min-height —— 固定 height 在字号上调后必然溢出，这里只保证「不低于 150」。 */
.g-modal{height:auto;min-height:150px}
.g-head .rule{height:3px;border-radius:999px;background:linear-gradient(90deg,rgba(63,100,73,.92),rgba(63,100,73,.30) 76%,rgba(63,100,73,0))}
/* 环境三层：顶光＝暖纸晕，板底＝纸，底带＝缓坡草（柔边、无硬顶线）。
   ⚠️ 2026-11-21：顶光原写 rgba(196,214,220,.34)，是吉祥寺时期的冷调天光，落在纸面上
   读作一条淡蓝带，与「纸绘动画」的暖纸语汇打架。换成暖白→纸黄的晕，只提亮不加色。 */
.board{
  background:
    radial-gradient(120% 46% at 50% -6%,rgba(255,253,246,.90) 0%,rgba(240,232,214,.34) 46%,rgba(240,232,214,0) 76%),
    linear-gradient(180deg,#f8f4e8 0%,#f6f1e4 44%,#f1e9d7 100%);
  border:1.5px solid rgba(90,74,58,.22);
  box-shadow:0 24px 52px rgba(70,55,40,.14);
}
.board::after{
  height:64px;border-top:none;
  background:
    radial-gradient(40% 90% at 16% 132%,rgba(139,163,112,.55) 0 58%,rgba(139,163,112,0) 74%),
    radial-gradient(36% 84% at 52% 138%,rgba(109,133,86,.48) 0 56%,rgba(109,133,86,0) 74%),
    linear-gradient(180deg,rgba(139,163,112,0) 0%,rgba(139,163,112,.16) 48%,rgba(139,163,112,.34) 100%);
}
.board .card,.board .g-card{border-radius:var(--radius-sm)}
.board .glass,.board .g-modal{border-radius:var(--radius)}
.board .pill{border-radius:999px}
/* 导览浮层：模板定位是 top:446px / height:186px，整块落在面板外压着天际线（模板有意如此，
   八个主题一致）。但本主题面板与浮层同为纸面，同色相接读作「一块纸飘在草地上」，
   抬不起来。补一道纸边与更实的柔影，让浮层读作「压在纸上的一张卡」。 */
.g-modal{
  background:var(--surface);
  border:1.5px solid rgba(90,74,58,.30);
  box-shadow:0 20px 44px rgba(70,55,40,.16),0 4px 10px rgba(70,55,40,.08);
}
/* 浮层标题：同卡片，走喜脉体并放大一档（18px → 26px）。
   ⚠️ 原写 var(--font-body) 是死声明（主题无此 token），字体实际走继承。 */
/* ⚠️ 2026-11-21：h4 涨到 26px 后「导览信息」宽 203px，右缘压到右上角关闭按钮
   （实测横向重叠 10px）。给标题让出关闭按钮的净空：按钮 right:16px + 宽 16px
   = 32px，再留 8px 呼吸，故 padding-right 40px。 */
.g-modal h4{font-family:var(--font-display);font-weight:400;font-size:26px;padding-right:40px}
.g-modal .sub{color:var(--text-3)}
.g-modal .x{color:var(--text-2)}
/* 导览板顶光：同 .board，原 rgba(196,214,220,.30) 是吉祥寺的冷调天光，换暖纸晕。 */
.guide-board{
  background:
    radial-gradient(120% 42% at 50% -4%,rgba(255,253,246,.90),rgba(240,232,214,.30) 48%,rgba(240,232,214,0) 78%),
    linear-gradient(180deg,#f8f4e9 0%,#f6f1e4 48%,#efe6d3 100%);
}
.guide-panel{
  background:rgba(253,250,241,.96);backdrop-filter:none;
  border:1.5px solid rgba(90,74,58,.30);
  border-radius:var(--radius);
  box-shadow:0 26px 56px rgba(70,55,40,.14);
}
.g-nav{background:rgba(245,239,223,.86);border-bottom:1.5px solid rgba(90,74,58,.22)}
.g-head,.g-body{border-color:rgba(90,74,58,.16)}
.g-card.alert-card{border-top:2px solid var(--line-6)}
.tile-corner{opacity:.5}
/* 字号地板：模板已统一 12px，这里只补模板没管到的材质名与图注 */
.mat .n,.g-foot,.g-card .note{font-size:12px;letter-spacing:0}
/* 脚注：12px 不适用手写体（笔画糊成一团），走正文字体。
   ⚠️ 原写 var(--font-body) 是死声明（主题无此 token），字体实际走继承。
   12px 这条纪律保留——用户要求的是 h1–h3，不含脚注。 */
.g-foot{font-family:var(--font-sans)}
/* 天际线：模板用 .skyline 定位，换成 .wf-skyline 后必须自带定位，
   否则 SVG 会变成行内元素贴在导览板左上角（2026-11-20 踩过）。 */
.wf-skyline{position:absolute;left:0;bottom:50px;width:1080px;height:166px;z-index:0;opacity:.82}
/* 模板 .mini-glass 是 96×64 的空浮层，只放一个 ×。本主题浮层是纸面，
   空着读作一块白斑——补一道铅笔起稿线，让它读作「一张还没画完的稿纸」。 */
.mini-glass::after{
  content:"";position:absolute;left:14px;right:14px;top:22px;height:22px;
  background-image:
    linear-gradient(180deg,rgba(138,118,96,.30) 0 1.4px,transparent 1.4px),
    linear-gradient(180deg,transparent 8px,rgba(138,118,96,.20) 8px 9.2px,transparent 9.2px),
    linear-gradient(180deg,transparent 16px,rgba(63,100,73,.26) 16px 17.2px,transparent 17.2px);
}
"""


LONGHUA_OVERRIDE = r"""
/* ============ 龙华寺预览适配（香灰 · 塔檐 · 白墙，仅 longhua-si）============
   模板的蓝天空、56px 硬边草带、钢面导航、半透明玻璃面板都要翻：
   香灰底 + 棂格细线、檐口双层线、白墙浮层。
   ⛔ 不给玻璃模糊（广兰路语汇）、⛔ 不给实心硬投影（番禺路语汇）。 */
body{
  background-color:var(--bg);
  background-image:
    repeating-linear-gradient(90deg,rgba(42,37,33,.024) 0 1px,transparent 1px 14px),
    radial-gradient(120% 70% at 50% -8%,rgba(255,255,255,.66),rgba(255,255,255,0) 72%);
}
/* 模度阶梯：模板引的是世纪广场的 --concrete-deep / --steel / --lawn，本主题没有这三个 token，
   1、2、4 条会落空成透明。换成三枚本主题色 + 墨，从浅到深读作「灰、青、赭、墨」。 */
/* ⚠️ 2026-11-21：原 --bg-soft(#e8e1d4) 落在面板底 --surface-2(#efe9db) 上，
   相邻 ΔL* 仅约 3，100 那根读作空条。模度阶梯要从浅到深可辨，
   第 1 根取香灰中调（比面板底深一档，仍是最浅的一级）。 */
.mod-scale .ms:nth-child(1) i{background:#d5cbb6}
/* ⚠️ 2026-11-21：色阶条前五根纸色（#EFE9DE/#E8E1D4/#F7F2E7/#EFE9DB/#DED5C3）相邻 ΔL*
   只有 2.78/5.85/3.14/6.93，15×15 方块并排分不出边界。这是展示问题不是配色问题
   （闸门第 197 行 chroma>0.08 门槛把低彩纸色豁免了，clean=1 合理）。
   补一道墨线描边 + 内白边，让每格有界。色值不动。 */
.mini i{border:1px solid rgba(42,37,33,.34);box-shadow:inset 0 0 0 1px rgba(247,242,231,.55)}
.mod-scale .ms:nth-child(2) i{background:var(--tower)}
.mod-scale .ms:nth-child(3) i{background:var(--sandal)}
.mod-scale .ms:nth-child(4) i{background:var(--ink)}
/* 铺装网格：模板写死冷灰 + 天蓝。本主题是石灰墙与石面——白墙底 + 塔影青描边。 */
.geo-grid i{background:var(--surface-2);border-color:rgba(42,37,33,.16)}
.geo-grid i.on{background:var(--tower);border-color:rgba(53,70,74,.46)}
.geo-grid i.gl{background:rgba(198,132,125,.22);border-color:rgba(198,132,125,.52)}
/* 模板 .mini-glass 是 96×64 的空浮层。本主题浮层是白墙，空白读不出东西——
   补三道檐线，让它读作一段刻了线的石。 */
.mini-glass::after{
  content:"";position:absolute;left:12px;right:12px;top:20px;height:26px;
  background-image:
    linear-gradient(180deg,rgba(74,90,94,.34) 0 1.4px,transparent 1.4px),
    linear-gradient(180deg,transparent 9px,rgba(74,90,94,.24) 9px 10.2px,transparent 10.2px),
    linear-gradient(180deg,transparent 19px,rgba(200,164,92,.40) 19px 20.2px,transparent 20.2px);
}
.g-glow{background:radial-gradient(60% 60% at 50% 50%,rgba(200,164,92,.10),rgba(200,164,92,0) 72%)}
.lead{border-bottom:1.4px solid rgba(74,90,94,.46)}
.lead h1{font-family:var(--font-display);font-weight:700;color:var(--text-1)}
/* 标题台＝匾下的白墙：顶上一道塔影青粗线，其下一道鎏金细线，方角 */
.titlebar{
  background:var(--surface);
  border:1.4px solid rgba(42,37,33,.30);
  border-top:6px solid rgba(74,90,94,.86);
  border-radius:3px;
  box-shadow:0 2px 0 -1px rgba(200,164,92,.52),0 14px 30px rgba(42,37,33,.09),inset 0 0 0 2px rgba(247,242,231,.95);
}
/* ⚠️ 2026-11-21：换法华文楷后标题在行盒里下沉（canvas 实测 skew 6.71px：
   字形上边空 7.95px、下边空 1.24px，44px/46.64px 行盒）。原 12/26 的上下内距
   让「龙华寺」视觉偏上。上内距 +7、下内距 -7，把字形推回视觉中线。 */
.titlebar{padding:19px 24px 19px}
.titlebar .mark{top:2px;background:var(--gold);border-radius:0;width:8px;height:13px}
.titlebar .en{margin-top:9px}
/* ⚠️ 2026-11-21：法华文楷 descent 深（841/-209），spec-title / g-head 的 h2 用
   line-height:normal，行盒紧贴字形，与 .en 的间距只剩 3–4px（标题台是 9px），
   楷书的捺脚几乎顶到英文行。统一补到 9px。 */
.spec-title .en,.g-head .en{margin-top:9px}
.titlebar h2,.spec-title h2,.g-head h2,.g-card h3{font-family:var(--font-display);font-weight:700}
/* 栏题收口：青粗线 + 金细线 = 檐口双线的小号版。
   ⚠️ 必须显式 background-color:transparent——模板 .rule 自带 background:var(--primary)，
   只改 height 会让主色从透明段漏出来，读成一条实心棒（2026-11-20 踩过）。 */
.titlebar .rule,.spec-title .rule,.g-head .rule{
  height:7px;border-radius:0;bottom:10px;background-color:transparent;
  background-image:linear-gradient(180deg,rgba(74,90,94,.90) 0 2px,rgba(74,90,94,0) 2px 5px,rgba(200,164,92,.86) 5px 7px);
}
.spec-title{padding-bottom:16px}
.spec-title .rule{bottom:4px}
.g-head .rule{bottom:8px}
/* ⚠️ 2026-11-21：titlebar 下内距从 26 收到 19（补偿法华文楷字形下沉）后，
   .rule 的 bottom:10px 让檐口双线顶到「LONGHUA SI」底下只剩 3.2px，读作线穿字。
   推到 6px，净距回到 7.2px。spec-title(4px) / g-head(8px) 各自单列，不受影响。 */
.titlebar .rule{bottom:6px}
.zz{
  background:linear-gradient(180deg,rgba(74,90,94,.90) 0 2px,rgba(74,90,94,0) 2px 5px,rgba(200,164,92,.86) 5px 7px);
}
/* 材质片：圆形，白墙内圈 + 塔影青细边（铜炉是圆的，圆盘在本主题成立） */
.mat .disc{
  border-radius:50%;
  border:1.4px solid rgba(74,90,94,.44);
  box-shadow:inset 0 0 0 2px rgba(247,242,231,.90),0 10px 22px rgba(42,37,33,.10);
}
.mat .disc::after{background:radial-gradient(circle at 32% 22%,rgba(255,255,255,.16),transparent 36%)}
.mat .n{color:var(--text-3)}
.spec-cell{
  background:
    radial-gradient(circle 1.05px at 50% 50%,rgba(42,37,33,.07) 0 100%,transparent 0),
    var(--surface-2);
  background-size:9px 9px,auto;
  border:1.4px solid rgba(42,37,33,.24);
  border-radius:2px;
  box-shadow:inset 0 0 0 2px rgba(247,242,231,.92);
}
/* 玻璃格里原本是两团彩色光晕；本主题换成三段塔檐线（filter 必须关掉） */
.spec-cell.glass-cell::before{
  background:
    linear-gradient(180deg,rgba(74,90,94,.52) 0 2px,rgba(74,90,94,0) 2px 9px),
    linear-gradient(180deg,transparent 9px,rgba(74,90,94,.34) 9px 11px,transparent 11px 18px),
    linear-gradient(180deg,transparent 18px,rgba(200,164,92,.42) 18px 20px,transparent 20px),
    var(--surface-2);
  filter:none;
}
.panel{background:rgba(247,242,231,.96);border:1.4px solid rgba(74,90,94,.34);border-radius:2px}
/* ⚠️ 2026-11-21：模板 .glass-cell .glass 的 margin-left:40px 是按 72px 高浮层卡算的，
   本主题格内标签「WALL SURFACE / 白墙」在右下角，与浮层卡左缘重叠 6.4×1.5px，
   正好切掉末字「墙」的右边缘。再推 16px 让标签整条露出（实测 48px 仍差 2.4px）。 */
.spec-cell.glass-cell .glass{margin-left:56px}
.pill-ghost{color:var(--text-1);background:rgba(247,242,231,.95);border:1.4px solid rgba(74,90,94,.50);box-shadow:none}
/* 分类标记＝鎏金底 + 墨字（8.0:1）。⛔ 白墙字压金只有 2.1:1。 */
.tag-chip,.g-card .tag{background:var(--gold);color:var(--ink)}
/* 环境层：板面＝香灰 + 棂格；底带＝檐口三层线 */
.board{
  background:
    repeating-linear-gradient(90deg,rgba(42,37,33,.022) 0 1px,transparent 1px 14px),
    linear-gradient(180deg,#f4efe4 0%,#efe9de 46%,#e9e2d4 100%);
  border:1.4px solid rgba(42,37,33,.26);
  border-top:6px solid rgba(74,90,94,.84);
  box-shadow:0 2px 0 -1px rgba(200,164,92,.55),0 24px 52px rgba(42,37,33,.12);
}
.board::after{
  height:34px;border-top:none;
  background:
    linear-gradient(180deg,rgba(247,242,231,0) 0%,rgba(247,242,231,.58) 54%,rgba(247,242,231,.92) 100%),
    linear-gradient(180deg,transparent 22px,rgba(74,90,94,.34) 22px 22.8px,transparent 22.8px),
    linear-gradient(180deg,transparent 28px,rgba(200,164,92,.40) 28px 28.8px,transparent 28.8px);
  border-bottom:none;
}
.board .card,.board .g-card{border-radius:2px}
.board .glass,.board .g-modal{border-radius:4px}
.board .pill{border-radius:999px}
.guide-board{
  background:
    repeating-linear-gradient(90deg,rgba(42,37,33,.020) 0 1px,transparent 1px 14px),
    linear-gradient(180deg,#f4efe4 0%,#efe9de 48%,#e8e1d3 100%);
  border-top:6px solid rgba(74,90,94,.84);
  box-shadow:0 2px 0 -1px rgba(200,164,92,.55),0 22px 48px rgba(42,37,33,.10);
}
.guide-panel{
  background:rgba(247,242,231,.97);backdrop-filter:none;
  border:1.4px solid rgba(74,90,94,.38);
  border-radius:4px;
  box-shadow:0 22px 50px rgba(42,37,33,.12),inset 0 0 0 2px rgba(247,242,231,.95);
}
.g-nav{background:var(--surface-2);border-bottom:1.4px solid rgba(74,90,94,.54);box-shadow:0 2px 0 -1px rgba(200,164,92,.36)}
.g-head,.g-body{border-color:rgba(42,37,33,.16)}
.g-card.alert-card{border-top:3px solid var(--gold)}
.g-modal{border:1.4px solid rgba(42,37,33,.36);box-shadow:0 20px 44px rgba(42,37,33,.14)}
.tile-corner{opacity:.38}
/* 字号地板：模板已统一 12px，这里只补模板没管到的材质名与图注 */
/* ⚠️ 2026-11-21：脚注 12px 走 --font-note，而 --font-note 已在
   longhua-si.css 里改指正文黑体（图注同理），此处只需锁字号与字距。 */
.mat .n,.g-card .note{font-size:12px;letter-spacing:0}
.g-foot{font-size:12px;letter-spacing:0}
.lh-skyline{position:absolute;left:0;bottom:34px;width:1080px;height:150px;z-index:0;opacity:.78}
"""

FUZHOU_OVERRIDE = r"""
/* ============ 福州路预览适配（石印小报，仅 fuzhou-rd）============
   模板的环境层是三件「别的年代」：蓝渐变天空、56px 硬边草坪带、钢面导航与半透明玻璃面板。
   这里把它们全部翻成版面：新闻纸底、报头双线、栏线、纸面浮层——
   ⛔ 不给玻璃模糊、⛔ 不给实心硬投影（这两样是广兰路与番禺路的语汇）。 */
body{
  background-color:var(--bg);
  background-image:
    radial-gradient(circle 1px at 50% 50%,rgba(36,29,21,.024) 0 100%,transparent 0),
    radial-gradient(120% 70% at 50% -8%,rgba(255,255,255,.70),rgba(255,255,255,0) 72%);
  background-size:6px 6px,auto;
}
/* 模度阶梯：模板 .mod-scale 引的是世纪广场的 --concrete-deep / --steel / --lawn，
   本主题没有这三个 token，第 1、2、4 条会落空成透明（2026-11-20 实测）。
   换成三枚套版色 + 墨，从浅到深读作「一道印、二道印、三道印、墨压」。
   ⚠️ 必须写在这段覆盖里（插在 style 块收尾标签之前）：写进主题 CSS 会被模板同名规则盖掉。 */
.mod-scale .ms:nth-child(1) i{background:var(--ochre)}
.mod-scale .ms:nth-child(2) i{background:var(--vermilion)}
.mod-scale .ms:nth-child(3) i{background:var(--indigo)}
.mod-scale .ms:nth-child(4) i{background:var(--ink)}
/* 铺装网格：模板写死冷灰 #e4e4e0 与天蓝 rgba(0,144,205,.14)（世纪广场的混凝土与玻璃）。
   本主题是纸与套版，没有混凝土也没有玻璃——换成纸底 + 藤黄描边。 */
.geo-grid i{background:var(--surface-2);border-color:rgba(36,29,21,.18)}
.geo-grid i.on{background:var(--indigo);border-color:rgba(24,47,71,.42)}
.geo-grid i.gl{background:rgba(189,143,51,.20);border-color:rgba(189,143,51,.52)}
/* 模板 .mini-glass 是 96×64 的空浮层（只有一枚 ×），别的主题里读作磨砂玻璃面板。
   本主题的浮层是白纸，空白纸面读不出东西——补两道栏线，让它读作一张印过的纸。 */
.mini-glass::after{
  content:"";position:absolute;left:12px;right:12px;top:20px;height:26px;
  background-image:repeating-linear-gradient(180deg,
    rgba(36,29,21,.30) 0 1.2px,transparent 1.2px 8px);
}
.g-glow{background:none}
.lead{border-bottom:2px solid rgba(20,17,14,.82)}
.lead h1{font-family:var(--font-display);font-weight:400;color:var(--text-1)}
/* 标题台＝报头：顶上一道粗墨线 + 一道朱线，方角，纸面 */
.titlebar{
  background:var(--surface);
  border:1.6px solid rgba(36,29,21,.34);
  border-top:7px solid var(--ink);
  border-radius:3px;
  box-shadow:0 12px 26px rgba(20,17,14,.09),inset 0 0 0 3px rgba(252,247,232,.95);
}
.titlebar{padding:12px 24px 26px}
.titlebar .mark{top:2px;background:var(--vermilion);border-radius:0;width:8px;height:13px}
.titlebar .en{margin-top:9px}
.titlebar h2,.spec-title h2,.g-head h2,.g-card h3{font-family:var(--font-display);font-weight:400}
/* 栏题收口：墨粗线 + 朱细线 = 报头双线的小号版 */
.titlebar .rule,.spec-title .rule,.g-head .rule{
  height:8px;border-radius:0;bottom:10px;background-color:transparent;
  background-image:linear-gradient(180deg,rgba(20,17,14,.92) 0 2px,rgba(20,17,14,0) 2px 6px,rgba(168,58,44,.86) 6px 8px);
}
.spec-title{padding-bottom:16px}
.spec-title .rule{bottom:4px}
.g-head .rule{bottom:8px}
.zz{
  background:linear-gradient(180deg,rgba(20,17,14,.92) 0 2px,rgba(20,17,14,0) 2px 6px,rgba(168,58,44,.86) 6px 8px);
}
/* 材质圆一律改方片：纸、版、墨都是直角，圆盘读作另一套年代 */
.mat .disc{
  border-radius:2px;
  border:1.6px solid rgba(36,29,21,.40);
  box-shadow:inset 0 0 0 3px rgba(252,247,232,.92),0 8px 18px rgba(20,17,14,.08);
}
.mat .disc::after{background:none}
.mat .n{color:var(--text-3)}
.spec-cell{
  background:
    radial-gradient(circle 1px at 50% 50%,rgba(36,29,21,.07) 0 100%,transparent 0),
    var(--surface-2);
  background-size:7px 7px,auto;
  border:1.6px solid rgba(36,29,21,.26);
  border-radius:2px;
  box-shadow:inset 0 0 0 3px rgba(252,247,232,.92);
}
.spec-cell.glass-cell::before{
  background:
    linear-gradient(115deg,rgba(37,71,107,.58) 0 46%,rgba(37,71,107,0) 46.8%),
    linear-gradient(115deg,rgba(168,58,44,.54) 0 44%,rgba(168,58,44,0) 44.8%);
  filter:none;
}
.panel{background:rgba(252,247,232,.96);border:1.6px solid rgba(36,29,21,.24);border-radius:2px}
.pill-ghost{color:var(--text-1);background:rgba(252,247,232,.95);border:1.6px solid rgba(36,29,21,.38);box-shadow:none}
/* 分类标记＝朱底纸白字（4.9:1）。⛔ 藤黄不做底：对纸白字只有 1.9:1。 */
.tag-chip,.g-card .tag{background:var(--vermilion);color:var(--accent-ink)}
/* 环境层：板面＝新闻纸 + 顶部报头双线；底带＝报脚（墨线 + 朱线），不上色块 */
.board{
  background:
    radial-gradient(circle 1px at 50% 50%,rgba(36,29,21,.022) 0 100%,transparent 0),
    linear-gradient(180deg,#f7f0de 0%,#f3ead7 46%,#eee3ca 100%);
  background-size:6px 6px,auto;
  border:1.6px solid rgba(36,29,21,.28);
  border-top:7px solid rgba(20,17,14,.90);
  box-shadow:0 3px 0 -1px rgba(168,58,44,.55),0 22px 48px rgba(20,17,14,.12);
}
.board::after{
  height:30px;border-top:none;
  background:linear-gradient(180deg,rgba(252,247,232,0) 0%,rgba(252,247,232,.62) 52%,rgba(252,247,232,.94) 100%);
  border-bottom:2px solid rgba(20,17,14,.74);
  box-shadow:0 4px 0 -2px rgba(168,58,44,.44);
}
.board .card,.board .g-card{border-radius:2px}
.board .glass,.board .g-modal{border-radius:4px}
.board .pill{border-radius:999px}
.guide-board{
  background:
    radial-gradient(circle 1px at 50% 50%,rgba(36,29,21,.020) 0 100%,transparent 0),
    linear-gradient(180deg,#f7f0de 0%,#f3ead7 48%,#ece1c7 100%);
  background-size:6px 6px,auto;
  border-top:7px solid rgba(20,17,14,.90);
  box-shadow:0 3px 0 -1px rgba(168,58,44,.55),0 22px 48px rgba(20,17,14,.10);
}
.guide-panel{
  background:rgba(252,247,232,.97);backdrop-filter:none;
  border:1.6px solid rgba(36,29,21,.36);
  border-radius:4px;
  box-shadow:0 22px 48px rgba(20,17,14,.12),inset 0 0 0 3px rgba(252,247,232,.95);
}
.g-nav{background:var(--surface-2);border-bottom:2px solid rgba(20,17,14,.70);box-shadow:0 3px 0 -1px rgba(168,58,44,.40)}
.g-head,.g-body{border-color:rgba(36,29,21,.18)}
.g-card.alert-card{border-top:4px solid var(--vermilion)}
.g-modal{border:1.6px solid rgba(36,29,21,.40);box-shadow:0 18px 40px rgba(20,17,14,.14)}
.tile-corner{opacity:.40}
/* 字号地板：模板已统一 12px，这里只补模板没管到的材质名与图注 */
.mat .n,.g-foot,.g-card .note{font-size:12px;letter-spacing:0}
/* 天际线：模板用 .skyline 定位，换成 .fz-skyline 后必须自带定位，
   否则 SVG 会变成行内元素贴在导览板左上角（2026-11-20 同款坑）。 */
.fz-skyline{position:absolute;left:0;bottom:30px;width:1080px;height:150px;z-index:0;opacity:.80}
"""

AERO_OVERRIDE = r'''
/* ============ 广兰路预览适配（Aqua / Frutiger Aero，仅 --aero） ============
   模板为世纪版式定制，其材质词与 Aero 相反；这里把材质/几何/浮层整体翻成
   「玻璃亮带＋气泡＋白瓷＋厚折射」。
   按钮 padding 不覆盖：模板 .pill 上下 10/14 恰与广兰路主题一致，
   且主题 ::before 圆角高光胶囊按按钮高度定位，套居中覆盖会破坏刚调好的效果。 */
:root{
  --primary:var(--accent);        /* 结构件：映射到广兰路 Aqua 蓝 */
  --line-4:var(--accent-2);       /* 标签：映射到广兰路紫 */
}
body{background:#eaf7ff}
.board{background:linear-gradient(180deg,#dff2fb 0%,#eaf7ff 38%,#f2fbfb 100%)}
/* 底部环境层：世纪广场是草地带，广兰路换成 Aqua 玻璃水线（青蓝渐层 + 细亮线） */
.board::after{
  background:
    repeating-linear-gradient(90deg,rgba(255,255,255,.16) 0 1px,transparent 1px 6px),
    linear-gradient(180deg,rgba(150,220,245,.55),rgba(90,175,215,.42));
  border-top:1px solid rgba(26,127,184,.28);
}

/* 材质样本圆：混凝土/大理石/拉丝钢 → Aqua 玻璃 / 气泡 / 白瓷 / 玻璃砖 / 天光 */
.d-concrete{  /* Aqua Glass：镜面亮带 18→21% 水面线 */
  background:
    linear-gradient(180deg,rgba(255,255,255,.98) 0,rgba(255,255,255,.82) 18%,rgba(255,255,255,.36) 22%,rgba(255,255,255,.04) 40%,rgba(255,255,255,.22) 62%,rgba(255,255,255,.02) 78%,rgba(255,255,255,.42) 100%),
    linear-gradient(180deg,#f6fdff,#d9effb);
  border-color:rgba(16,90,120,.30);
  box-shadow:inset 0 1px 0 #fff,0 6px 14px rgba(12,70,100,.18),0 0 0 1px rgba(16,90,120,.22);
}
.d-marble{    /* Bubble：两枚玻璃球 + 月牙高光 */
  background:
    radial-gradient(circle at 34% 36%,rgba(16,90,120,.20) 0 2px,rgba(255,255,255,.92) 3px 15px,transparent 16px),
    radial-gradient(circle at 36% 34%,rgba(255,255,255,.95) 0 4px,transparent 6px),
    radial-gradient(circle at 68% 64%,rgba(16,90,120,.16) 0 2px,rgba(190,230,248,.95) 3px 11px,transparent 12px),
    linear-gradient(150deg,#eaf9ff,#cbe9f8);
  border-color:rgba(16,90,120,.28);
}
.d-steel{     /* Porcelain Tray：白瓷，靠一圈冷蓝釉边与釉面高光区分于玻璃 */
  background:
    radial-gradient(circle at 34% 26%,#ffffff 0 26%,#f7fdff 46%,#e6f4fb 78%,#cfe6f2 100%);
  border-color:rgba(16,90,120,.34);
  box-shadow:inset 0 0 0 3px rgba(255,255,255,.85),inset 0 -6px 14px -8px rgba(16,90,120,.40),0 8px 18px rgba(30,100,124,.16);
}
.d-frost{     /* Frosted Aqua：雾面磨砂，明显更灰更哑，与亮面 Aqua Glass 拉开 */
  background:
    linear-gradient(150deg,rgba(214,232,242,.92),rgba(176,206,222,.86) 55%,rgba(198,222,236,.90)),
    radial-gradient(circle at 32% 30%,rgba(26,127,184,.30),transparent 46%),
    radial-gradient(circle at 70% 68%,rgba(139,124,232,.22),transparent 46%);
  border-color:rgba(16,90,120,.30);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.60),inset 0 -3px 8px -4px rgba(16,90,120,.28),0 8px 18px rgba(30,100,124,.14);
}
.d-tile{      /* Glossy Tile：洁净车间亮釉砖 */
  background:repeating-linear-gradient(0deg,transparent 0 18px,rgba(16,90,120,.10) 18px 19px),repeating-linear-gradient(90deg,transparent 0 18px,rgba(16,90,120,.10) 18px 19px),linear-gradient(150deg,#f4fbff,#dceef8);
  border-color:rgba(16,90,120,.22);
}
.d-square{    /* Glass Block：玻璃砖，圆角软反光 */
  background:repeating-linear-gradient(0deg,transparent 0 25px,rgba(16,90,120,.14) 25px 26px),repeating-linear-gradient(90deg,transparent 0 25px,rgba(16,90,120,.14) 25px 26px),linear-gradient(150deg,#eef9ff,#cfe7f5);
  border-color:rgba(16,90,120,.24);
}
.d-lawn{      /* 绿带：Frutiger 的「精心维护的自然」 */
  background:repeating-linear-gradient(90deg,rgba(74,104,54,.14) 0 1px,rgba(255,255,255,.10) 1px 3px,transparent 3px 7px),radial-gradient(circle at 40% 40%,#a8c58c,#7ba368);
  border-color:rgba(74,104,54,.26);
}
.d-day{       /* Skylight：天幕冷光，压成明显的蓝调渐层，不再是一片白 */
  background:
    radial-gradient(circle at 28% 20%,rgba(255,255,255,.92),transparent 42%),
    linear-gradient(155deg,#cfe8fa 0%,#a8d4ee 46%,#7fbde0 100%);
  border-color:rgba(16,90,120,.30);
}

/* 几何：模度直角阶梯 → 圆角 / 气泡 / 玻璃倒角 */
.mod-scale .ms i{border-radius:20px}
.mod-scale .ms:nth-child(1) i{background:linear-gradient(90deg,#1a7fb8,#8fd0ec)}
.mod-scale .ms:nth-child(2) i{background:linear-gradient(90deg,#8b7ce8,#c8bff5)}
.mod-scale .ms:nth-child(3) i{background:linear-gradient(90deg,#e0632f,#f5b28d)}
.mod-scale .ms:nth-child(4) i{background:linear-gradient(90deg,#168f70,#8ccfae)}
/* 气泡网格：底色统一为 Aqua 蓝，只用深浅区分选中态，不再三色轮转 */
.geo-grid i{
  height:24px;border-radius:50%;
  background:radial-gradient(circle at 35% 28%,rgba(255,255,255,.92),rgba(26,127,184,.24) 62%,rgba(26,127,184,.10));
  border:1px solid rgba(16,90,120,.20);
}
.geo-grid i.on{background:radial-gradient(circle at 35% 28%,#fff,rgba(26,127,184,.60) 62%,rgba(26,127,184,.30));border-color:rgba(16,90,120,.38)}
.geo-grid i.gl{background:radial-gradient(circle at 35% 28%,#fff,rgba(139,124,232,.34) 62%,rgba(139,124,232,.14));border-color:rgba(104,84,186,.26)}

/* 导览面板：标题台去大理石改 Aqua 玻璃灯箱；导航去拉丝钢改玻璃条 */
.g-head{background:var(--aero-gloss),linear-gradient(180deg,#f6fdff 0%,#d9effb 100%);border-bottom:1px solid rgba(16,90,120,.24);box-shadow:inset 0 1px 0 #fff,0 8px 18px -12px rgba(12,70,100,.36)}
.g-head h2{color:var(--text-1);text-shadow:none}
.g-head .rule{background:var(--accent);box-shadow:0 0 8px rgba(26,127,184,.36)}
.g-nav{background:linear-gradient(180deg,rgba(255,255,255,.72),rgba(217,239,251,.58));border-bottom:1px solid rgba(16,90,120,.18)}
/* 导航条：七个珊瑚色实心胶囊并排＝满饱和抢戏，且违反「单视图主色 + 一个次色」。
   改为玻璃薄片导航：默认中性玻璃，仅当前项用主色实心。 */
.g-nav .pill{
  border-radius:999px;
  color:var(--accent);
  background:linear-gradient(180deg,rgba(255,255,255,.90),rgba(226,244,252,.72));
  border:1px solid rgba(26,127,184,.34);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.95),0 2px 6px rgba(12,70,100,.10);
}
.g-nav .pill::before{display:none}
.g-nav .pill-accent{
  color:#fff;
  background:linear-gradient(180deg,#3aa6e0,#1478b0);
  border-color:rgba(9,84,124,.55);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.55),0 3px 8px rgba(12,70,100,.22);
}
.g-card{background:var(--aero-gloss),linear-gradient(180deg,#f9fdff,#e6f4fb);border:1px solid var(--aero-rim);box-shadow:inset 0 1px 0 #fff,var(--aero-ring),0 10px 24px -16px rgba(16,90,120,.34),0 4px 10px rgba(16,90,120,.12)}
.g-card h3{color:var(--text-1)}
.g-card p{color:var(--text-2)}
.g-card .tag{background:var(--accent-2);color:#fff}
.alert-card{border-top:3px solid var(--accent-3)}
/* 组件卡：混凝土点阵底 → 白瓷托盘；光斑黄/2蓝/6玫红 → Aqua 蓝/紫/珊瑚 */
.spec-cell{background:radial-gradient(circle at 30% 22%,rgba(255,255,255,.98),transparent 54%),linear-gradient(160deg,#f7fcff,#e4f2fa);border:1px solid rgba(16,90,120,.16);box-shadow:inset 0 1px 0 #fff,0 6px 14px rgba(12,70,100,.10)}
.spec-cell.glass-cell::before{background:radial-gradient(circle at 30% 40%,rgba(26,127,184,.32),transparent 55%),radial-gradient(circle at 70% 60%,rgba(139,124,232,.30),transparent 55%),radial-gradient(circle at 55% 30%,rgba(224,99,47,.24),transparent 55%)}
.panel{background:rgba(255,255,255,.58);border-color:rgba(16,90,120,.16)}
.tile-corner{border-radius:22px;opacity:.72}
/* 磨砂浮层 → Aqua 玻璃浮层：保留厚倒角与强折射（Aero 的核心，不能去掉） */
.g-modal.glass{background:var(--aero-gloss),linear-gradient(150deg,rgba(255,255,255,.90),rgba(217,239,251,.82) 55%,rgba(232,244,250,.88));backdrop-filter:blur(6px) saturate(1.15);border:1px solid #fff;box-shadow:inset 0 1px 0 #fff,inset 0 -2px 6px -3px rgba(16,90,120,.28),var(--aero-ring),0 18px 38px -14px rgba(12,70,100,.42)}
.g-modal h4{color:var(--text-1)}
.skyline g rect{fill:#b6d6ec}

/* cp-* 组件类已收进 assets/themes/guanglan-rd.css 本体，此处不再兜底 */
'''

DARK_OVERRIDE = r'''
/* ===================== 暗色预览版式覆盖（灯箱夜景装饰，非主题本体） ===================== */
body{background:#120d0a}
.lead{border-bottom-color:rgba(245,185,66,.18)}
.lead .mono,.lead .meta{color:var(--text-2)}
.lead .meta code{color:var(--text-2)}
.board-tag{color:var(--text-2)}
.board-tag span{color:var(--accent-ink)}
.board{
  border-color:rgba(245,185,66,.14);
  box-shadow:0 22px 54px rgba(0,0,0,.55);
  background:linear-gradient(180deg,#1d1611 0%,#241c17 38%,#2b221a 100%);
}
/* 站台暖光带取代亮色草地带 */
.board::after{
  background:
    repeating-linear-gradient(90deg,transparent 0 6px,rgba(0,0,0,.22) 6px 7px),
    linear-gradient(180deg,rgba(245,185,66,.30),rgba(180,110,30,.18));
  border-top:1px solid rgba(245,185,66,.30);
}
.hair{background:rgba(245,185,66,.16)}
.sec-h{color:var(--text-2)}
.titlebar{border-color:rgba(245,185,66,.26);box-shadow:0 8px 22px rgba(245,185,66,.14),0 8px 18px rgba(0,0,0,.4)}
.titlebar .en,.spec-title .en,.g-head .en{color:var(--text-2)}
/* 奢华黑金大理石标题台＝地铁灯箱导视牌（金脉 + 醒目黄字，参照世纪大道站 2/4/6/9 号线导视牌） */
.titlebar h2,.spec-title h2,.g-head h2{color:var(--sign-yellow);text-shadow:0 0 24px rgba(255,210,31,.34)}
.titlebar .en,.spec-title .en,.g-head .en{color:var(--text-2);text-shadow:none}
.titlebar .rule,.spec-title .rule,.g-head .rule{background:var(--sign-yellow);box-shadow:0 0 12px rgba(255,210,31,.45)}

/* ============ 暗色色板更正（世纪大道） ============
   模板色板是世纪广场亮色版硬编码（#F9D328 / #0090CD / #84318E / #D62768），
   世纪大道主题实际用的是钠灯暖金 + 酚醛暗调（#F5B942 / #4A7091 / #7D5A86 / #A34F66）。
   不更正会出现「色板写亮黄、按钮却是暖金」的自相矛盾。 */
/* 色板小样：亮色硬编码改为暖色系（下面由 inline style 覆盖，这里兜底） */
.mini i{border-color:rgba(245,185,66,.22)}
/* 用色比例条：暗底上把次色压哑一档，避免四色并排的荧光感 */
.spec-bar i{filter:saturate(.72) brightness(.92)}
.spec-bar{box-shadow:inset 0 0 0 1px rgba(245,185,66,.20),0 5px 12px rgba(0,0,0,.45)}
.spec-legend em{color:var(--text-3)}
.panel{border-color:rgba(245,185,66,.14);background:rgba(58,46,36,.55)}
.mod-scale .ms:nth-child(1) i{background:#7a6550}
.mod-scale .ms:nth-child(2) i{background:#4a3c2f}
.mod-scale .ms:nth-child(3) i{background:var(--primary)}
.mod-scale .ms:nth-child(4) i{background:#6f8f5a}
/* 铺装网格：中性暗底，选中格用钠灯黄实心、关联格用蓝酚醛描边（原先蓝绿随机散布＝噪声） */
.geo-grid i{background:#3a2e24;border-color:rgba(245,185,66,.16)}
.geo-grid i.on{background:var(--primary);border-color:rgba(245,185,66,.55)}
.geo-grid i.gl{background:rgba(74,112,145,.30);border-color:rgba(74,112,145,.62)}
.spec-cell{
  background:radial-gradient(rgba(245,214,140,.05) .7px,transparent .7px) 0 0/4px 4px,#3a2e24;
  border-color:rgba(245,185,66,.14);box-shadow:0 6px 14px rgba(0,0,0,.4);
}
.spec-cell .cap{color:var(--text-3)}
.spec-cell.glass-cell::before{
  background:radial-gradient(circle at 30% 40%,rgba(245,185,66,.55),transparent 55%),
             radial-gradient(circle at 70% 60%,rgba(74,112,145,.5),transparent 55%),
             radial-gradient(circle at 55% 30%,rgba(163,79,102,.45),transparent 55%);
}
.guide-board{background:linear-gradient(180deg,#2a1c10 0%,#3a2a18 34%,#2b221a 72%,#2b221a 100%)}
.skyline g rect{fill:#6f5738}
.tile-corner{opacity:.7;filter:sepia(.5) brightness(.6)}
.guide-panel{border-color:rgba(245,185,66,.18);box-shadow:0 22px 48px rgba(0,0,0,.55);background:rgba(36,28,23,.72)}
.g-head{border-bottom-color:rgba(245,185,66,.14)}
.g-nav{border-bottom-color:rgba(245,185,66,.14)}
.g-card p{color:var(--text-2)}
.g-card .note{color:var(--text-3)}
.g-card .tag{background:var(--line-4);color:#f6e7cd}
.tag-chip{background:var(--line-4);color:#f6e7cd}
.cp-btn-2{color:var(--primary);background:rgba(245,185,66,.06);border:1.5px solid rgba(245,185,66,.62);box-shadow:none}
.pill-ghost{color:var(--primary);background:rgba(245,185,66,.05);border:1.5px solid rgba(245,185,66,.55);box-shadow:none}
.g-glow{
  background:radial-gradient(circle at 72% 20%,rgba(245,185,66,.34),transparent 58%),
             radial-gradient(circle at 28% 42%,rgba(74,112,145,.28),transparent 60%),
             radial-gradient(circle at 60% 72%,rgba(163,79,102,.34),transparent 62%);
}
.g-modal .x{color:var(--text-2)}
.g-modal .sub{color:var(--text-2)}
.g-modal p{color:var(--text-1)}
.g-foot{color:var(--text-3)}
/* 材质圆样本：暗色酚醛 / 奢华黑金大理石（参考方案2，与主题 cp-marble 同纹理） */
/* 暗底材质圆：模板的统一镜面高光在深色上过曝成弹珠，压到只留一道弱弧 */
.mat .disc::after{
  background:
    radial-gradient(circle at 30% 20%,rgba(255,240,210,.16) 0,rgba(255,240,210,.04) 16%,transparent 30%),
    radial-gradient(circle at 74% 86%,rgba(0,0,0,.30) 0,transparent 52%);
}
.d-concrete{background:radial-gradient(rgba(245,214,140,.12) .7px,transparent .7px) 0 0/4px 4px,#3a2e24}
.d-marble{
  background-color:var(--marble-black);
  background-image:
    radial-gradient(at 10% 10%,rgba(30,41,59,.80) 0px,transparent 60%),
    linear-gradient(115deg,transparent 47%,rgba(212,175,55,.15) 49%,var(--marble-gold) 50%,rgba(212,175,55,.10) 52%,transparent 55%),
    linear-gradient(-65deg,transparent 43%,rgba(255,255,255,.05) 45%,var(--marble-vein) 46%,transparent 48%);
  background-size:100% 100%,500px 500px,400px 400px;
}
.d-steel{background:repeating-linear-gradient(90deg,rgba(255,240,210,.10) 0 1px,rgba(0,0,0,.22) 1px 2px,transparent 2px 4px),linear-gradient(180deg,#4a3c2f,#2e251d)}
.d-frost{background:linear-gradient(150deg,rgba(255,240,210,.55),rgba(90,70,52,.75) 55%,rgba(58,46,36,.70)),radial-gradient(circle at 30% 30%,rgba(245,185,66,.35),transparent 45%),radial-gradient(circle at 70% 70%,rgba(74,112,145,.30),transparent 48%)}
.d-tile{background:repeating-linear-gradient(0deg,transparent 0 15px,rgba(0,0,0,.28) 15px 16px),repeating-linear-gradient(90deg,transparent 0 15px,rgba(0,0,0,.28) 15px 16px),#3a2e24}
.d-square{background:repeating-linear-gradient(0deg,transparent 0 15px,rgba(0,0,0,.34) 15px 16px),repeating-linear-gradient(90deg,transparent 0 15px,rgba(0,0,0,.34) 15px 16px),#2e251d}
.d-lawn{background:repeating-linear-gradient(90deg,rgba(0,0,0,.22) 0 1px,rgba(255,240,210,.05) 1px 3px,transparent 3px 6px),radial-gradient(circle at 40% 40%,#6f8f5a,#455232)}
.d-day{background:radial-gradient(circle at 28% 22%,rgba(255,226,168,.85),transparent 46%),linear-gradient(150deg,#3a2a18,#5a4022 48%,#7a5220 78%,#8a5a1e)}
'''


# 模度阶梯四色：各瓦作自备（2026-11-24 裁定「各主题自备」，⛔ 不用墨色阶兜底充数）。
# 顺序＝模板第 1–4 档（100 / 62 / 38 / 24）。值一律写字面色或字面渐变：
# 此前友谊大厦那段读的是 --gold-lo/--gold-hi/--mint/--terrazzo-deep，本主题一个都没定义，
# 同样是一条静默透明的条子（2026-11-24 复查发现）。
MOD_SCALE = {
    'century-sq':      ('#dab406', '#222222', '#0090cd', '#96b878'),
    'century-ave':     ('#f5b942', '#efe6d2', '#446685', '#96719f'),
    'friendship-bldg': ('#9f7c27', '#26221b', '#6a5d48', '#881e21'),
    'fuzhou-rd':       ('#25476b', '#a83a2c', '#bd8f33', '#14110e'),
    'guanglan-rd':     ('linear-gradient(90deg,#1a7fb8,#8fd0ec)',
                        'linear-gradient(90deg,#8b7ce8,#c8bff5)',
                        'linear-gradient(90deg,#e0632f,#f5b28d)',
                        'linear-gradient(90deg,#168f70,#8ccfae)'),
    'longhua-si':      ('#d5cbb6', '#4a5a5e', '#5f2e1c', '#2a2521'),
    'panyu-rd':        ('#ba4a33', '#141414', '#e0a32e', '#63594e'),
    'qiu-r':           ('#3c757e', '#1d2421', '#8a3932', '#4c5651'),
    'wanhang-fy':      ('#3f6449', '#241c15', '#ad6a45', '#6f5f4d'),
}


def apply_mod_scale(s, theme):
    """把本瓦作的四色写到 </style> 之前（晚于各主题 override，才盖得干净）。"""
    cols = MOD_SCALE.get(theme)
    if not cols:
        return s
    css = '\n/* ============ 模度阶梯四色（本瓦作自备） ============ */\n'
    # 第 1 档必须也写 :nth-child(1)：各主题旧 override 用了该选择器，
    # 裸 .ms i 的优先级更低，会盖不住（真踩过：暗色版 100 条仍是旧奶白）。
    css += '.mod-scale .ms:nth-child(1) i{background:%s}\n' % cols[0]
    for n, c in zip((2, 3, 4), cols[1:]):
        css += '.mod-scale .ms:nth-child(%d) i{background:%s}\n' % (n, c)
    k = s.rindex('</style>')
    return s[:k] + css + s[k:]


def _backfill_base_tokens(page, theme_css):
    """把 assets/base.css :root 里主题未定义的 token 补进页面，插在 </style> 之前。

    只补缺的：主题若自己定义了同名 token，不覆盖（主题仍是唯一真源）。
    """
    base_root = re.search(r':root\{(.*?)\}', (SKILL / 'assets/base.css').read_text(encoding='utf-8'), re.S)
    if not base_root:
        return page
    base_toks = dict(re.findall(r'--([a-z0-9-]+)\s*:\s*([^;]+);', base_root.group(1)))
    theme_toks = set(re.findall(r'--([a-z0-9-]+)\s*:', theme_css)) | set(
        re.findall(r'--([a-z0-9-]+)\s*:', page))
    missing = [(k, v.strip()) for k, v in base_toks.items() if k not in theme_toks]
    if not missing:
        return page
    block = '\n/* ============ 引擎级 token 兜底（来自 assets/base.css，主题未定义的那些） ============ */\n:root{\n'
    block += ''.join(f'  --{k}:{v};\n' for k, v in missing)
    block += '}\n'
    k = page.rindex('</style>')
    return page[:k] + block + page[k:]


def read_tokens(css_text):
    """从主题 CSS 的 :root 里读 hex token，返回 {token: '#rrggbb'}。

    预览页的色板标签必须与主题真值同源。此前靠各分支硬编码 swap 表，
    11-20 配色体检改了 :root 却没人同步那些表，12 个色值里 8 个是错的。
    这里改成直接读 CSS：改了 token，预览页自动跟上，不会再脱节。
    """
    out = {}
    for m in re.finditer(r'^\s*(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})\b', css_text, re.M):
        out[m.group(1)] = m.group(2).lower()
    return out


def sync_mini(s, tokens, spec):
    """重写 .mini-row 那一排小色块。

    模板里这 9 个 hex 是世纪广场的基底材质色（混凝土/钢/玻璃/草坪…），
    sync_palette 只管比例条与图例，从没管过它——于是每个 fork 主题都带着
    别人的材质色板（2026-11-20 在虬江上暴露）。主题给了 spec 就整排重写。
    """
    if not spec:
        return s
    missing = [t for t, _ in spec if t not in tokens]
    if missing:
        print(f'WARN mini token 缺失: {missing}', file=sys.stderr)
        return s
    m = re.search(r'<div class="mini-row">.*?</div>\s*</div>', s, re.S)
    if not m:
        print('WARN mini-row 未找到', file=sys.stderr)
        return s
    cells = '\n'.join(
        f'          <div class="mini"><i style="background:{tokens[t]}"></i><b>{tokens[t].upper()}</b></div>'
        for t, _ in spec)
    block = f'<div class="mini-row">\n{cells}\n        </div>'
    return s[:m.start()] + block + s[m.end():]


def sync_palette(s, tokens, spec):
    """按 spec 把色板比例条 / 图例 / 组件卡标注里的 hex 换成 :root 真值。

    spec = [(token, 中文名, 说明), ...] 顺序即色板从左到右的顺序。
    做法是「先按位置抓出模板里那 4 个旧 hex，再逐个替换成新值」，
    不依赖旧值是什么——旧值写的是亮黄还是紫，都能换对。
    """
    missing = [row[0] for row in spec if row[0] not in tokens]
    if missing:
        print(f'WARN palette token 缺失: {missing}', file=sys.stderr)
        return s

    # 1) 比例条：模板里 .spec-bar 下 4 个 <i style="background:#XXXXXX;flex:NN">
    bar = re.search(r'<div class="spec-bar">(.*?)</div>', s, re.S)
    if bar:
        block = bar.group(1)
        olds = re.findall(r'background:(#[0-9a-fA-F]{6});flex:(\d+)', block)
        if len(olds) == len(spec):
            new_block = block
            for (old_hex, flex), row in zip(olds, spec):
                tok = row[0]
                new_block = new_block.replace(
                    f'background:{old_hex};flex:{flex}',
                    f'background:{tokens[tok]};flex:{flex}', 1)
            s = s[:bar.start(1)] + new_block + s[bar.end(1):]

    # 2) 图例：4 个 .lg 块，按出现顺序对齐 spec。
    #    注意 .lg 内部还有 .r1 的 </div>，用非贪婪 + 精确结构匹配，
    #    否则 4 个块会被吞成 1 个（.lg 从头吃到最后一个 </div>）。
    lg_pat = re.compile(
        r'<div class="lg"><div class="r1"><i style="background:#[0-9a-fA-F]{6}"></i>'
        r'<b>[^<]*</b></div><span>#[0-9A-Fa-f]{6}</span><em>[^<]*</em></div>')
    lgs = list(lg_pat.finditer(s))
    if len(lgs) == len(spec):
        # 从后往前替换，避免前面的替换把后面的 offset 打乱
        for m, row in zip(reversed(lgs), reversed(spec)):
            tok, name, note = row[0], row[1], row[2]
            hexv = tokens[tok]
            new = (f'<div class="lg"><div class="r1"><i style="background:{hexv}"></i>'
                   f'<b>{name}</b></div><span>{hexv.upper()}</span><em>{note}</em></div>')
            s = s[:m.start()] + new + s[m.end():]
    else:
        print(f'WARN 图例块数 {len(lgs)} != spec {len(spec)}', file=sys.stderr)

    # 3) 组件卡标注：PRIMARY / #XXXXXX 这类。
    #    ⚠️ 不能按 spec 顺序猜——标签必须跟「实物」走。
    #    曾经出现过「标签写 PRIMARY / #BA4A33（赤陶），按钮实物却是 #E0A32E（赭黄）」的错位，
    #    根因是 zip(caps, spec) 拿 spec[0] 当主按钮色，而番禺路的 .pill 用的是 --ochre。
    #    这里显式登记每个主题「主按钮实际用的 token」，表里没有的回退到 spec[0]。
    #    主按钮 token 由调用方通过 spec 的第 4 个元素（可选）传入，缺省取 spec[0]。
    primary_tok = spec[0][3] if len(spec[0]) > 3 else spec[0][0]
    caps = list(re.finditer(r'<span class="cap">(PRIMARY|SECONDARY) / #[0-9A-Fa-f]{6}</span>', s))
    for idx, m in enumerate(caps):
        label = m.group(1)
        tok = primary_tok if label == 'PRIMARY' else spec[min(idx, len(spec) - 1)][0]
        s = s[:m.start()] + f'<span class="cap">{label} / {tokens[tok].upper()}</span>' + s[m.end():]
        caps = list(re.finditer(r'<span class="cap">(PRIMARY|SECONDARY) / #[0-9A-Fa-f]{6}</span>', s))

    return s


def load_bd():
    spec = importlib.util.spec_from_file_location('bd', SKILL / 'scripts/build-deck.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    args = sys.argv[1:]
    if '--help' in args or '-h' in args:
        print(__doc__)
        return
    if len(args) < 3:
        raise SystemExit(__doc__)
    dark = '--dark' in args
    aero = '--aero' in args
    if dark and aero:
        raise SystemExit('--dark 与 --aero 互斥')
    args = [a for a in args if a not in ('--dark', '--aero')]
    theme, zh, en = args[:3]
    out = args[3] if len(args) > 3 else None

    bd = load_bd()
    fonts = (SKILL / 'assets/fonts.css').read_text(encoding='utf-8')
    fonts = '\n'.join(l for l in fonts.split('\n') if not l.startswith('@import url('))
    fonts = bd.inline_fonts(fonts, SKILL / 'assets')
    theme_css = (SKILL / 'assets/themes' / f'{theme}.css').read_text(encoding='utf-8')
    # 主题自带的 @font-face（如 qiu-r 内化的奶盖宋）也要转 data URI，否则预览页按相对路径断链
    theme_css = bd.inline_fonts(theme_css, SKILL / 'assets/themes')
    # 主题里的 background:url(../textures/…) 同理：内联进预览页后，相对路径的基准变成页面目录，
    # 不转 data URI 就会 404 且无声（2026-11-22 位图材质进库后新增这条）
    theme_css = bd.inline_images(theme_css, SKILL / 'assets/themes')

    # --aero: 主题自带 Google Fonts @import，必须提到 <style> 最前，否则内联后中段无效
    imports = ''
    if aero:
        tlines = theme_css.split('\n')
        found = [l.strip() for l in tlines if l.strip().startswith('@import')]
        theme_css = '\n'.join(l for l in tlines if not l.strip().startswith('@import'))
        imports = '\n'.join(found) + '\n' if found else ''

    tokens = read_tokens(theme_css)

    src = TPL.read_text(encoding='utf-8')
    marker = '/* ===================== 预览页专用版式（不属于主题） ===================== */'
    tail = src[src.index(marker):]

    # data-theme 供模板里 [data-theme="X"] 作用域的主题专属材质选择器命中
    head = ('<!DOCTYPE html>\n<html lang="zh-CN" data-theme="' + theme + '">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{zh} {en} · 来雪亭 B 出口主题预览</title>\n<style>\n'
            + imports +
            '/* ============ 内化字体（data URI，随文件可移植） ============ */\n'
            f'{fonts}\n/* ============ 主题：{theme} ============ */\n{theme_css}\n')

    s = head + tail
    # 引擎级 token 兜底：--t-* 字阶与中性墨色定义在 assets/base.css 的 :root，主题只引用不重写。
    # 预览页此前只内联主题 CSS，于是 font-size:var(--t-h1) 全是死引用（静默退回继承值），
    # 字号档形同虚设（2026-11-24 排障发现）。这里只补主题没定义的那些，主题自己的值仍优先。
    s = _backfill_base_tokens(s, theme_css)
    # 覆盖段必须插在 </style> 之前，不能追加到文件末尾（否则落在 </body> 后无效）
    k = s.index('</style>')
    if dark:
        s = s[:k] + GHOST_BTN_OVERRIDE + '\n' + DARK_OVERRIDE + '\n' + s[k:]
    elif aero:
        s = s[:k] + AERO_OVERRIDE + '\n' + s[k:]
    elif theme == 'friendship-bldg':
        # 友谊大厦：主题自带 .fb-* 材质与完整 token，预览板只需换语汇，不借用世纪广场的混凝土/大理石/钢
        s = s[:k] + FRIENDSHIP_OVERRIDE + '\n' + s[k:]
    elif theme == 'qiu-r':
        # 虬江：纸面学术版，材质圆全部换成 qj-* 方片
        s = s[:k] + QIU_OVERRIDE + '\n' + s[k:]
    elif theme == 'wanhang-fy':
        # 万航渡：纸绘动画版，环境层换成本墨晕 / 画稿纸 / 河岸草带
        s = s[:k] + WANHANG_OVERRIDE + '\n' + s[k:]
    elif theme == 'fuzhou-rd':
        # 福州路：石印小报版，环境层换成新闻纸 / 报头双线 / 报脚
        s = s[:k] + FUZHOU_OVERRIDE + '\n' + s[k:]
    elif theme == 'longhua-si':
        # 龙华寺：香灰版，环境层换成棂格 / 檐口双线 / 白墙
        s = s[:k] + LONGHUA_OVERRIDE + '\n' + s[k:]
    else:
        # 不锈钢强化 / 白大理石材质圆只作用于亮色版世纪广场；暗色版保持既有暖酚醛钢面与黑金大理石
        s = s[:k] + GHOST_BTN_OVERRIDE + '\n' + LIGHT_STEEL_OVERRIDE + '\n' + LIGHT_MARBLE_OVERRIDE + '\n' + s[k:]
        # 页眉措辞：世纪广场的定位是「模度几何 · 清水混凝土」，不是笼统的「磨砂玻璃版」
        # ⚠️ 必须限定 theme == 'century-sq'：这条是全局 replace，若不加条件会先跑，
        #    把 panyu-rd / qiu-r 段依赖的「磨砂玻璃版」old 串改掉，导致它们的页眉替换静默失效。
        if theme == 'century-sq':
            s = s.replace('磨砂玻璃版 · 2026-11-19',
                          '模度几何版 · 2026-11-19')
    if not aero:
        # 按钮垂直居中覆盖只给世纪主题；广兰路 padding 10/14 本就居中且高光胶囊依赖按钮高度
        k = s.index('</style>')
        s = s[:k] + PILL_ALIGN_OVERRIDE + '\n' + s[k:]

    # ---- 色板同步（唯一真源＝主题 :root）----
    # 各分支的 swap 表只管「换成哪个 token 语义」，具体 hex 一律从 tokens 取，
    # 避免 11-20 那次「改了 :root、预览页还写旧值」的脱节重演。
    if aero:
        PALETTE_SPEC = [
            ('--accent',   'Primary', '主色 · 结构件 / 链接 / 强调'),
            ('--accent-2', 'Violet',  '紫玻璃 · 分类标签'),
            ('--accent-3', 'Coral',   '暖珊瑚 · 轻提示 / 卡顶'),
            ('--good',     'Green',   '绿化带 · 仅环境层'),
        ]
    elif dark:
        PALETTE_SPEC = [
            ('--primary', 'Primary', '钠灯黄 · 灯箱 / 主按钮'),
            ('--line-2',  'Line 9',  '蓝酚醛 · 导航 / 次按钮'),
            ('--line-4',  'Line 4',  '紫酚醛 · 分类标签'),
            ('--line-6',  'Line 6',  '玫红酚醛 · 轻警示'),
        ]
    elif theme == 'panyu-rd':
        # 番禺路不是地铁站，也不是色号系统：色板按「面 / 线 / 标记」分工命名
        PALETTE_SPEC = [
            ('--primary', '赤陶',   '主色 · 实心块 / 图版', '--ochre'),
            ('--line-2',  '墨黑',   '正文 / 边框 / 硬投影'),
            ('--line-4',  '赭黄',   '分类标签 / 胶囊底 / 图版号'),
            ('--line-6',  '鼠尾草', '轻警示 / 卡顶细条'),
        ]
    elif theme == 'qiu-r':
        # 虬江不是地铁站，⛔ 不许沿用 Line 2/4/6/9 这套线号标签（2026-11-20 修）
        PALETTE_SPEC = [
            ('--primary', '河青',   '主色 · 实心块 / 按钮 / 顶线'),
            ('--line-2',  '墨黑',   '正文 / 导航 / 次按钮'),
            ('--line-4',  '砖红',   '分类标签 / 图版号 / 批注'),
            ('--line-6',  '深砖',   '轻警示 / 卡顶细条'),
        ]
    elif theme == 'wanhang-fy':
        # 万航渡不是地铁站：色板按「树荫 / 纸墨 / 河 / 砖」分工命名
        PALETTE_SPEC = [
            ('--primary', '梧桐',   '主色 · 按钮 / 强调 / 顶线'),
            ('--line-2',  '纸墨',   '正文 / 边框 / 轮廓线'),
            ('--line-4',  '河青',   '分类标签 / 链接 / 水线'),
            ('--line-6',  '深砖',   '轻警示 / 卡顶细条'),
        ]
    elif theme == 'fuzhou-rd':
        # 福州路不是地铁站：色板按「套版」分工命名——靛主、朱标记、墨版线、藤黄小牌
        PALETTE_SPEC = [
            ('--primary',  '套版靛', '主色 · 按钮 / 主块 / 顶线'),
            ('--vermilion','套版朱', '分类标记 / 图版号 / 第二块版'),
            ('--line-2',   '墨',     '正文 / 版线 / 报头粗线'),
            ('--line-6',   '藤黄',   '小牌 / 轻标记'),
        ]
    elif theme == 'longhua-si':
        # 龙华寺不是地铁站：色板按「殿前四物」分工命名——檀赭主、塔影青线、鎏金小牌、春桃标记
        PALETTE_SPEC = [
            ('--sandal', '檀赭',   '主色 · 按钮 / 柱身 / 顶线'),
            ('--tower',  '塔影青', '线 / 判对 / 次按钮'),
            ('--gold',   '鎏金',   '匾额 / 小牌 / 轻标记'),
            ('--peach',  '春桃',   '落瓣 / 分类标记'),
        ]
    elif theme == 'friendship-bldg':
        PALETTE_SPEC = [
            ('--gold',     '鎏金',   '主色 · 塔身 / 按钮 / 强调'),
            ('--red',      '红玻璃', '五角星 / 标记 / 轻警示'),
            ('--accent-3', '墨绿',   '分类标签 / 辅助标注'),
            ('--mint',     '薄荷绿', '序馆穹顶 / 柔和底'),
        ]
    else:
        PALETTE_SPEC = [
            ('--primary', 'Primary', '主色 · 按钮 / 强调 / 进度'),
            ('--line-2',  'Line 9',  '导航 / 链接 / 次按钮'),
            ('--line-4',  'Line 4',  '分类标签 / 辅助标注'),
            ('--line-6',  'Line 6',  '轻警示 / 卡顶细条'),
        ]
    s = sync_palette(s, tokens, PALETTE_SPEC)
    # 基底材质色排：只有给了 MINI_SPEC 的主题才重写（其余主题的模板值仍是世纪广场的，
    # 属已知未治项，见 references/theme-preview.md 的漂移清单）
    MINI_SPEC = None
    if theme == 'wanhang-fy':
        # ---- 万航渡：纸绘动画。色板 hex 由 sync_palette 填，这里只换
        #      「语义标签 / 材质圆 / 导览语汇 / 页眉事实 / 天际线」----
        wf_swaps = [
            ('<span class="cap">SECONDARY / LINE 2</span>', '<span class="cap">SECONDARY / PAPER INK</span>'),
            ('<span class="cap">CATEGORY / LINE 4</span>', '<span class="cap">CATEGORY / RIVER</span>'),
            ('<span class="cap">ALERT STRIPE / LINE 6</span>', '<span class="cap">ALERT / DEEP BRICK</span>'),
            ('<span class="cap">SELECTED / FIXED YELLOW</span>', '<span class="cap">SELECTED / PLANE</span>'),
            ('<span class="cap">FROSTED PANEL</span>', '<span class="cap">SOFT SHADOW / 浮层</span>'),
            ('<div class="sub">子标题 · FROSTED GLASS</div>', '<div class="sub">子标题 · 纸面柔影</div>'),
            # 材质圆：八个通用 .d-* 换成本主题的水墨晕 / 河岸 / 画稿纸 / 苏州河 / 驳岸 / 梧桐 / 红砖 / 墨
            ('<div class="disc d-concrete"></div><div class="n">Raw Concrete</div>',
             '<div class="disc wf-wash"></div><div class="n">水墨晕</div>'),
            ('<div class="disc d-marble"></div><div class="n">Polished Marble</div>',
             '<div class="disc wf-paper"></div><div class="n">画稿纸</div>'),
            ('<div class="disc d-steel"></div><div class="n">Brushed Steel</div>',
             '<div class="disc wf-bank"></div><div class="n">河岸</div>'),
            ('<div class="disc d-frost"></div><div class="n">Frosted Glass</div>',
             '<div class="disc wf-river"></div><div class="n">苏州河</div>'),
            ('<div class="disc d-tile"></div><div class="n">Matte Tile</div>',
             '<div class="disc wf-quay"></div><div class="n">驳岸</div>'),
            ('<div class="disc d-square"></div><div class="n">Matte Square</div>',
             '<div class="disc wf-grove"></div><div class="n">梧桐</div>'),
            ('<div class="disc d-lawn"></div><div class="n">Green Lawn</div>',
             '<div class="disc wf-brick-swatch"></div><div class="n">红砖</div>'),
            ('<div class="disc d-day"></div><div class="n">Soft Daylight</div>',
             '<div class="disc wf-ink"></div><div class="n">墨</div>'),
            # 导航：当前项梧桐绿实心，其余棕灰描边幽灵
            ('<span class="pill pill-accent">首页</span>\n        <span class="pill pill-accent">广场</span>\n        <span class="pill pill-accent">餐饮</span>\n        <span class="pill pill-accent">服务</span>\n        <span class="pill pill-accent">公园</span>\n        <span class="pill pill-accent">植被</span>\n        <span class="pill pill-accent">休憩</span>\n        <span class="pill">关于我们</span>',
             '<span class="pill pill-accent">首页</span>\n        <span class="pill pill-ghost">渡口</span>\n        <span class="pill pill-ghost">河岸</span>\n        <span class="pill pill-ghost">618</span>\n        <span class="pill pill-ghost">桥</span>\n        <span class="pill pill-ghost">纸</span>\n        <span class="pill">关于我们</span>'),
            ('<div class="k">PLAZA</div>\n          <h3>Century Sq</h3>\n          <p>导览面板示例页。标题台用磨光大理石，卡片用清水混凝土；正文按标题—正文—注释三级排布，行距与留白服从模度。</p>',
             '<div class="k">WANHANG FY</div>\n          <h3>万航渡</h3>\n          <p>导览面板示例页。标题台用画稿纸，卡片用薄彩纸；正文按标题—正文—注释三级排布，行距 1.7，一屏只留一道岸线。</p>'),
            ('<span class="tag">Category</span>\n          <h3>植被与休憩</h3>\n          <p>分类标记固定用 4 号线紫；草坪与瓷砖只作底部环境层，低透明度暗示材质，不盖住文字。</p>',
             '<span class="tag">Category</span>\n          <h3>渡口与桥</h3>\n          <p>分类标记固定用河青；岸线与水面只作底部环境层，低透明度暗示材质，不盖住文字。</p>'),
            ('<p>6 号线玫红仅作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>',
             '<p>深砖仅作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>'),
            ('<div class="sub">FROSTED GLASS / 磨砂浮层</div>\n        <p>半透明雾面、轻微背景模糊、淡天光蓝调；边缘只有柔和高光，不做厚倒角与强折射。</p>',
             '<div class="sub">SOFT SHADOW / 柔影浮层</div>\n        <p>不透明纸面、1.5px 棕灰细线、零偏移的高斯柔影；抬起来靠影的扩散，不靠影的方向。</p>'),
            ('<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实广场公告</div>',
             '<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实街区公告</div>'),
            ('<code>assets/themes/century-sq.css</code><br>\n      磨砂玻璃版 · 2026-11-19',
             '<code>assets/themes/wanhang-fy.css</code><br>\n      画稿纸 · 梧桐绿 · 河青 · 砖红 · 2026-11-21'),
            ('<span class="pill">Submit</span>', '<span class="pill">提交</span>'),
        ]
        for old, new in wf_swaps:
            if old not in s:
                print(f'WARN wanhang-fy swap miss: {old[:64]}', file=sys.stderr)
                continue
            s = s.replace(old, new, 1)
        # 模板的环境层是「蓝天空 / 草坪硬带 / 钢面导航」：
        # 天空换水墨晕、草带换河岸、钢面换纸面。
        s = s.replace('<div class="g-nav cp-steel">', '<div class="g-nav wf-nav">', 1)
        # 天际线：28 个错落方盒（CBD 轮廓）→ 苏州河 + 一座桥 + 车站钟楼 + 梧桐树冠
        s = re.sub(
            r'<svg class="skyline".*?</svg>',
            """<svg class="wf-skyline" viewBox="0 0 760 110" preserveAspectRatio="none" aria-hidden="true">
      <!-- 苏州河：一条水平光带 + 两道波线；一座单孔桥压在河上——渡口被桥取代，只剩名字。 -->
      <g fill="none" stroke="#8A7660" stroke-width="1" stroke-opacity=".26">
        <path d="M0 78 C80 74 160 80 240 76 C320 72 400 79 480 75 C560 71 640 78 720 75 L760 74"/>
        <path d="M0 90 C90 86 170 92 260 88 C350 84 430 91 520 87 C610 83 690 89 760 86"/>
      </g>
      <rect x="0" y="82" width="760" height="20" fill="#9FBCC6" fill-opacity=".30"/>
      <rect x="0" y="82" width="760" height="1.6" fill="#2B5168" fill-opacity=".30"/>
      <!-- 单孔桥：拱券与桥面两根线 -->
      <path d="M196 96 C196 44 356 44 356 96" fill="none" stroke="#8A7660" stroke-width="1.6" stroke-opacity=".38"/>
      <!-- 梵皇渡车站钟楼：一座窄塔 + 钟面 -->
      <rect x="612" y="50" width="20" height="40" fill="none" stroke="#8A7660" stroke-width="1.2" stroke-opacity=".34"/>
      <path d="M608 50 L646 50 L627 36 Z" fill="none" stroke="#8A7660" stroke-width="1.2" stroke-opacity=".34"/>
      <circle cx="622" cy="62" r="4.5" fill="none" stroke="#8A7660" stroke-width="1" stroke-opacity=".40"/>
      <!-- 厂房坡顶：低矮一排，只勾轮廓 -->
      <path d="M64 82 L64 64 L150 56 L236 64 L236 82" fill="none" stroke="#8A7660" stroke-width="1.2" stroke-opacity=".30"/>
      <!-- 梧桐树冠：三组圆，读成行道树不是噪声 -->
      <g fill="#35583f" fill-opacity=".38">
        <circle cx="44" cy="66" r="13"/><circle cx="58" cy="60" r="10"/><circle cx="70" cy="67" r="8"/>
        <circle cx="432" cy="66" r="12"/><circle cx="446" cy="60" r="9"/>
        <circle cx="692" cy="64" r="13"/><circle cx="708" cy="58" r="10"/><circle cx="720" cy="65" r="8"/>
      </g>
      <path d="M0 100 C120 94 200 100 300 96 C420 92 520 99 620 95 C690 92 730 96 760 95 L760 110 L0 110 Z" fill="#8CA876" fill-opacity=".30"/>
    </svg>""",
            s, count=1, flags=re.S)

    if theme == 'fuzhou-rd':
        # ---- 福州路：石印小报。只换「语义标签 / 材质片 / 导览语汇 / 页眉事实 / 天际线」----
        fz_swaps = [
            ('<span class="cap">SECONDARY / LINE 2</span>', '<span class="cap">SECONDARY / INK</span>'),
            ('<span class="cap">CATEGORY / LINE 4</span>', '<span class="cap">CATEGORY / VERMILION</span>'),
            ('<span class="cap">ALERT STRIPE / LINE 6</span>', '<span class="cap">ALERT / OCHRE</span>'),
            ('<span class="cap">SELECTED / FIXED YELLOW</span>', '<span class="cap">SELECTED / INDIGO</span>'),
            ('<span class="cap">FROSTED PANEL</span>', '<span class="cap">PAPER SHEET / 白纸</span>'),
            ('<div class="sub">子标题 · FROSTED GLASS</div>', '<div class="sub">子标题 · 报头双线</div>'),
            # 材质片：八个通用 .d-* 换成本主题的纸 / 网点 / 套版
            ('<div class="disc d-concrete"></div><div class="n">Raw Concrete</div>',
             '<div class="disc fz-paper"></div><div class="n">白纸</div>'),
            ('<div class="disc d-marble"></div><div class="n">Polished Marble</div>',
             '<div class="disc fz-halftone"></div><div class="n">网点</div>'),
            ('<div class="disc d-steel"></div><div class="n">Brushed Steel</div>',
             '<div class="disc fz-ochre"></div><div class="n">套版藤黄</div>'),
            ('<div class="disc d-frost"></div><div class="n">Frosted Glass</div>',
             '<div class="disc fz-news"></div><div class="n">新闻纸</div>'),
            ('<div class="disc d-tile"></div><div class="n">Matte Tile</div>',
             '<div class="disc fz-misreg"></div><div class="n">套版错位</div>'),
            ('<div class="disc d-square"></div><div class="n">Matte Square</div>',
             '<div class="disc fz-vermilion"></div><div class="n">套版朱</div>'),
            ('<div class="disc d-lawn"></div><div class="n">Green Lawn</div>',
             '<div class="disc fz-indigo"></div><div class="n">套版靛</div>'),
            ('<div class="disc d-day"></div><div class="n">Soft Daylight</div>',
             '<div class="disc fz-ink"></div><div class="n">墨</div>'),
            # 导航：当前项靛实心，其余墨线幽灵
            ('<span class="pill pill-accent">首页</span>\n        <span class="pill pill-accent">广场</span>\n        <span class="pill pill-accent">餐饮</span>\n        <span class="pill pill-accent">服务</span>\n        <span class="pill pill-accent">公园</span>\n        <span class="pill pill-accent">植被</span>\n        <span class="pill pill-accent">休憩</span>\n        <span class="pill">关于我们</span>',
             '<span class="pill pill-accent">首页</span>\n        <span class="pill pill-ghost">报馆</span>\n        <span class="pill pill-ghost">书店</span>\n        <span class="pill pill-ghost">石印</span>\n        <span class="pill pill-ghost">套版</span>\n        <span class="pill pill-ghost">栏线</span>\n        <span class="pill">关于我们</span>'),
            ('<div class="k">PLAZA</div>\n          <h3>Century Sq</h3>\n          <p>导览面板示例页。标题台用磨光大理石，卡片用清水混凝土；正文按标题—正文—注释三级排布，行距与留白服从模度。</p>',
             '<div class="k">FUZHOU RD</div>\n          <h3>福州路</h3>\n          <p>导览面板示例页。标题台用白纸压报头双线，卡片用网点纸；正文按标题—正文—注释三级排布，行距 1.7，一屏只留一组栏线。</p>'),
            ('<span class="tag">Category</span>\n          <h3>植被与休憩</h3>\n          <p>分类标记固定用 4 号线紫；草坪与瓷砖只作底部环境层，低透明度暗示材质，不盖住文字。</p>',
             '<span class="tag">Category</span>\n          <h3>报馆与书店</h3>\n          <p>分类标记固定用套版朱；网点与栏线只作版面层，低透明度暗示印刷，不盖住文字。</p>'),
            ('<p>6 号线玫红仅作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>',
             '<p>藤黄仅作图版号与轻标记，绝不铺底。此处为版式占位文案，非真实公告。</p>'),
            ('<div class="sub">FROSTED GLASS / 磨砂浮层</div>\n        <p>半透明雾面、轻微背景模糊、淡天光蓝调；边缘只有柔和高光，不做厚倒角与强折射。</p>',
             '<div class="sub">INK RULE / 报头双线</div>\n        <p>不透明纸面、1.6px 墨线、零方向柔影；层次靠第二块版错开的边，不靠影的方向。</p>'),
            ('<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实广场公告</div>',
             '<div class="g-foot">示例文案 · 用于展示层级与版式，不代表真实街区公告</div>'),
            ('<code>assets/themes/century-sq.css</code><br>\n      磨砂玻璃版 · 2026-11-19',
             '<code>assets/themes/fuzhou-rd.css</code><br>\n      新闻纸 · 套版靛 · 套版朱 · 藤黄 · 2026-11-20'),
            ('<span class="pill">Submit</span>', '<span class="pill">提交</span>'),
        ]
        for old, new in fz_swaps:
            if old not in s:
                print(f'WARN fuzhou swap miss: {old[:64]}', file=sys.stderr)
                continue
            s = s.replace(old, new, 1)
        # 导航条：钢面换成纸面版条
        s = s.replace('<div class="g-nav cp-steel">', '<div class="g-nav fz-nav">', 1)
        # 天际线：28 个错落方盒（CBD 轮廓）→ 街屋坡顶 + 竖排窗 + 报脚双线
        s = re.sub(
            r'<svg class="skyline".*?</svg>',
            """<svg class="fz-skyline" viewBox="0 0 760 120" preserveAspectRatio="none" aria-hidden="true">
      <g fill="#241d15" fill-opacity=".30">
        <path d="M0 78 L58 78 L58 52 L92 52 L92 78 L150 78 L150 60 L196 60 L196 78 L252 78 L252 46 L286 46 L286 78 L344 78 L344 64 L392 64 L392 78 L448 78 L448 50 L486 50 L486 78 L548 78 L548 58 L596 58 L596 78 L654 78 L654 48 L692 48 L692 78 L760 78 L760 120 L0 120 Z"/>
      </g>
      <g fill="#fcf7e8" fill-opacity=".58">
        <rect x="66" y="58" width="8" height="12"/><rect x="80" y="58" width="8" height="12"/>
        <rect x="160" y="66" width="8" height="10"/><rect x="176" y="66" width="8" height="10"/>
        <rect x="262" y="52" width="8" height="12"/><rect x="274" y="52" width="8" height="12"/>
        <rect x="352" y="70" width="8" height="8"/><rect x="366" y="70" width="8" height="8"/>
        <rect x="458" y="56" width="8" height="12"/><rect x="472" y="56" width="8" height="12"/>
        <rect x="558" y="64" width="8" height="10"/><rect x="572" y="64" width="8" height="10"/>
        <rect x="662" y="54" width="8" height="12"/><rect x="676" y="54" width="8" height="12"/>
      </g>
      <rect x="0" y="86" width="760" height="2" fill="#14110e" fill-opacity=".72"/>
      <rect x="0" y="92" width="760" height="1.6" fill="#a83a2c" fill-opacity=".62"/>
    </svg>""",
            s, count=1, flags=re.S)

    if theme == 'panyu-rd':
        MINI_SPEC = [
            ('--bg',        '石灰华'),
            ('--bg-soft',   '灰泥深'),
            ('--surface',   '纸白'),
            ('--surface-2', '纸二'),
            ('--paper-deep','纸槽'),
            ('--terracotta','赤陶'),
            ('--ochre',     '赭黄'),
            ('--ultra',     '群青'),
            ('--sage',      '鼠尾草'),
        ]
    if theme == 'fuzhou-rd':
        MINI_SPEC = [
            ('--bg',        '新闻纸'),
            ('--bg-soft',   '纸深'),
            ('--surface',   '白纸'),
            ('--surface-2', '网点纸'),
            ('--paper-deep','纸槽'),
            ('--vermilion', '套版朱'),
            ('--indigo',    '套版靛'),
            ('--ochre',     '藤黄'),
            ('--ink',       '墨'),
        ]
    if theme == 'wanhang-fy':
        MINI_SPEC = [
            ('--bg',        '画稿纸'),
            ('--bg-soft',   '纸二'),
            ('--surface',   '卡纸'),
            ('--surface-2', '薄彩'),
            ('--paper-deep','纸槽'),
            ('--plane',     '梧桐'),
            ('--river',     '河青'),
            ('--lawn',      '草坪'),
            ('--brick',     '老砖'),
            ('--brick-dk',  '砖红'),
        ]
    if theme == 'qiu-r':
        MINI_SPEC = [
            ('--bg',        '纸底'),
            ('--bg-soft',   '纸底深'),
            ('--surface',   '卡纸'),
            ('--surface-2', '稿纸'),
            ('--paper-deep','石槽'),
            ('--stone',     '河埠石'),
            ('--brick-wall','青砖'),
            ('--ink-blue',  '靛'),
            ('--ginkgo',    '银杏'),
        ]
    if theme == 'longhua-si':
        MINI_SPEC = [
            ('--bg',        '香灰'),
            ('--bg-soft',   '灰深'),
            ('--surface',   '白墙'),
            ('--surface-2', '墙二'),
            ('--paper-deep','石槽'),
            ('--sandal',    '檀赭'),
            ('--tower',     '塔影青'),
            ('--gold',      '鎏金'),
            ('--ink',       '墨'),
        ]

    s = sync_mini(s, tokens, MINI_SPEC)

    if theme == 'longhua-si':
        # ---- 龙华寺：香灰 · 塔檐 · 白墙。只换「语义标签 / 材质片 / 导览语汇 / 页眉事实 / 天际线」----
        lh_swaps = [
            ('<span class="cap">SECONDARY / LINE 2</span>', '<span class="cap">SECONDARY / TOWER</span>'),
            ('<span class="cap">CATEGORY / LINE 4</span>', '<span class="cap">CATEGORY / PEACH</span>'),
            ('<span class="cap">ALERT STRIPE / LINE 6</span>', '<span class="cap">ALERT / GOLD</span>'),
            ('<span class="cap">SELECTED / FIXED YELLOW</span>', '<span class="cap">SELECTED / TOWER</span>'),
            ('<span class="cap">FROSTED PANEL</span>', '<span class="cap">WALL SURFACE / 白墙</span>'),
            ('<div class="sub">子标题 · FROSTED GLASS</div>', '<div class="sub">子标题 · 檐口双线</div>'),
            # 材质片：八个通用 .d-* 换成白墙 / 香灰 / 碑石 / 春桃 / 塔檐 / 铜绿 / 檀赭 / 墨
            ('<div class="disc d-concrete"></div><div class="n">Raw Concrete</div>',
             '<div class="disc lh-wall"></div><div class="n">白墙</div>'),
            ('<div class="disc d-marble"></div><div class="n">Polished Marble</div>',
             '<div class="disc lh-ash"></div><div class="n">香灰</div>'),
            ('<div class="disc d-steel"></div><div class="n">Brushed Steel</div>',
             '<div class="disc lh-granite"></div><div class="n">碑石</div>'),
            ('<div class="disc d-frost"></div><div class="n">Frosted Glass</div>',
             '<div class="disc lh-peach"></div><div class="n">落瓣</div>'),
            ('<div class="disc d-tile"></div><div class="n">Matte Tile</div>',
             '<div class="disc lh-eave"></div><div class="n">塔檐</div>'),
            ('<div class="disc d-square"></div><div class="n">Matte Square</div>',
             '<div class="disc lh-patina"></div><div class="n">铜绿</div>'),
            ('<div class="disc d-lawn"></div><div class="n">Green Lawn</div>',
             '<div class="disc lh-sandal"></div><div class="n">檀赭</div>'),
            ('<div class="disc d-day"></div><div class="n">Soft Daylight</div>',
             '<div class="disc lh-ink"></div><div class="n">墨</div>'),
            # 导航：当前项檀赭实心，其余塔影青线幽灵
            ('<span class="pill pill-accent">首页</span>\n        <span class="pill pill-accent">广场</span>\n        <span class="pill pill-accent">餐饮</span>\n        <span class="pill pill-accent">服务</span>\n        <span class="pill pill-accent">公园</span>\n        <span class="pill pill-accent">植被</span>\n        <span class="pill pill-accent">休憩</span>\n        <span class="pill">关于我们</span>',
             '<span class="pill pill-accent">首页</span>\n        <span class="pill pill-ghost">塔檐</span>\n        <span class="pill pill-ghost">香灰</span>\n        <span class="pill pill-ghost">白墙</span>\n        <span class="pill pill-ghost">落瓣</span>\n        <span class="pill pill-ghost">铜炉</span>\n        <span class="pill">关于我们</span>'),
            ('<div class="k">PLAZA</div>\n          <h3>Century Sq</h3>\n          <p>导览面板示例页。标题台用磨光大理石，卡片用清水混凝土；正文按标题—正文—注释三级排布，行距与留白服从模度。</p>',
             '<div class="k">LONGHUA SI</div>\n          <h3>龙华寺</h3>\n          <p>导览面板示例页。标题台压塔檐双线，卡片用香灰纸；正文按标题—正文—注释三级排布，行距 1.7，一屏只留一道檐线。</p>'),
            ('<span class="tag">Category</span>\n          <h3>植被与休憩</h3>\n          <p>分类标记固定用 4 号线紫；草坪与瓷砖只作底部环境层，低透明度暗示材质，不盖住文字。</p>',
             '<span class="tag">Category</span>\n          <h3>塔檐与香灰</h3>\n          <p>分类标记固定用春桃；香灰与磬灰只作底部环境层，低透明度暗示质地，不盖住文字。</p>'),
            ('<p>6 号线玫红仅作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>',
             '<p>鎏金仅作匾沿小牌与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>'),
            ('<div class="sub">FROSTED GLASS / 磨砂浮层</div>\n        <p>半透明雾面、轻微背景模糊、淡天光蓝调；边缘只有柔和高光，不做厚倒角与强折射。</p>',
             '<div class="sub">EAVE RULE / 檐口双线</div>\n        <p>不透明白墙、1.4px 塔影青细线、零方向柔影；层次靠檐口逐级收分的线组，不靠影的方向。</p>'),
            ('<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实广场公告</div>',
             '<div class="g-foot">示例文案 · 用于展示层级与版式，不代表真实寺院公告</div>'),
            ('<code>assets/themes/century-sq.css</code><br>\n      磨砂玻璃版 · 2026-11-19',
             '<code>assets/themes/longhua-si.css</code><br>\n      香灰 · 檀赭 · 塔影青 · 鎏金 · 春桃 · 2026-11-20'),
            ('<span class="pill">Submit</span>', '<span class="pill">提交</span>'),
        ]
        for old, new in lh_swaps:
            if old not in s:
                print(f'WARN longhua swap miss: {old[:64]}', file=sys.stderr)
                continue
            s = s.replace(old, new, 1)
        # 导航条：钢面换成白墙版条
        s = s.replace('<div class="g-nav cp-steel">', '<div class="g-nav lh-nav">', 1)
        # 天际线：CBD 方盒 → 八角塔（七级收分）+ 殿宇坡顶 + 檐口双线
        s = re.sub(
            r'<svg class="skyline".*?</svg>',
            """<svg class="lh-skyline" viewBox="0 0 760 120" preserveAspectRatio="none" aria-hidden="true">
      <g fill="#4a5a5e" fill-opacity=".28">
        <path d="M0 86 L84 86 L84 72 L140 72 L140 86 L196 86 L196 66 L232 66 L232 86 L286 86 L286 74 L332 74 L332 86 L392 86 L392 62 L418 62 L418 86 L470 86 L470 70 L516 70 L516 86 L566 86 L566 64 L606 64 L606 86 L652 86 L652 72 L696 72 L696 86 L760 86 L760 120 L0 120 Z"/>
      </g>
      <g fill="#2a2521" fill-opacity=".30">
        <path d="M404 86 L404 30 L410 30 L410 24 L418 24 L418 30 L424 30 L424 86 Z"/>
        <path d="M396 34 L432 34 L432 31 L396 31 Z"/>
        <path d="M398 44 L430 44 L430 41 L398 41 Z"/>
        <path d="M400 54 L428 54 L428 51.4 L400 51.4 Z"/>
        <path d="M402 63 L426 63 L426 60.8 L402 60.8 Z"/>
        <path d="M403 71 L425 71 L425 69 L403 69 Z"/>
        <path d="M404 78 L424 78 L424 76.4 L404 76.4 Z"/>
      </g>
      <g fill="#f7f2e7" fill-opacity=".50">
        <rect x="100" y="76" width="10" height="8"/><rect x="120" y="76" width="10" height="8"/>
        <rect x="208" y="70" width="10" height="8"/><rect x="224" y="70" width="10" height="8"/>
        <rect x="300" y="78" width="10" height="6"/><rect x="316" y="78" width="10" height="6"/>
        <rect x="480" y="74" width="10" height="8"/><rect x="496" y="74" width="10" height="8"/>
        <rect x="576" y="68" width="10" height="8"/><rect x="592" y="68" width="10" height="8"/>
      </g>
      <rect x="0" y="88" width="760" height="1.6" fill="#4a5a5e" fill-opacity=".62"/>
      <rect x="0" y="93" width="760" height="1.2" fill="#c8a45c" fill-opacity=".60"/>
    </svg>"""
            , s, count=1, flags=re.S)

    # 裸标题补 display 字族
    for sel in ('.titlebar h2{', '.spec-title h2{', '.g-head h2{',
                '.g-card h3{', '.g-modal h4{', '.lead h1{'):
        i = s.index(sel); j = s.index('}', i)
        if 'font-family' not in s[i:j]:
            s = s[:j] + ';font-family:var(--font-display)' + s[j:]

    # 模板里英文名有两种写法：长写 CENTURY PLAZA（旧版）与缩写 CENTURY SQ（现行模板）。
    # 只替换长写会漏掉页眉与标题台的 CENTURY SQ，页眉读作「CENTURY SQ」而正文是友谊大厦。
    #
    # ⚠️ 大写名必须查表，⛔ 不能用 en.upper()：
    #    upper() 会把 'FriendshipBldg' 压成 'FRIENDSHIPBLDG'（丢词间空格），
    #    页眉靠 letter-spacing:.22em 撑着，肉眼看着像有空格，复制出来是一串连写。
    #    表里没有的主题回退到「驼峰拆词 + 全大写」，比 upper() 至少保住词界。
    EN_UPPER = {
        'panyu-rd':        'PANYU RD',
        'qiu-r':           'QIU R',
        'friendship-bldg': 'FRIENDSHIP BLDG',
        'century-sq':      'CENTURY SQ',
        'century-ave':     'CENTURY AVE',
        'guanglan-rd':     'GUANGLAN RD',
        'wanhang-fy':       'WANHANG FY',
        'fuzhou-rd':       'FUZHOU RD',
        'longhua-si':      'LONGHUA SI',
    }
    en_upper = EN_UPPER.get(theme) or re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', en).upper()
    s = (s.replace('Century Plaza', en).replace('CENTURY PLAZA', en_upper)
           .replace('CENTURY SQ', en_upper)
           .replace('世纪广场', zh))
    # 全局换名会把 century-ave 的「世纪广场所在站」误改成「世纪大道所在站」——
    # 世纪大道站是世纪广场所在站，反过来不成立，改回来
    if theme == 'century-ave':
        s = s.replace('世纪大道所在站', '世纪广场所在站')
    # 友谊大厦：上面那行已把 CENTURY PLAZA 换成 FRIENDSHIP BLDG，这里只需处理标题台的中文名
    if theme == 'friendship-bldg':
        s = s.replace('<h1>友谊大厦 <small>FRIENDSHIP BLDG</small></h1>',
                      '<h1>友谊大厦 <small>FRIENDSHIP BLDG</small></h1>')
    if theme in ('century-sq', 'century-ave'):
        # 世纪主题：蓝色格标签更正为 Line 9，色值不变。
        # 广兰路是 2 号线保留 Line 2；友谊大厦不用线路语义，走自己的图例替换。
        s = s.replace('>Line 2<', '>Line 9<').replace('SECONDARY / LINE 2', 'SECONDARY / LINE 9')
    if aero:
        # 色板是模板硬编码的世纪广场配色；不换就会标题台是 Aqua 蓝、色板第一格却是亮黄。
        swaps = [
            # 色板：用色比例条 + 角色图例（结构见模板 .spec-bar / .spec-legend）
            ('<div class="sec-h">Color palette · 用色比例</div>',
             '<div class="sec-h">Color palette · 用色比例</div>'),
            # 比例条 / 图例 / cap 的 hex 由 sync_palette 从 :root 统一填，此处不再硬编码
            ('<span class="cap">CATEGORY / LINE 4</span>', '<span class="cap">CATEGORY / VIOLET</span>'),
            ('<span class="cap">ALERT STRIPE / LINE 6</span>', '<span class="cap">ALERT STRIPE / CORAL</span>'),
            ('<span class="cap">SELECTED / FIXED YELLOW</span>', '<span class="cap">SELECTED / AQUA</span>'),
            # 材质圆名称：世纪广场四件 → Frutiger Aero 自己的材质词
            ('<div class="n">Raw Concrete</div>', '<div class="n">Aqua Glass</div>'),
            ('<div class="n">Polished Marble</div>', '<div class="n">Bubble</div>'),
            ('<div class="n">Brushed Steel</div>', '<div class="n">Porcelain</div>'),
            ('<div class="n">Frosted Glass</div>', '<div class="n">Frosted Aqua</div>'),
            ('<div class="n">Matte Tile</div>', '<div class="n">Glossy Tile</div>'),
            ('<div class="n">Matte Square</div>', '<div class="n">Glass Block</div>'),
            ('<div class="n">Green Lawn</div>', '<div class="n">Green Belt</div>'),
            ('<div class="n">Soft Daylight</div>', '<div class="n">Skylight</div>'),
            # 几何：柯布西耶模度 → 圆角与气泡
            ('<div class="sec-h">Geometry · 模度 1 : 1.618</div>', '<div class="sec-h">Geometry · 圆角 / 气泡节奏</div>'),
            # 组件卡：磨砂浮层 → Aqua 玻璃浮层
            ('<div class="sub">子标题 · FROSTED GLASS</div>', '<div class="sub">子标题 · AQUA GLASS</div>'),
            ('<span class="cap">FROSTED PANEL</span>', '<span class="cap">AQUA GLASS PANEL</span>'),
            # 导览面板：从「广场/公园/植被」导视 + 大理石混凝土文案，改成芯片厂园区 + Aero 材质
            ('<span class="pill pill-accent">广场</span>', '<span class="pill pill-accent">园区</span>'),
            ('<span class="pill pill-accent">公园</span>', '<span class="pill pill-accent">厂区</span>'),
            ('<span class="pill pill-accent">植被</span>', '<span class="pill pill-accent">绿化</span>'),
            ('<div class="k">PLAZA</div>', '<div class="k">CAMPUS</div>'),
            ('<h3>Century Sq</h3>', '<h3>广兰路</h3>'),
            ('<p>导览面板示例页。标题台用磨光大理石，卡片用清水混凝土；正文按标题—正文—注释三级排布，行距与留白服从模度。</p>',
             '<p>园区导览示例页。标题台用 Aqua 玻璃灯箱，卡片是白瓷托盘与玻璃糖；正文按标题—正文—注释三级排布，圆角与留白服从气泡节奏。</p>'),
            ('<h3>植被与休憩</h3>', '<h3>绿化与休憩</h3>'),
            ('<p>分类标记固定用 4 号线紫；草坪与瓷砖只作底部环境层，低透明度暗示材质，不盖住文字。</p>',
             '<p>分类标记固定用紫玻璃；绿带与亮釉砖只作底部环境层，低透明度暗示材质，不盖住文字。</p>'),
            ('<p>6 号线玫红仅作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>',
             '<p>暖珊瑚仅作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>'),
            ('<div class="sub">FROSTED GLASS / 磨砂浮层</div>', '<div class="sub">AQUA GLASS / 玻璃浮层</div>'),
            ('<p>半透明雾面、轻微背景模糊、淡天光蓝调；边缘只有柔和高光，不做厚倒角与强折射。</p>',
             '<p>玻璃质感＝镜面亮带＋外暗环＋接地反光；边缘有厚倒角与强折射，天光冷蓝调，气泡只作页脚点缀不压正文。</p>'),
            ('<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实广场公告</div>',
             '<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实园区公告</div>'),
            # 顶部 meta：世纪广场的路径与「磨砂玻璃版」改为广兰路事实
            ('<div class="mono">来雪亭Lesciotia / B 出口主题</div>',
             '<div class="mono">来雪亭Lesciotia / B 出口主题</div>'),
            ('<code>assets/themes/century-sq.css</code><br>\n      磨砂玻璃版 · 2026-11-19',
             '<code>assets/themes/guanglan-rd.css</code><br>\n      Aqua / Frutiger Aero · 2026-11-20'),
            # 中性色阶：世纪广场混凝土灰 → 广兰路玻璃蓝阶
            ('<i style="background:#E8E8E4"></i><b>#E8E8E4</b>', '<i style="background:#EAF7FF"></i><b>#EAF7FF</b>'),
            ('<i style="background:#B8B8B4"></i><b>#B8B8B4</b>', '<i style="background:#F2FBFB"></i><b>#F2FBFB</b>'),
            ('<i style="background:#F4F4F2"></i><b>#F4F4F2</b>', '<i style="background:#DFF4F7"></i><b>#DFF4F7</b>'),
            ('<i style="background:#DCDFE2"></i><b>#DCDFE2</b>', '<i style="background:#D9EFFB"></i><b>#D9EFFB</b>'),
            ('<i style="background:#C8D8E8"></i><b>#C8D8E8</b>', '<i style="background:#BFE3F2"></i><b>#BFE3F2</b>'),
            ('<i style="background:#96B878"></i><b>#96B878</b>', '<i style="background:#8FD4E8"></i><b>#8FD4E8</b>'),
            ('<i style="background:#EEEEEC"></i><b>#EEEEEC</b>', '<i style="background:#173B52"></i><b>#173B52</b>'),
            ('<i style="background:#222222"></i><b>#222222</b>', '<i style="background:#4B6C7D"></i><b>#4B6C7D</b>'),
            ('<i style="background:#777777"></i><b>#777777</b>', '<i style="background:#FFFFFF"></i><b>#FFFFFF</b>'),
        ]
        for old, new in swaps:
            if old not in s:
                print(f'WARN aero palette miss: {old[:60]}', file=sys.stderr)
                continue
            s = s.replace(old, new)

    # 色板 hex 由 sync_palette 从 :root 统一填（原 dark_palette_swaps 已删）


    if dark:
        # 页眉事实更正：世纪大道是从 century-sq（亮色版）fork 的暖光夜景版，
        # 不是从 guanglan-rd fork 的磨砂玻璃版（模板硬编码的是后者）。
        meta_swaps = [
            ('<div class="mono">来雪亭Lesciotia / B 出口主题</div>',
             '<div class="mono">来雪亭Lesciotia / B 出口主题</div>'),
            ('<code>assets/themes/century-sq.css</code><br>\n      磨砂玻璃版 · 2026-11-19',
             '<code>assets/themes/century-ave.css</code><br>\n      暖光夜景版 · 2026-11-19'),
            # 材质圆词：亮色版的「混凝土/大理石/钢」在夜景里对应暖光酚醛
            ('<div class="n">Raw Concrete</div>', '<div class="n">Warm Concrete</div>'),
            ('<div class="n">Polished Marble</div>', '<div class="n">Black-Gold Marble</div>'),
            ('<div class="n">Brushed Steel</div>', '<div class="n">Brushed Bronze</div>'),
            ('<div class="n">Frosted Glass</div>', '<div class="n">Lamp Panel</div>'),
            ('<div class="n">Matte Tile</div>', '<div class="n">Phenol Tile</div>'),
            ('<div class="n">Matte Square</div>', '<div class="n">Phenol Grid</div>'),
            ('<div class="n">Green Lawn</div>', '<div class="n">Green Phenol</div>'),
            ('<div class="n">Soft Daylight</div>', '<div class="n">Sodium Glow</div>'),
            # 组件卡标注：模板写死亮色版色值，暗色版必须同步成主题真实值
            ('<span class="cap">PRIMARY / #F9D328</span>', '<span class="cap">PRIMARY / #F5B942</span>'),
            ('<span class="cap">SELECTED / FIXED YELLOW</span>', '<span class="cap">SELECTED / SODIUM YELLOW</span>'),
            # 中性色阶：模板写死世纪广场亮色灰，暗底上会跳成一片浅块；
            # 换成世纪大道主题 :root 的真实暗色阶（底色 / 面板 / 米白 / 黑金 / 酚醛 / 文字三级）
            ('<i style="background:#E8E8E4"></i><b>#E8E8E4</b>', '<i style="background:#1A1410"></i><b>#1A1410</b>'),
            ('<i style="background:#B8B8B4"></i><b>#B8B8B4</b>', '<i style="background:#221B15"></i><b>#221B15</b>'),
            ('<i style="background:#F4F4F2"></i><b>#F4F4F2</b>', '<i style="background:#2D231C"></i><b>#2D231C</b>'),
            ('<i style="background:#DCDFE2"></i><b>#DCDFE2</b>', '<i style="background:#0F172A"></i><b>#0F172A</b>'),
            ('<i style="background:#C8D8E8"></i><b>#C8D8E8</b>', '<i style="background:#EDE4D3"></i><b>#EDE4D3</b>'),
            ('<i style="background:#96B878"></i><b>#96B878</b>', '<i style="background:#6F8F5A"></i><b>#6F8F5A</b>'),
            ('<i style="background:#EEEEEC"></i><b>#EEEEEC</b>', '<i style="background:#EFE6D2"></i><b>#EFE6D2</b>'),
            ('<i style="background:#222222"></i><b>#222222</b>', '<i style="background:#B7A995"></i><b>#B7A995</b>'),
            ('<i style="background:#777777"></i><b>#777777</b>', '<i style="background:#9C8D78"></i><b>#9C8D78</b>'),
        ]
        for old, new in meta_swaps:
            # 色板标签可能已被 sync_palette 先行写入正确值，属冗余替换，不报 WARN
            if old not in s:
                continue
                continue
            s = s.replace(old, new, 1)

        # ---- 第三屏导览面板：整段还是世纪广场的公园导览（广场/餐饮/公园/植被/休憩），
        #      世纪大道是地铁站台，换成站台语汇；导航七项全实心主色也是模板缺陷，
        #      改成「当前项实心、其余描边幽灵」的常规层级。
        ave_guide = [
            ('<span class="pill pill-accent">首页</span>\n        <span class="pill pill-accent">广场</span>\n        <span class="pill pill-accent">餐饮</span>\n        <span class="pill pill-accent">服务</span>\n        <span class="pill pill-accent">公园</span>\n        <span class="pill pill-accent">植被</span>\n        <span class="pill pill-accent">休憩</span>\n        <span class="pill">关于我们</span>',
             '<span class="pill pill-accent">首页</span>\n        <span class="pill pill-ghost">站台</span>\n        <span class="pill pill-ghost">换乘</span>\n        <span class="pill pill-ghost">出口</span>\n        <span class="pill pill-ghost">首末班</span>\n        <span class="pill pill-ghost">无障碍</span>\n        <span class="pill pill-ghost">周边</span>\n        <span class="pill">关于我们</span>'),
            ('<div class="k">PLAZA</div>\n          <h3>Century Sq</h3>\n          <p>导览面板示例页。标题台用磨光大理石，卡片用清水混凝土；正文按标题—正文—注释三级排布，行距与留白服从模度。</p>',
             '<div class="k">PLATFORM</div>\n          <h3>世纪大道</h3>\n          <p>站台导览示例页。标题台用黑金大理石，卡片用暖酚醛板；正文按标题—正文—注释三级排布，行距与留白服从模度。</p>'),
            ('<span class="tag">Category</span>\n          <h3>植被与休憩</h3>\n          <p>分类标记固定用 4 号线紫；草坪与瓷砖只作底部环境层，低透明度暗示材质，不盖住文字。</p>',
             '<span class="tag">Category</span>\n          <h3>换乘与导向</h3>\n          <p>分类标记固定用紫酚醛；钠灯黄只作灯箱与主按钮，低透明度暗示材质，不盖住文字。</p>'),
            ('<p>6 号线玫红仅作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>',
             '<p>玫红酚醛仅作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>'),
            ('<div class="sub">FROSTED GLASS / 磨砂浮层</div>\n        <p>半透明雾面、轻微背景模糊、淡天光蓝调；边缘只有柔和高光，不做厚倒角与强折射。</p>',
             '<div class="sub">PHENOL PANEL / 酚醛灯箱</div>\n        <p>暖酚醛板面、钠灯透光、边缘一圈细黄光；不做厚倒角与强折射，暗底上靠明度立边界。</p>'),
            ('<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实广场公告</div>',
             '<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实站点公告</div>'),
        ]
        for old, new in ave_guide:
            if old not in s:
                print(f'WARN ave guide miss: {old[:56]}', file=sys.stderr)
                continue
            s = s.replace(old, new, 1)


    if theme == 'friendship-bldg':
        # ---- 色板：世纪广场亮黄蓝紫玫红 -> 友谊大厦 鎏金 / 红玻璃 / 墨绿 / 薄荷 ----
        fb_swaps = [
            # 比例条 / 图例 hex 由 sync_palette 从 :root 统一填
            # 中性色阶：换成友谊大厦的乳黄石 / 汉白玉 / 水磨石 / 金阶 / 文字三级
            ('<i style="background:#E8E8E4"></i><b>#E8E8E4</b>', '<i style="background:#EFE3C6"></i><b>#EFE3C6</b>'),
            ('<i style="background:#B8B8B4"></i><b>#B8B8B4</b>', '<i style="background:#D6BE93"></i><b>#D6BE93</b>'),
            ('<i style="background:#F4F4F2"></i><b>#F4F4F2</b>', '<i style="background:#FBF6EC"></i><b>#FBF6EC</b>'),
            ('<i style="background:#DCDFE2"></i><b>#DCDFE2</b>', '<i style="background:#D9E1D2"></i><b>#D9E1D2</b>'),
            ('<i style="background:#C8D8E8"></i><b>#C8D8E8</b>', '<i style="background:#B9C6B4"></i><b>#B9C6B4</b>'),
            ('<i style="background:#96B878"></i><b>#96B878</b>', '<i style="background:#DDBE5B"></i><b>#DDBE5B</b>'),
            ('<i style="background:#EEEEEC"></i><b>#EEEEEC</b>', '<i style="background:#F2E8D2"></i><b>#F2E8D2</b>'),
            ('<i style="background:#222222"></i><b>#222222</b>', '<i style="background:#26221B"></i><b>#26221B</b>'),
            ('<i style="background:#777777"></i><b>#777777</b>', '<i style="background:#6A5D48"></i><b>#6A5D48</b>'),
            # 材质圆：类名与名称一起换。
            # 主题 CSS 里定义了 .fb-stone/.fb-terrazzo/.fb-gold/.fb-mint/.fb-redglass/
            # .fb-birch/.fb-daylight 等真材质，模板却用世纪广场的通用 .d-*，
            # 结果「鎏金塔身」显示拉丝不锈钢、「红玻璃星」显示瓷砖格——最核心的四个材质全没画出来。
            ('<div class="disc d-concrete"></div><div class="n">Raw Concrete</div>',
             '<div class="disc fb-stone"></div><div class="n">乳黄水刷石</div>'),
            ('<div class="disc d-marble"></div><div class="n">Polished Marble</div>',
             '<div class="disc cp-marble"></div><div class="n">汉白玉台基</div>'),
            ('<div class="disc d-steel"></div><div class="n">Brushed Steel</div>',
             '<div class="disc fb-gold"></div><div class="n">鎏金塔身</div>'),
            ('<div class="disc d-frost"></div><div class="n">Frosted Glass</div>',
             '<div class="disc fb-terrazzo"></div><div class="n">彩色水磨石</div>'),
            ('<div class="disc d-tile"></div><div class="n">Matte Tile</div>',
             '<div class="disc fb-mint"></div><div class="n">薄荷穹顶</div>'),
            ('<div class="disc d-square"></div><div class="n">Matte Square</div>',
             '<div class="disc fb-redglass"></div><div class="n">红玻璃星</div>'),
            ('<div class="disc d-lawn"></div><div class="n">Green Lawn</div>',
             '<div class="disc fb-birch"></div><div class="n">白桦木饰面</div>'),
            ('<div class="disc d-day"></div><div class="n">Soft Daylight</div>',
             '<div class="disc fb-daylight"></div><div class="n">漫射顶光</div>'),
            # 几何标题：模度 -> 中轴对称
            ('Geometry · 模度 1 : 1.618', 'Geometry · 模度 1 : 1.618 · 中轴对称'),
            # 组件卡标注：友谊大厦不是地铁站，⛔ 不许留 Line 2 / Line 4 这套线号
            ('<span class="cap">SECONDARY / LINE 2</span>', '<span class="cap">SECONDARY / INK</span>'),
            ('<span class="cap">CATEGORY / LINE 4</span>', '<span class="cap">CATEGORY / MOSS</span>'),
            ('<span class="cap">ALERT STRIPE / LINE 6</span>', '<span class="cap">ALERT / RED GLASS</span>'),
            ('<span class="cap">SELECTED / FIXED YELLOW</span>', '<span class="cap">SELECTED / GOLD</span>'),
            # 页眉事实：从 century-sq 的骨架重建，材质换成石墙/汉白玉/水磨石/鎏金
            ('<div class="mono">来雪亭Lesciotia / B 出口主题</div>',
             '<div class="mono">来雪亭Lesciotia / B 出口主题</div>'),
            ('<code>assets/themes/century-sq.css</code><br>\n      磨砂玻璃版 · 2026-11-19',
             '<code>assets/themes/friendship-bldg.css</code><br>\n      石墙 · 汉白玉 · 水磨石 · 鎏金 · 2026-11-20'),
            # 主按钮必须是鎏金（主题的 .pill-accent），模板用的是次级 .pill，主色缺席
            ('<span class="pill">主按钮</span>', '<span class="pill pill-accent">主按钮</span>'),
            ('<span class="pill">Submit</span>', '<span class="pill pill-accent">提交</span>'),
            # 导航组：当前项实心鎏金，其余描边幽灵（模板是首页实心 + 服务/产品也实心）
            ('<span class="pill">首页</span><span class="pill pill-ghost">服务</span><span class="pill pill-ghost">产品</span>',
             '<span class="pill pill-accent">首页</span><span class="pill pill-ghost">服务</span><span class="pill pill-ghost">产品</span>'),
            # 几何网格：6 列随机散布 -> 8 列中轴镜像（读作立面开间，不是随机铺装）
            #   中轴两列为鎏金实心，次轴金描边，外翼墨绿细边，最外留空
            ('<i class="on"></i><i></i><i></i><i class="gl"></i><i></i><i></i>\n            <i></i><i class="on"></i><i></i><i></i><i class="gl"></i><i></i>',
             '<i></i><i class="wing"></i><i class="gl"></i><i class="on"></i><i class="on"></i><i class="gl"></i><i class="wing"></i><i></i>\n            <i></i><i class="wing"></i><i class="gl"></i><i class="on"></i><i class="on"></i><i class="gl"></i><i class="wing"></i><i></i>'),
            # ---- 第三屏导览面板：整段是世纪广场的公园导览（广场/餐饮/公园/植被/休憩），
            #      换成友谊大厦的展览建筑语汇，否则第三屏和三屏前两屏不是同一个主题 ----
            ('<span class="pill pill-accent">首页</span>\n        <span class="pill pill-accent">广场</span>\n        <span class="pill pill-accent">餐饮</span>\n        <span class="pill pill-accent">服务</span>\n        <span class="pill pill-accent">公园</span>\n        <span class="pill pill-accent">植被</span>\n        <span class="pill pill-accent">休憩</span>\n        <span class="pill">关于我们</span>',
             '<span class="pill pill-accent">首页</span>\n        <span class="pill pill-ghost">序馆</span>\n        <span class="pill pill-ghost">中央大厅</span>\n        <span class="pill pill-ghost">展览</span>\n        <span class="pill pill-ghost">会议</span>\n        <span class="pill pill-ghost">鎏金塔</span>\n        <span class="pill">关于我们</span>'),
            ('<div class="k">PLAZA</div>\n          <h3>Century Sq</h3>\n          <p>导览面板示例页。标题台用磨光大理石，卡片用清水混凝土；正文按标题—正文—注释三级排布，行距与留白服从模度。</p>',
             '<div class="k">PLAZA</div>\n          <h3>友谊大厦</h3>\n          <p>导览面板示例页。标题台用汉白玉，卡片用乳黄水刷石；正文按标题—正文—注释三级排布，行距与留白服从模度，全页中轴对称。</p>'),
            ('<span class="tag">Category</span>\n          <h3>植被与休憩</h3>\n          <p>分类标记固定用 4 号线紫；草坪与瓷砖只作底部环境层，低透明度暗示材质，不盖住文字。</p>',
             '<span class="tag">Category</span>\n          <h3>序馆与穹顶</h3>\n          <p>分类标记固定用墨绿；水磨石地坪只作底部环境层，低透明度暗示材质，不盖住文字。</p>'),
            ('<div class="k">MESSAGES</div>\n          <h3>提示信息</h3>\n          <p>6 号线玫红仅作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>',
             '<div class="k">MESSAGES</div>\n          <h3>提示信息</h3>\n          <p>红玻璃只作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>'),
            ('<div class="sub">FROSTED GLASS / 磨砂浮层</div>\n        <p>半透明雾面、轻微背景模糊、淡天光蓝调；边缘只有柔和高光，不做厚倒角与强折射。</p>',
             '<div class="sub">MARBLE INLAY / 汉白玉嵌板</div>\n        <p>实心汉白玉面、无背景模糊、暖白漫射；边缘只有一道细金线，不做厚倒角与强折射。</p>'),
            ('<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实广场公告</div>',
             '<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实场馆公告</div>'),
            ('<div class="sub">子标题 · FROSTED GLASS</div>', '<div class="sub">子标题 · MARBLE INLAY</div>'),
            ('<span class="cap">FROSTED PANEL</span>', '<span class="cap">MARBLE PANEL</span>'),
            # 注：CENTURY PLAZA 已被上面的全局换名处理，此处为兜底，命中与否都不报 WARN
        ]
        for old, new in fb_swaps:
            if old not in s:
                print(f'WARN fb swap miss: {old[:64]}', file=sys.stderr)
                continue
            s = s.replace(old, new, 1)
        # 天际线：模板是 28 个错落方盒（世纪广场城市轮廓），整段换成中轴对称塔楼剪影
        s = re.sub(
            r'<svg class="skyline".*?</svg>',
            '''<svg class="fb-skyline" viewBox="0 0 760 110" preserveAspectRatio="none" aria-hidden="true">
      <g fill="#B08A2B">
        <!-- 中轴对称的连续剪影：端部序馆 → 外翼 → 翼楼 → 中央大厅 → 鎏金钢塔，一条底边收口 -->
        <path d="M60,92 L130,92 L130,80 L210,80 L210,62 L300,62 L300,76
                 L356,76 L356,52 L368,52 L368,26 L372,26 L372,8
                 L388,8 L388,26 L392,26 L392,52 L404,52 L404,76
                 L460,76 L460,62 L550,62 L550,80 L630,80 L630,92
                 L700,92 L700,110 L60,110 Z"/>
        <!-- 塔顶红玻璃五角星（真五角星，非三角） -->
        <polygon points="380,-2 382.2,3.4 388,3.4 383.3,7 385.1,12.4 380,9 374.9,12.4 376.7,7 372,3.4 377.8,3.4"/>
        <!-- 柱廊：中轴两侧严格对称 -->
        <rect x="306" y="80" width="3" height="30"/><rect x="320" y="80" width="3" height="30"/>
        <rect x="334" y="80" width="3" height="30"/><rect x="348" y="80" width="3" height="30"/>
        <rect x="409" y="80" width="3" height="30"/><rect x="423" y="80" width="3" height="30"/>
        <rect x="437" y="80" width="3" height="30"/><rect x="451" y="80" width="3" height="30"/>
      </g>
    </svg>''',
            s, count=1, flags=re.S)
        # ---- 标题字体提示条：摇醒青年黑因授权限制不随包，未安装时回落宋骨黑体 ----
        # 为什么不用 JS 探测：模板是纯静态单文件，加脚本会破坏「自包含、可直接双击打开」
        # 的承诺，也让 check-preview-sync 的比对变复杂。提示条写成静态说明，
        # 措辞用「如未安装」而不是「未安装」，装了字体的用户读着也不别扭。
        fb_notice = '''<style>
.fb-fontnote{width:1080px;margin:0 auto 22px;display:flex;gap:14px;align-items:flex-start;
  padding:13px 18px;background:rgba(221,190,91,.13);border:1px solid rgba(159,124,39,.34);
  border-left:3px solid var(--gold);border-radius:var(--radius);font-size:13px;line-height:1.75;
  color:var(--text-2)}
.fb-fontnote b{flex:0 0 auto;font-family:var(--font-button);font-weight:400;font-size:12px;
  letter-spacing:.1em;color:var(--gold-lo);padding-top:2px}
.fb-fontnote span{flex:1 1 auto}
.fb-fontnote em{font-style:normal;color:var(--text-1);border-bottom:1px solid rgba(159,124,39,.5)}
.fb-fontnote a{color:var(--gold-lo);text-decoration:none;border-bottom:1px solid rgba(159,124,39,.5)}
</style>
<div class="fb-fontnote">
  <b>标题字体</b>
  <span>本主题标题用 <em>摇醒青年黑</em>。该字体因授权范围不含「网页字体嵌入」，
  不随本库分发；未安装时标题自动回落 <em>宋骨黑体</em>（随包内化，同为黑体，版式与色板不受影响）。
  想要原设计的撇点宋意，可自行下载安装摇醒青年黑（作者声明永久免费商用），刷新即生效。<br>
  两级内化字体都没命中时，最后兜底 <em>系统黑体粗体</em>（PingFang SC Semibold / STHeiti Medium）——
  标题规则写 400，所以兜底层必须点名粗字重，否则会掉成一层细黑，跟前面两档厚度差一截。</span>
</div>
'''
        s = s.replace('<div class="wrap">', fb_notice + '<div class="wrap">', 1)

    if theme == 'panyu-rd':
        # ---- 标题字体提示条：爱点风雅黑因授权限制不随包，未安装时回落宋骨黑体 ----
        # 与 friendship-bldg 同因同法（zfont font_657：嵌入 not、衍生 not），
        # 只用静态 HTML，不加 JS 探测。配色换成本主题的赤陶 + 石灰华。
        py_notice = '''<style>
.py-fontnote{width:1080px;margin:0 auto 22px;display:flex;gap:14px;align-items:flex-start;
  padding:13px 18px;background:rgba(186,74,51,.09);border:1px solid rgba(186,74,51,.30);
  border-left:3px solid var(--accent);border-radius:var(--radius);font-size:13px;line-height:1.75;
  color:var(--text-2)}
.py-fontnote b{flex:0 0 auto;font-family:var(--font-button);font-weight:400;font-size:12px;
  letter-spacing:.1em;color:var(--accent);padding-top:2px}
.py-fontnote span{flex:1 1 auto}
.py-fontnote em{font-style:normal;color:var(--text-1);border-bottom:1px solid rgba(186,74,51,.5)}
</style>
<div class="py-fontnote">
  <b>标题字体</b>
  <span>本主题标题用 <em>爱点风雅黑</em>。该字体因授权范围不含「网页字体嵌入」，
  不随本库分发；未安装时标题自动回落 <em>宋骨黑体</em>（同为黑体，版式与色板不受影响）。
  想要原设计的方硬转折，可自行下载安装爱点风雅黑（作者声明永久免费商用），刷新即生效。</span>
</div>
'''
        s = s.replace('<div class="wrap">', py_notice + '<div class="wrap">', 1)

    if theme == 'longhua-si':
        # ---- 标题字体提示条：爨八体内化随包；法华文楷降为可选提示 ----
        # 2026-11-21：标题改用爨八体（作者声明授权，可随包）。
        # 法华文楷因 zfont font_777 标「嵌入 not / 衍生 not」，只作提示、不随包。
        # 只用静态 HTML，不加 JS 探测。配色用本主题的檀赭 + 香灰底。
        lh_notice = '''<style>
.lh-fontnote{width:1080px;margin:0 auto 22px;display:flex;gap:14px;align-items:flex-start;
  padding:13px 18px;background:rgba(95,46,28,.07);border:1px solid rgba(95,46,28,.26);
  border-left:3px solid var(--sandal);border-radius:var(--radius);font-size:13px;line-height:1.75;
  color:var(--text-2)}
.lh-fontnote b{flex:0 0 auto;font-family:var(--font-button);font-weight:400;font-size:12px;
  letter-spacing:.1em;color:var(--sandal);padding-top:2px}
.lh-fontnote span{flex:1 1 auto}
.lh-fontnote em{font-style:normal;color:var(--text-1);border-bottom:1px solid rgba(95,46,28,.45)}
</style>
<div class="lh-fontnote">
  <b>标题字体</b>
  <span>本主题标题用 <em>爨八体</em>（张济海独创书法新书体，作者声明授权免费商用，
  随包内化 3.4 MB / 3757 字）。爨八体<b>只有汉字</b>——标点、数字、拉丁字母全部不在字库内，
  这些字符自动回落 <em>霞鹜文楷</em>（SIL OFL 1.1，随包内化）。所以标题里「·」「，」「2026」
  会呈现楷书笔意，这是设计上的混排，不是缺字。<br>
  另可选：装了 <em>法华文楷</em>（作者声明免费商用）的用户，把 --ff-title 首位改成
  '法华文楷标准版' 即可切到敦煌写经笔意。该字体授权不含网页嵌入，故本库不随包分发。</span>
</div>
'''
        s = s.replace('<div class="wrap">', lh_notice + '<div class="wrap">', 1)

    if theme == 'qiu-r':
        # ---- 虬江：色板 / 材质圆 / 导览面板语汇 / 页眉事实，全部换成河与纸 ----
        qiu_swaps = [
            # 组件卡标注：虬江没有地铁线号，也没有「固定黄」，⛔ 不许沿用世纪广场的标注
            ('<span class="cap">SECONDARY / LINE 2</span>', '<span class="cap">SECONDARY / WATER LO</span>'),
            ('<span class="cap">CATEGORY / LINE 4</span>', '<span class="cap">CATEGORY / BRICK</span>'),
            ('<span class="cap">ALERT STRIPE / LINE 6</span>', '<span class="cap">ALERT / DEEP BRICK</span>'),
            ('<span class="cap">SELECTED / FIXED YELLOW</span>', '<span class="cap">SELECTED / RIVER STONE</span>'),
            # 材质圆：模板的通用 .d-* 换成主题自带的 qj-* 方片
            ('<div class="disc d-concrete"></div><div class="n">Raw Concrete</div>',
             '<div class="disc qj-brick"></div><div class="n">青砖驳岸</div>'),
            ('<div class="disc d-marble"></div><div class="n">Polished Marble</div>',
             '<div class="disc qj-stone"></div><div class="n">河埠石</div>'),
            ('<div class="disc d-steel"></div><div class="n">Brushed Steel</div>',
             '<div class="disc qj-wave"></div><div class="n">河面水线</div>'),
            ('<div class="disc d-frost"></div><div class="n">Frosted Glass</div>',
             '<div class="disc qj-grid"></div><div class="n">方格稿纸</div>'),
            ('<div class="disc d-tile"></div><div class="n">Matte Tile</div>',
             '<div class="disc cp-tile"></div><div class="n">青砖铺面</div>'),
            ('<div class="disc d-square"></div><div class="n">Matte Square</div>',
             '<div class="disc qj-paper"></div><div class="n">硫酸纸</div>'),
            ('<div class="disc d-lawn"></div><div class="n">Green Lawn</div>',
             '<div class="disc cp-steel"></div><div class="n">河青实漆</div>'),
            ('<div class="disc d-day"></div><div class="n">Soft Daylight</div>',
             '<div class="disc qj-deep"></div><div class="n">深水面</div>'),
            # 导航：当前项实心河青，其余描边幽灵
            ('<span class="pill pill-accent">首页</span>\n        <span class="pill pill-accent">广场</span>\n        <span class="pill pill-accent">餐饮</span>\n        <span class="pill pill-accent">服务</span>\n        <span class="pill pill-accent">公园</span>\n        <span class="pill pill-accent">植被</span>\n        <span class="pill pill-accent">休憩</span>\n        <span class="pill">关于我们</span>',
             '<span class="pill pill-accent">首页</span>\n        <span class="pill pill-ghost">河道</span>\n        <span class="pill pill-ghost">驳岸</span>\n        <span class="pill pill-ghost">图版</span>\n        <span class="pill pill-ghost">脚注</span>\n        <span class="pill pill-ghost">水线</span>\n        <span class="pill pill-ghost">引文</span>\n        <span class="pill">关于我们</span>'),
            ('<div class="k">PLAZA</div>\n          <h3>Century Sq</h3>\n          <p>导览面板示例页。标题台用磨光大理石，卡片用清水混凝土；正文按标题—正文—注释三级排布，行距与留白服从模度。</p>',
             '<div class="k">RIVERBANK</div>\n          <h3>虬江</h3>\n          <p>导览面板示例页。标题台用河埠石，卡片用方格稿纸；正文按标题—正文—注释三级排布，行距 1.7、方格 26px 一档。</p>'),
            ('<span class="tag">Category</span>\n          <h3>植被与休憩</h3>\n          <p>分类标记固定用 4 号线紫；草坪与瓷砖只作底部环境层，低透明度暗示材质，不盖住文字。</p>',
             '<span class="tag">Category</span>\n          <h3>字纸与图版</h3>\n          <p>分类标记固定用砖红；方格与水线只作底部环境层，低透明度暗示材质，不盖住文字。</p>'),
            ('<p>6 号线玫红仅作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>',
             '<p>砖红仅作卡顶细条、图版号与批注条，绝不铺底。此处为版式占位文案，非真实公告。</p>'),
            ('<div class="sub">FROSTED GLASS / 磨砂浮层</div>\n        <p>半透明雾面、轻微背景模糊、淡天光蓝调；边缘只有柔和高光，不做厚倒角与强折射。</p>',
             '<div class="sub">TRACING PAPER / 硫酸纸浮层</div>\n        <p>半透纸白、极轻模糊、纸纤维可见；边缘只有一圈纸色细边，不做厚倒角与玻璃高光。</p>'),
            ('<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实广场公告</div>',
             '<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实河道公告</div>'),
            ('<code>assets/themes/century-sq.css</code><br>\n      磨砂玻璃版 · 2026-11-19',
             '<code>assets/themes/qiu-r.css</code><br>\n      宣纸 · 河青 · 靛蓝 · 砖红 · 2026-11-20'),
            # ⛔ 主按钮不许改成 pill-accent：虬江的 .pill 本身就是河青实心主色，
            #    改成 accent 就与次按钮（靛描边）同形，层级全塌（2026-11-20 修）。只换文案，不动类名。
            ('<span class="pill">主按钮</span>', '<span class="pill">主按钮</span>'),
            ('<span class="pill">Submit</span>', '<span class="pill">提交</span>'),
        ]
        for old, new in qiu_swaps:
            if old not in s:
                print(f'WARN qiu swap miss: {old[:64]}', file=sys.stderr)
                continue
            s = s.replace(old, new, 1)
        # 天际线：28 个错落方盒（CBD 轮廓）→ 三道河面波线 + 青砖岸线
        s = re.sub(
            r'<svg class="skyline".*?</svg>',
            """<svg class="qj-skyline" viewBox="0 0 760 110" preserveAspectRatio="none" aria-hidden="true">
      <g fill="none" stroke="#3C757E" stroke-width="1">
        <path d="M0 26 C60 22 100 30 160 26 C220 22 260 30 320 26 C380 22 420 30 480 26 C540 22 580 30 640 26 C700 22 730 30 760 26" stroke-opacity=".42"/>
        <path d="M0 44 C60 40 100 48 160 44 C220 40 260 48 320 44 C380 40 420 48 480 44 C540 40 580 48 640 44 C700 40 730 48 760 44" stroke-opacity=".28"/>
        <path d="M0 62 C60 58 100 66 160 62 C220 58 260 66 320 62 C380 58 420 66 480 62 C540 58 580 66 640 62 C700 58 730 66 760 62" stroke-opacity=".18"/>
      </g>
      <rect x="0" y="74" width="760" height="2" fill="#8A3932" fill-opacity=".55"/>
      <rect x="0" y="76" width="760" height="34" fill="#6F7873" fill-opacity=".30"/>
      <g fill="#565E59" fill-opacity=".45">
        <rect x="0" y="76" width="760" height="1"/><rect x="0" y="104" width="760" height="1"/>
        <rect x="0" y="76" width="1" height="28"/><rect x="60" y="76" width="1" height="28"/><rect x="120" y="76" width="1" height="28"/>
        <rect x="180" y="76" width="1" height="28"/><rect x="240" y="76" width="1" height="28"/><rect x="300" y="76" width="1" height="28"/>
        <rect x="360" y="76" width="1" height="28"/><rect x="420" y="76" width="1" height="28"/><rect x="480" y="76" width="1" height="28"/>
        <rect x="540" y="76" width="1" height="28"/><rect x="600" y="76" width="1" height="28"/><rect x="660" y="76" width="1" height="28"/>
        <rect x="720" y="76" width="1" height="28"/>
      </g>
    </svg>""",
            s, count=1, flags=re.S)

    if theme == 'panyu-rd':
        # ---- 番禺路：新粗野主义 × 意大利。色板 hex 由 sync_palette 填，
        #      这里只换「语义标签 / 材质圆 / 导览语汇 / 页眉事实 / 天际线」----
        pg_swaps = [
            ('<span class="cap">SECONDARY / LINE 2</span>', '<span class="cap">SECONDARY / INK</span>'),
            ('<span class="cap">CATEGORY / LINE 4</span>', '<span class="cap">CATEGORY / OCHRE</span>'),
            ('<span class="cap">ALERT STRIPE / LINE 6</span>', '<span class="cap">ALERT / TERRACOTTA</span>'),
            ('<span class="cap">SELECTED / FIXED YELLOW</span>', '<span class="cap">SELECTED / ARCH</span>'),
            ('<span class="cap">FROSTED PANEL</span>', '<span class="cap">SHADOW / 浮层</span>'),
            # 材质圆：模板的通用 .d-* 换成主题自带的 pg-* 方片
            ('<div class="disc d-concrete"></div><div class="n">Raw Concrete</div>',
             '<div class="disc pg-terrazzo"></div><div class="n">水磨石</div>'),
            ('<div class="disc d-marble"></div><div class="n">Polished Marble</div>',
             '<div class="disc pg-flute"></div><div class="n">柱身凹槽</div>'),
            ('<div class="disc d-steel"></div><div class="n">Brushed Steel</div>',
             '<div class="disc pg-terracotta"></div><div class="n">赤陶砖</div>'),
            ('<div class="disc d-frost"></div><div class="n">Frosted Glass</div>',
             '<div class="disc pg-travertine"></div><div class="n">石灰华</div>'),
            ('<div class="disc d-tile"></div><div class="n">Matte Tile</div>',
             '<div class="disc pg-ochre"></div><div class="n">赭黄平涂</div>'),
            ('<div class="disc d-square"></div><div class="n">Matte Square</div>',
             '<div class="disc pg-ultra"></div><div class="n">群青平涂</div>'),
            ('<div class="disc d-lawn"></div><div class="n">Green Lawn</div>',
             '<div class="disc pg-sage"></div><div class="n">鼠尾草</div>'),
            ('<div class="disc d-day"></div><div class="n">Soft Daylight</div>',
             '<div class="disc pg-ink"></div><div class="n">墨黑</div>'),
            # 几何标题：模度 → 拱与开间（数值仍是模度，改的是它在这一页的读法）
            ('<div class="sec-h">Geometry · 模度 1 : 1.618</div>',
             '<div class="sec-h">Geometry · 模度 1 : 1.618 · 拱与开间</div>'),
            # 导航：当前项赭黄实心，其余墨线幽灵
            ('<span class="pill pill-accent">首页</span>\n        <span class="pill pill-accent">广场</span>\n        <span class="pill pill-accent">餐饮</span>\n        <span class="pill pill-accent">服务</span>\n        <span class="pill pill-accent">公园</span>\n        <span class="pill pill-accent">植被</span>\n        <span class="pill pill-accent">休憩</span>\n        <span class="pill">关于我们</span>',
             '<span class="pill pill-accent">首页</span>\n        <span class="pill pill-ghost">拱廊</span>\n        <span class="pill pill-ghost">柱式</span>\n        <span class="pill pill-ghost">赤陶</span>\n        <span class="pill pill-ghost">水磨石</span>\n        <span class="pill pill-ghost">图版</span>\n        <span class="pill">关于我们</span>'),
            ('<div class="k">PLAZA</div>\n          <h3>Century Sq</h3>\n          <p>导览面板示例页。标题台用磨光大理石，卡片用清水混凝土；正文按标题—正文—注释三级排布，行距与留白服从模度。</p>',
             '<div class="k">ARCADE</div>\n          <h3>番禺路</h3>\n          <p>导览面板示例页。标题台用拱廊剖面，卡片用石灰华暖白；正文按标题—正文—注释三级排布，行距 1.7，一屏只留一个拱。</p>'),
            ('<span class="tag">Category</span>\n          <h3>植被与休憩</h3>\n          <p>分类标记固定用 4 号线紫；草坪与瓷砖只作底部环境层，低透明度暗示材质，不盖住文字。</p>',
             '<span class="tag">Category</span>\n          <h3>拱与柱</h3>\n          <p>分类标记固定用赭黄；赤陶砖与水磨石只作底部环境层，低透明度暗示材质，不盖住文字。</p>'),
            ('<p>6 号线玫红仅作卡顶细条与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>',
             '<p>赤陶仅作卡顶细条、图版号与轻提示，绝不铺底。此处为版式占位文案，非真实公告。</p>'),
            ('<div class="sub">FROSTED GLASS / 磨砂浮层</div>\n        <p>半透明雾面、轻微背景模糊、淡天光蓝调；边缘只有柔和高光，不做厚倒角与强折射。</p>',
             '<div class="sub">HARD SHADOW / 硬投影浮层</div>\n        <p>实心纸面、3px 墨黑框、4px 实心硬投影；零模糊、零半透明，抬起来的那一下全靠影子的偏移量。</p>'),
            ('<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实广场公告</div>',
             '<div class="g-foot">示例文案 · 用于展示层级与材质，不代表真实路段公告</div>'),
            ('<code>assets/themes/century-sq.css</code><br>\n      磨砂玻璃版 · 2026-11-19',
             '<code>assets/themes/panyu-rd.css</code><br>\n      拱廊 · 赤陶砖 · 水磨石 · 2026-11-20'),
            ('<span class="pill">Submit</span>', '<span class="pill">提交</span>'),
        ]
        for old, new in pg_swaps:
            if old not in s:
                print(f'WARN panyu swap miss: {old[:64]}', file=sys.stderr)
                # 调试：看 s 里对应位置的真实内容
                continue
            s = s.replace(old, new, 1)
        # 模板自带的环境层是「草坪 / 天空 / 钢面」，与番禺路互斥：
        # 草坪换砖行、天空换石灰华、导览面板的玻璃与钢导航换硬边纸面。
        s = s.replace('<div class="g-nav cp-steel">', '<div class="g-nav pg-nav">', 1)
        i = s.rfind('</style>')
        s = s[:i] + '''
/* —— panyu 补丁：把模板的草坪 / 天空 / 钢面换成石灰华与砖 —— */
.board::after{
  height:56px;border-top:3px solid #141414;
  background:
    repeating-linear-gradient(0deg,transparent 0 13px,rgba(20,20,20,.42) 13px 15px),
    repeating-linear-gradient(90deg,transparent 0 43px,rgba(20,20,20,.20) 43px 45px),
    linear-gradient(180deg,#C7523C,#B0432F);
}
.guide-board{background:linear-gradient(180deg,#F6F0E6 0%,#F3ECE1 46%,#E9DECC 100%)}
.guide-panel{
  background:#F3ECE1;backdrop-filter:none;
  border:3px solid #141414;box-shadow:8px 8px 0 #141414;
}
.pg-nav{background:#E9DECC;border-bottom:3px solid #141414}
.pg-skyline{opacity:.9}
.disc.pg-terrazzo{
  background-color:#D8CAB0;
  background-image:
    radial-gradient(circle 5px at 26px 34px,rgba(186,74,51,.55) 0 100%,transparent 0),
    radial-gradient(circle 4px at 92px 18px,rgba(47,93,140,.48) 0 100%,transparent 0),
    radial-gradient(circle 4.6px at 60px 88px,rgba(123,138,99,.45) 0 100%,transparent 0),
    radial-gradient(circle 3.4px at 14px 104px,rgba(20,20,20,.30) 0 100%,transparent 0),
    radial-gradient(circle 4.2px at 112px 74px,rgba(186,74,51,.40) 0 100%,transparent 0),
    radial-gradient(circle 3.6px at 78px 124px,rgba(20,20,20,.26) 0 100%,transparent 0);
  background-size:132px 132px;
}
/* 石灰华圆片：暖白底 + 横向沉积纹，颗粒比水磨石更细 */
.disc.pg-travertine{
  background-color:#E8DCC6;
  background-image:
    repeating-linear-gradient(0deg,transparent 0 7px,rgba(150,120,80,.13) 7px 8px),
    repeating-linear-gradient(0deg,transparent 0 22px,rgba(120,90,60,.07) 22px 23px);
}
/* 柱身圆片：纸白抬亮一档，与左侧水磨石拉开 ΔL* */
.disc.pg-flute{background-color:#F7F2E9}
/* 赤陶砖圆片：横向砖缝 + 错缝竖缝，不做纯色红圆 */
.disc.pg-terracotta{
  background-color:#C7523C;
  background-image:
    repeating-linear-gradient(0deg,transparent 0 11px,rgba(20,20,20,.38) 11px 13px),
    repeating-linear-gradient(90deg,transparent 0 29px,rgba(20,20,20,.22) 29px 31px);
  background-size:auto,62px 26px;
}
/* 导览面板导航：幽灵在前、赭黄实心在后（顺序定胜负，同权重取后者） */
.pg-nav .pill,.pg-nav .pill-ghost{background:#F3ECE1;color:#141414;border:3px solid #141414;font-weight:400}
.pg-nav .pill-accent{background:#E0A32E;color:#141414;border:3px solid #141414;font-weight:400}
/* 02 规格格：模板是细线柔影，粗野主义要有黑框和硬影；玻璃格的彩色光斑一并撤 */
.spec-cell{
  background:#F3ECE1;border:3px solid #141414;
  box-shadow:4px 4px 0 #141414;border-radius:4px;
}
.spec-cell .cap{color:#141414;opacity:.62}
.spec-cell.glass-cell::before{display:none}
/* 板底蓝天空与页脚小字：一个换石灰华，一个撤掉（占位声明已写在第三张卡里） */
.board{background:linear-gradient(180deg,#F6F0E6 0%,#F3ECE1 58%,#EFE5D5 100%)}
.g-foot{display:none}
/* 脚注撤掉后卡片行下方会空 39px（模板面板高 480 是为容纳脚注留的），本主题压回 468，
   让卡片行距面板底 28px，与卡片上方 18px 内距同一量级，不留一块空场。 */
.guide-panel{height:468px}
/* 面板卡：三级字号收小一档，正文不越过卡片下沿 */
.g-card{padding:16px 18px 14px}
.g-card h3{font-size:20px;margin:4px 0 6px}
.g-card p{font-size:12px;line-height:1.7}
</style>''' + s[i:]
        # 页眉事实：模板那行已被通用分支改成「模度几何版」（见上），逐字匹配会漏，
        # 所以这里不依赖 swap 表，直接按当前文本改两处
        s = s.replace('<code>assets/themes/century-sq.css</code><br>',
                      '<code>assets/themes/panyu-rd.css</code><br>')
        s = s.replace('模度几何版 · 2026-11-19',
                      '拱廊 · 赤陶砖 · 水磨石 · 2026-11-20')
        # 天际线：CBD 错落方盒 → 一排拱廊剪影（拱脚落在同一条基线，柱距等分）
        s = re.sub(
            r'<svg class="skyline".*?</svg>',
            """<svg class="pg-skyline" viewBox="0 0 1080 166" preserveAspectRatio="none" aria-hidden="true">
      <g fill="#BA4A33" fill-opacity=".30" stroke="#141414" stroke-opacity=".55" stroke-width="1">
        <path d="M0,166 L0,96 A45,46 0 0,1 90,96 L90,166 Z"/>
        <path d="M90,166 L90,96 A45,46 0 0,1 180,96 L180,166 Z"/>
        <path d="M180,166 L180,96 A45,46 0 0,1 270,96 L270,166 Z"/>
        <path d="M270,166 L270,96 A45,46 0 0,1 360,96 L360,166 Z"/>
        <path d="M360,166 L360,96 A45,46 0 0,1 450,96 L450,166 Z"/>
        <path d="M450,166 L450,96 A45,46 0 0,1 540,96 L540,166 Z"/>
        <path d="M540,166 L540,96 A45,46 0 0,1 630,96 L630,166 Z"/>
        <path d="M630,166 L630,96 A45,46 0 0,1 720,96 L720,166 Z"/>
        <path d="M720,166 L720,96 A45,46 0 0,1 810,96 L810,166 Z"/>
        <path d="M810,166 L810,96 A45,46 0 0,1 900,96 L900,166 Z"/>
        <path d="M900,166 L900,96 A45,46 0 0,1 990,96 L990,166 Z"/>
        <path d="M990,166 L990,96 A45,46 0 0,1 1080,96 L1080,166 Z"/>
      </g>
      <rect x="0" y="92" width="1080" height="4" fill="#141414" fill-opacity=".55"/>
      <rect x="0" y="96" width="1080" height="2" fill="#E0A32E" fill-opacity=".35"/>
      <rect x="0" y="163" width="1080" height="3" fill="#141414" fill-opacity=".55"/>
    </svg>""",
            s, count=1, flags=re.S)

    s = s.replace(f'<h1>{zh} <small>{en.upper()}</small></h1>',
                  f'<h1>{zh} <small style="font-family:var(--font-display);letter-spacing:.06em">{en.upper()}</small></h1>')

    if out:
        outp = Path(out)
    else:
        DEFAULT_OUTDIR.mkdir(parents=True, exist_ok=True)
        outp = DEFAULT_OUTDIR / f'{theme}-theme-preview.html'
    s = apply_mod_scale(s, theme)
    outp.write_text(s, encoding='utf-8')
    print(f'OK {outp} ({outp.stat().st_size // 1024} KB) | {theme} | {zh} {en} | '
          f'dark={dark} aero={aero}')


if __name__ == '__main__':
    main()
