# TABITO Common Test Chinese Item Generator

旅人教育の内部教研向けに、**共通テスト中国語の原创問題を短時間で作成・独立審査・題庫化・組版するための命題支援ツール**。

現在は第4問（Q4）を優先している。API は不要で、ChatGPT Plus を manual LLM backend として使う。

## UI Workbench（推荐）

命令行仍然保留，但日常教研推荐直接使用本地网页 UI。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ui]"
tabito-itemgen-ui
```

浏览器会自动打开 **TABITO 共通テスト中国語 命題 Workbench**。当前 UI 默认显示 **Pilot 002（2026 本试型）**，并可直接切换/查看其他 Pilot。

可以直接：

- 切换「学生版 / 教师版」网页预览
- 查看表格、图表、SNS feed、流程/关系图等资料
- 编辑或上传 item JSON
- 运行完整 validator
- 保存到 draft
- 明确选择 `2026 本试型 / 2026 追试型` 后生成新的 `request.md`
- 生成 blind-review prompt
- 导出学生版 / 教师版 TeX
- 本机存在 XeLaTeX 时直接生成并下载 PDF

网页预览本身**不需要 LaTeX**。因此只想检查题目内容和视觉结构时，不需要先安装 MacTeX。

## Current baseline

命題方向は次の順序で扱う。

1. **Tier 0** — 2026大学入試センター問題作成方針：測る能力の境界
2. **Tier 1** — 2026本試験 + 2026追・再試験：中国語Q4の同格primary blueprint
3. **Tier 2** — 2025以前：語彙・文法レベル、誤答肢、日本語設問等の歴史的参考のみ

現在の blueprint version は：

```text
R8-2026-main-tsui-v3
```

### v3 の重要な修正

以前は「2026本試・追試の共通能力」だけを抽象化しすぎて、結果として一般的な多資料読解問題になっていた。

現在は、内容を原创にする一方で、**2026本試・追試の実際の surface grammar を再現する**。

full Q4 は必ず次のどちらかの `surface_family` を持つ。

- `main_2026` — 2026本試験型
- `makeup_2026` — 2026追・再試験型

Aの21〜28とBの29〜36は、選択した family の答番号グループ・設問役割・資料接続に従う。

詳細：

- `docs/Q4_SURFACE_GRAMMAR_2026.md`
- `docs/EXAM_SPEC_2026.md`
- `docs/ITEM_WRITING_DIRECTION_2026.md`
- `blueprints/q4_2026_reference_patterns.yaml`
- `blueprints/q4_2026_generation_profile.yaml`

## 現在の Pilot

- **Pilot 001** — REJECTED。16枠はあるが、2026の実際のQ4型を再現できていない失敗サンプル。
- **Pilot 002** — `main_2026` active candidate。市立図書館の学習スペース。
- **Pilot 003** — `makeup_2026` active candidate。街の明かりと星空観察。

`pilots/README.md` と各 QA log を参照。

## v0.4 系で重要になったこと

- 2026本試・追試を「能力参考」だけでなく、現在のQ4の実際の型として扱う
- `surface_family` を full Q4 の必須概念にする
- validator が 21〜36 の family-specific slot grouping を検査する
- 本試型：会話 → 調査資料 → 説明 / memo → checklist → profile matching → missing information → flow / case
- 追試型：会話 → survey → prose+diagram → memo → chronological planning → compound operational source → safety instructions → reflection
- 「原创」を理由に surface grammar まで捨てることを禁止
- 日本語設問・中国語資料・選択肢言語の組み合わせも題面の一部として扱う
- arbitraryな「3 cross-material tasks」「4 material types」hard ruleは廃止
- `single_source / within_compound / cross_source / scenario_plus_source` で情報依存を表現
- compound source用 `bundle_id` を使用
- blind reviewer から answer key と author-side metadata を除去
- real full-Q4 pilotで見つかった欠陥を prompt / validator へ反映
- 装飾目的の図表を禁止し、情報関係に最も自然な資料形式を選ぶ

## CLI Setup

UI を使わない場合：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## CLI の実務フロー

### 1. 生成依頼を作る

本試型：

```bash
tabito-itemgen new-item \
  --topic "地域施設の利用改善" \
  --scope full \
  --surface-family main_2026
```

追試型：

```bash
tabito-itemgen new-item \
  --topic "地域活動の調査と現地体験" \
  --scope full \
  --surface-family makeup_2026
```

full Q4 の default difficulty は `official_like`。

`workspace/requests/*.request.md` を ChatGPT Plus にそのまま渡し、返答 JSON を保存する。

### 2. draft に取り込んで検証

```bash
tabito-itemgen import-response response.json
tabito-itemgen validate item_bank/draft/TABITO-CN-Q4-....json
```

validator は schema だけでなく、v3 full Q4 について：

- `surface_family` の有無
- A=21〜28 / B=29〜36
- familyごとの task-slot grouping
- 21–22 が会話 + 二つ選べか
- 本試型Bの matching / flow-family が成立しているか
- 追試型Bの chronological planning / compound source / reflection が成立しているか

も確認する。

### 3. ブラインド独立審査

```bash
tabito-itemgen review-request item_bank/draft/TABITO-CN-Q4-....json
```

review JSON を保存後：

```bash
tabito-itemgen import-review review.json

tabito-itemgen review-check \
  --item item_bank/draft/TABITO-CN-Q4-....json \
  --review workspace/reviews/TABITO-CN-Q4-....review.json
```

reviewer の独立解答と author key が不一致なら FAIL。

### 4. 必要なら修訂

```bash
tabito-itemgen revision-request \
  --item item_bank/draft/TABITO-CN-Q4-....json \
  --review workspace/reviews/TABITO-CN-Q4-....review.json
```

### 5. 類似度を確認して approve

```bash
tabito-itemgen similarity revised_item.json

tabito-itemgen approve revised_item.json \
  --review workspace/reviews/TABITO-CN-Q4-....review.json
```

### 6. 学生版 / 教師版を組版

```bash
tabito-itemgen render item_bank/approved/TABITO-CN-Q4-....json --compile
```

`output/<item_id>/` に student / teacher の TeX / PDF を生成する。

## Repository

```text
blueprints/          versioned blueprint + 2026 structural reference metadata
templates/           Q4 generation constraints
prompts/             generate / blind review / revise
docs/                exam spec, surface grammar, item-writing direction, audits
examples/            schema/regression fixtures; NOT gold content
pilots/              real content-QA candidates and revision history
benchmarks/          future human-approved gold exemplars
workspace/           manual ChatGPT handoff + UI temp files
item_bank/draft/     unapproved candidates
item_bank/approved/  usable items
item_bank/rejected/  rejected items
src/                 CLI / UI / schema / validation / rendering
tests/               regression tests
output/              generated TeX/PDF
```

## Content maturity

`examples/` はschemaとrendererの回帰用fixtureであり、命題品質の見本ではない。

`pilots/` は実際に内容QAを行う候補問題。失敗や修訂履歴も保存する。

本当に質が確認された問題だけを将来 `benchmarks/` に入れる。

## まだやらないこと

現段階では API、LangChain、vector DB、fine-tuning、IRT を優先しない。

まず main_2026 / makeup_2026 の real full Q4 を複数生成し、**人間がどこを何分直したか**を記録する。その結果から次の開発優先順位を決める。

## 次の優先順位

1. Pilot 002 / 003 を blind review + human item-writing review
2. UI 上で main_2026 / makeup_2026 を比較しながら content QA
3. 返工理由と修正時間を記録
4. 最も頻発する品質欠陥を prompt / schema / validator へ反映
5. PDF renderer を大学入試センター冊子に近い版面へ改善
6. `used_in` と模試assembly
7. Q5 pipeline
8. Q1/Q2/Q3
