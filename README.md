# TABITO Common Test Chinese Item Generator

旅人教育の内部教研向け **共通テスト中国語 命題 Workbench**。

現在は第4問（Q4）を優先し、**2026 本試験 + 2026 追・再試験を唯一の一次蓝本**として、原创問題の生成・独立審査・題庫化・学生版/教師版組版までを一つのローカルUIで扱う。

API は不要。ChatGPT Plus を manual LLM backend として使う。

## まず UI を開く

初回：

```bash
cd ~/automatic-assessment-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ui]"
tabito-itemgen-ui
```

2回目以降：

```bash
cd ~/automatic-assessment-generator
source .venv/bin/activate
git pull
tabito-itemgen-ui
```

ブラウザで **TABITO 共通テスト中国語 命題 Workbench** が開く。

### UI の4つの仕事

#### 1. 试卷预览

最初に見る画面。

- **学生册**：共通テスト冊子に近い階層で A/B・問1〜3・小問・資料・解答欄を見る
- **教师标注**：正答一覧、根拠、解説、誤答肢分析を必要な問題だけ展開する
- **结构检查**：answer slot / dependency / material type を教研用に確認する

旧 Pilot / rejected sample は初期状態では隠している。

#### 2. 新建命题

最初に family を選ぶ。

- `main_2026` — **2026 本試験型**
- `makeup_2026` — **2026 追試験型**

その後に題材を決める。逆ではない。

UI が `request.md` を作るので、新しい ChatGPT 対話へコピーして JSON を返してもらう。

#### 3. 质检 / 审题

- schema / 21〜36 / family-specific surface grammar
- 選択肢言語分布
- information dependency
- decorative material / unused material
- approved bank との類似度
- blind reviewer の独立解答と author key の一致

をまとめて確認する。

reviewer JSON を UI にアップロードすれば、その場で gate 判定し、必要なら revision prompt を生成できる。

#### 4. 编辑 / 导出

通常は JSON を触らない。

必要なときだけ高度な JSON editor を開き、draft 保存・TeX/PDF出力を行う。

网页预览は LaTeX 不要。PDF生成だけ XeLaTeX が必要。

---

## 命題の一次蓝本

優先順位は固定する。

1. **Tier 0** — 2026 大学入試センター問題作成方針：測る能力の境界
2. **Tier 1** — **2026 本試験 + 2026 追・再試験**：Q4の実際の型
3. **Tier 2** — 2025以前：語彙・文法レベル、誤答肢、日本語設問等の歴史的参考のみ

2025以前の題型を平均化して2026へ戻さない。

現在の blueprint：

```text
R8-2026-main-tsui-v3
```

## 2026 Q4 surface grammar

full Q4 は必ず `surface_family` を持つ。

### `main_2026`

```text
A
21–22  会話 + 二つ選べ
23–24  shared options / quantitative material
25      chart
26      related visual comparison
27–28  explanation / lecture / memo + 二つ選べ

B
29–30  checklist / requirements + 二つ選べ
31–32  profile / candidate matching
33      missing-information inference
34      rule / flow general principle
35–36  process applied to two cases
```

### `makeup_2026`

```text
A
21–22  discussion dialogue + 二つ選べ
23–24  survey / chart + 二つ選べ
25–26  explanatory text + diagram + 二つ選べ
27–28  structured memo + 二つ選べ

B
29–30  chronological planning
31–32  map / memo / system compound source
33–34  flyer / instructions / safety document
35–36  reflection / summary + 二つ選べ
```

`surface_family` は schema の正式フィールド。UI / validator / renderer が同じ値を使う。

また新規生成では `subsection_intros_ja.A/B` を持ち、A/B冒頭の日本語導入まで冊子の一部として審査する。

詳細：

- `docs/Q4_SURFACE_GRAMMAR_2026.md`
- `docs/EXAM_SPEC_2026.md`
- `docs/ITEM_WRITING_DIRECTION_2026.md`
- `blueprints/q4_2026_reference_patterns.yaml`
- `blueprints/q4_2026_generation_profile.yaml`

---

## Pilot の扱い

`examples/` は schema / renderer fixture。質の見本ではない。

`pilots/` は real content-QA 用。

- **Pilot 001** — REJECTED。generic multi-source reading に寄りすぎた失敗例
- **Pilot 002** — active `main_2026` candidate
- **Pilot 003 v1** — SUPERSEDED。option-language surface が不十分
- **Pilot 003 v2** — active `makeup_2026` candidate

本当に教研品質を通過したものだけ将来 `benchmarks/` に入れる。

---

## CLI

UIを使わない場合：

```bash
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

本試型 request：

```bash
tabito-itemgen new-item \
  --topic "地域施設の利用改善" \
  --scope full \
  --family main_2026
```

追試型 request：

```bash
tabito-itemgen new-item \
  --topic "地域活動の調査と現地体験" \
  --scope full \
  --family makeup_2026
```

検証：

```bash
tabito-itemgen validate item_bank/draft/TABITO-CN-Q4-....json
```

Blind review：

```bash
tabito-itemgen review-request item_bank/draft/TABITO-CN-Q4-....json
```

Review check：

```bash
tabito-itemgen review-check \
  --item item_bank/draft/TABITO-CN-Q4-....json \
  --review workspace/reviews/TABITO-CN-Q4-....review.json
```

Revision：

```bash
tabito-itemgen revision-request \
  --item item_bank/draft/TABITO-CN-Q4-....json \
  --review workspace/reviews/TABITO-CN-Q4-....review.json
```

Approve：

```bash
tabito-itemgen similarity revised_item.json

tabito-itemgen approve revised_item.json \
  --review workspace/reviews/TABITO-CN-Q4-....review.json
```

PDF：

```bash
tabito-itemgen render item_bank/approved/TABITO-CN-Q4-....json --compile
```

---

## Repository

```text
blueprints/          2026 blueprint / official structural reference metadata
templates/           generation constraints
prompts/             generate / blind review / revise
docs/                exam spec / surface grammar / item-writing direction
examples/            schema regression fixtures; NOT gold content
pilots/              real content-QA candidates + revision history
benchmarks/          future human-approved gold exemplars
workspace/           manual ChatGPT handoff + UI temporary files
item_bank/draft/     unapproved candidates
item_bank/approved/  usable items
item_bank/rejected/  rejected items
src/                 CLI / UI / schema / validation / presentation / rendering
tests/               regression tests
output/              generated TeX/PDF
```

## 今やらないこと

API、LangChain、vector DB、fine-tuning、IRT、重いWeb frameworkは優先しない。

優先するのは：

1. `main_2026` / `makeup_2026` の候補問題を実際に作る
2. blind review + 中国語自然度 + 共通テスト命題観点で人間が直す
3. **何を何分直したか**を記録する
4. 頻発する失敗だけを prompt / schema / validator へ戻す
5. 学生が実際に読む冊子の可読性を上げる
