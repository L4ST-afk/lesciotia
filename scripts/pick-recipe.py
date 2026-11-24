#!/usr/bin/env python3
"""体裁判定 + 提示词配方：这一段内容该按哪一版写（中文优先，外文也能触发）。

来雪亭不替人写，但「写」这件事有型：汇报要结论先行，提案要代价与要什么，讲解要槽位与前置，
复盘要归因不归咎，发布要一句主张加一条限制。型选错了，九条判据只会把错的东西判得更整齐。

用法：
    python3 scripts/pick-recipe.py --detect 草稿.md        # 判型，给置信与依据
    python3 scripts/pick-recipe.py --detect deck.json      # 也可以喂 spec
    python3 scripts/pick-recipe.py --show briefing         # 出这一型的提示词（可直接用）
    python3 scripts/pick-recipe.py --list                  # 五型一览

判型只看内容，不看文件名。**中文优先**：中文触发词每条计 2 分，英文/日文计 1 分；
同一份里中英混排，中文证据压过外文证据（实测见 examples/prose/recipes/mixed-zh-first.md）。
分数接近时（头名与次名差 ≤2）明说「两型都对」，不硬判——矮凳桥的规矩：两套都对就分段写。
"""
import argparse
import json
import re
import sys

# 中文触发词计 2 分，外文计 1 分：同一段里两种语言都在说话时，作者用哪种语言写的，就按哪种优先。
CJK_W, FOREIGN_W = 2.0, 1.0

RECIPES = {
    'briefing': {
        'name': '汇报',
        'when': '对上：周报、进度、评审、给领导讲',
        'triggers': {
            'zh': ['汇报', '领导', '评审', '进度', '周报', '月报', '部门', '会上', '过会', '述职'],
            'en': ['weekly report', 'status update', 'progress', 'stakeholder', 'review meeting',
                   'standup', 'briefing', 'to the team'],
            'ja': ['報告', '進捗', '週報', '上司', 'レビュー'],
        },
        'structure': ['结论先行（第一页就是主张与代价）',
                      '每页一条主张 + 一处证据 + 一个数',
                      '最后给「下一步只做一件事」，不给清单'],
        'prompt': """你是给上级写汇报的人。输入是一段口语草稿，输出是本库的 deck spec（slides[]，页型从 cover/bullets/kpi/comparison/table 里选）。

硬要求（数得出，不靠形容词）：
1. 第 1 页 cover：标题给「对象＋卡点」（「设备数据采集／卡在三处」），lede 给代价或反常识的一句，不复述标题。
2. 每页只放一个主张；要点每条 ≤26 字、一个句读，形如「现象：数字」。
3. 所有数字带 `source`（谁给的、哪个月）；指不到出处的数降级成「约」或删。
4. 结尾 kpi 页给「下一步只做一件事」，三个以内的数，不给任务清单。
5. 全程禁词：赋能/闭环/抓手/一站式/全链路/降本增效/生态位。
写完自己过四问（浮沙言）：换个主题还成立吗？谁在说、为什么说？删掉这句会掉信息吗？这句有来处吗？""",
    },
    'proposal': {
        'name': '提案',
        'when': '对外或对内争取资源：立项、报价、合作、投资',
        'triggers': {
            'zh': ['提案', '方案', '立项', '预算', '报价', '合作', '投资', '采购', '申请', '说服'],
            'en': ['proposal', 'budget', 'approval', 'quote', 'funding', 'invest', 'partner',
                   'procure', 'pitch', 'ask for'],
            'ja': ['提案', '予算', '見積', '投資', '申請'],
        },
        'structure': ['问题与代价（不先讲我们多好）',
                      '做法（三步以内，每步一个可验证的产物）',
                      '证据（先例、数字、谁验过）',
                      '要什么（钱/人/时间，具体到数）'],
        'prompt': """你在写一份要资源的东西。顺序是：问题与代价 → 做法 → 证据 → 要什么。

硬要求：
1. 第 1 页不许夸自己，先写「不做会怎样」，且代价带数字或时间。
2. 做法最多三步，每步写清「产出什么、谁验」；不写第四步的远景。
3. 证据必须是已发生的事（某厂、某月、某数），不用「预计」「有望」当证据；预测单独一页并标「估计」。
4. 最后一页写「要什么」：金额/人力/周期，给区间并说清下限能干什么。
5. 禁词同汇报；另禁「颠覆」「重新定义」「一站式」。
写完过四问：换主题还成立吗？谁在说？删了掉信息吗？有来处吗？""",
    },
    'teaching': {
        'name': '讲解',
        'when': '培训、科普、机制说明、「这是怎么运作的」',
        'triggers': {
            'zh': ['讲解', '原理', '机制', '培训', '科普', '怎么运作', '为什么', '入门', '教程', '由哪些'],
            'en': ['how it works', 'why', 'explainer', 'walkthrough', 'tutorial', 'onboarding',
                   'mechanism', 'mental model', 'teach'],
            'ja': ['仕組み', '前提', 'なぜ', '研修', '講義', '入門', '構成'],
        },
        'structure': ['槽位（这东西由哪几个角色构成）',
                      '前置（走到这一步之前必须已经有什么）',
                      '典型性（典型用法 → 边缘用法 → 反例）',
                      '边界（做不到什么，别让人误用）'],
        'prompt': """你在讲一个机制，听众是会用但说不清的人。按矮凳桥的结构走，不按时间线走。

硬要求：
1. 先给「槽位」：这件东西由哪 2–4 个角色构成，每个角色一句话职责；配图用形状表达关系，不用流程图硬凑。
2. 再给「前置」：走到这一步之前必须已经具备什么，缺了会怎样。
3. 典型性阶梯：先一个最常见的用法（带一个真实数字或场景），再一个边缘用法，最后一条反例（常见误用）。
4. 结尾一页写边界：做不到什么。⛔ 不许用「强大」「灵活」代替边界。
5. 术语首现括注中文；每个缩写只解释一次。
写完过四问：换主题还成立吗？谁在说？删了掉信息吗？有来处吗？""",
    },
    'retro': {
        'name': '复盘',
        'when': '做完回头看：项目收尾、事故、发布后',
        'triggers': {
            'zh': ['复盘', '总结', '教训', '事故', '回顾', '收尾', '问题分析', '根因', '事后'],
            'en': ['postmortem', 'retro', 'retrospective', 'root cause', 'lesson', 'incident',
                   'what went wrong', "after action", 'blameless'],
            'ja': ['振り返り', '原因', '障害', '教訓', '事後'],
        },
        'structure': ['发生了什么（时间线，只列事实）',
                      '为什么（根因，写到可改的那一层）',
                      '改什么（具体动作 + 谁 + 何时验）',
                      '没改的（明说取舍）'],
        'prompt': """你在写复盘。纪律：归因不归咎，事实与判断分开放。

硬要求：
1. 第一页只写事实：时间、数字、谁做了什么，不掺评价词。
2. 根因写到「可改的那一层」：停在「沟通不畅」就是没写完，要落到某个流程/某个字段/某个检查点。
3. 改法每条带负责人与验收时点；没有验收时点的条目删掉。
4. 单开一页写「这次不改的」及理由——不写这一页的复盘通常是在护短。
5. 禁「高度重视」「举一反三」这类替代品。
写完过四问：换主题还成立吗？谁在说？删了掉信息吗？有来处吗？""",
    },
    'launch': {
        'name': '发布',
        'when': '对外宣发：上线、版本、产品页、朋友圈长文',
        'triggers': {
            'zh': ['发布', '上线', '新版', '版本', '宣发', '推广', '产品页', '介绍', '发布会'],
            'en': ['launch', 'release', 'announce', 'ship', 'now available', 'go live',
                   'product page', 'introducing'],
            'ja': ['リリース', '公開', '発売', '新バージョン', 'お知らせ'],
        },
        'structure': ['一句主张（做了什么，给谁，省了什么）',
                      '三条证据（可核）',
                      '一条限制（不适用谁）',
                      '一个动作（怎么开始）'],
        'prompt': """你在写对外发布。读者不认识你，只给你 30 秒。

硬要求：
1. 第 1 页一句话说清：给谁、解决什么、省下多少（数字或时间），⛔ 不用形容词。
2. 三条证据，每条能被外人核（公开链接、可复现步骤、第三方数据）；核不了的降级成「我们自己测的」。
3. 必写一条限制：不适用谁、什么情况下别用。没有限制的发布读起来像广告。
4. 结尾给一个动作：怎么开始，一步，别给注册流程五步。
5. 禁词：颠覆/重新定义/一站式/赋能/生态。
写完过四问：换主题还成立吗？谁在说？删了掉信息吗？有来处吗？""",
    },
}

# 结构信号：不看词，看这段字在干什么（中/外各一组，外文权重 1）
SIGNALS = [
    ('proposal', [r'下一步', r'计划', r'预算', r'需要.{0,4}(人|钱|资源)', r'申请'],
     [r'\bnext step', r'\bwe need\b', r'\bcost\b']),
    ('retro', [r'教训', r'根因', r'本来应该', r'事后', r'哪里出问题'],
     [r'\blesson', r'\bwent wrong', r'\broot cause']),
    ('teaching', [r'为什么', r'原理', r'由.{0,6}组成', r'第一步.*第二步'],
     [r'\bwhy\b', r'\bconsists of', r'\bstep one']),
    ('launch', [r'上线', r'发布', r'新版本', r'欢迎试用'],
     [r'\bavailable now', r'\breleased?\b']),
    ('briefing', [r'汇报', r'进展', r'完成了', r'目前'],
     [r'\bupdate\b', r'\bprogress\b']),
]

LANG_TAIL = """
目标语言不是中文时：字数按 26 字 ≈ 54 字符折算；禁词按同义替换（enable/empower、closed loop、
one-stop、synergy 这类），判据编号不变。"""


def collect_text(obj):
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict) and ('slides' in obj or 'pages' in obj):
        out = []
        for d in obj.get('slides') or obj.get('pages') or []:
            for k in ('kicker', 'title', 'lede', 'subtitle', 'body', 'quote', 'notes'):
                v = d.get(k)
                if isinstance(v, list):
                    out += [str(x) for x in v]
                elif v:
                    out.append(str(v))
            for it in d.get('items') or []:
                out.append(' '.join(str(c) for c in it) if isinstance(it, (list, tuple)) else str(it))
        return '\n'.join(out)
    return json.dumps(obj, ensure_ascii=False)


def count_foreign(text, w):
    # 词边界匹配：report 不该命中 reporter 里的子串，但允许复数/时态（\w* 尾巴）
    return len(re.findall(r'(?<![A-Za-z])%s\w{0,4}(?![A-Za-z])' % re.escape(w), text, re.I))


def is_cjk(w):
    return bool(re.match(r'^[\u4e00-\u9fff]', w))


def detect(text):
    score = {k: 0.0 for k in RECIPES}
    hits = {k: [] for k in RECIPES}
    for k, r in RECIPES.items():
        for lang, words in r['triggers'].items():
            for w in words:
                n = text.count(w) if lang == 'zh' else count_foreign(text, w)
                if n:
                    score[k] += min(n, 3) * (CJK_W if lang == 'zh' else FOREIGN_W)
                    hits[k].append('%s×%d' % (w, n))
    for k, zh_pats, foreign_pats in SIGNALS:
        for p in zh_pats:
            if re.search(p, text):
                score[k] += 1
                hits[k].append('结构:%s' % p)
        for p in foreign_pats:
            if re.search(p, text, re.I):
                score[k] += FOREIGN_W * 0.5
                hits[k].append('struct:%s' % p)
    ranked = sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))
    return ranked, hits


def load(path):
    try:
        with open(path, encoding='utf-8') as fh:
            raw = fh.read()
    except Exception as e:
        print('✗ 读不了 %s：%s' % (path, e), file=sys.stderr)
        sys.exit(2)
    if raw.lstrip().startswith('{'):
        try:
            return collect_text(json.loads(raw))
        except Exception:
            return raw
    return raw


def main():
    ap = argparse.ArgumentParser(description='体裁判定 + 成稿提示词配方（五型，中文优先）')
    ap.add_argument('--detect', metavar='FILE', help='判这份草稿或 spec 属哪一型')
    ap.add_argument('--show', metavar='KEY', choices=sorted(RECIPES), help='打印该型的提示词')
    ap.add_argument('--list', action='store_true', help='五型一览')
    ap.add_argument('--json', action='store_true', help='机器可读摘要（配 --detect）')
    a = ap.parse_args()

    if a.list or (not a.detect and not a.show):
        for k, r in RECIPES.items():
            print('%-10s %s —— %s' % (k, r['name'], r['when']))
        print('\n用法：--detect <草稿|spec> 判型；--show <key> 出提示词。判据九条见 references/prose-gate.md。')
        return 0

    if a.show:
        r = RECIPES[a.show]
        print('# %s（%s）\n' % (r['name'], a.show))
        print(r['prompt'] + LANG_TAIL)
        print('\n---\n胎：结构骨架 ' + '；'.join(r['structure']) + '。')
        return 0

    text = load(a.detect)
    ranked, hits = detect(text)
    top, second = ranked[0], ranked[1]
    if a.json:
        print(json.dumps({'recipe': top[0], 'score': top[1], 'runner_up': second[0],
                          'runner_up_score': second[1], 'ties': top[1] - second[1] <= 2,
                          'hits': hits[top[0]]}, ensure_ascii=False))
        return 0
    print('判型（%d 字）：' % len(text))
    for k, v in ranked:
        print('  %-10s %4.1f  %s' % (k, v, '／'.join(hits[k][:5]) if hits[k] else '—'))
    if top[1] == 0:
        print('→ 没有命中：按「汇报」起步，或补一句「这是给谁看的、要他做什么」。')
    elif top[1] - second[1] <= 2:
        print('→ 两型都对（%s %.1f / %s %.1f）：按矮凳桥的规矩分段写，别混在一页。'
              % (RECIPES[top[0]]['name'], top[1], RECIPES[second[0]]['name'], second[1]))
    else:
        print('→ 按「%s」写：python3 scripts/pick-recipe.py --show %s' % (RECIPES[top[0]]['name'], top[0]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
