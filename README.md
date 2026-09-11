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

浏览器会自动打开 **TABITO 共通テスト中国語 命題 Workbench**。默认优先显示最新 Pilot，可以直接：

- 切换「学生版 / 教师版」网页预览
- 查看表格、图表、SNS feed、流程/关系图等资料
- 编辑或上传 item JSON
- 运行完整 validator
- 保存到 draft
- 填主题并生成新的 `request.md`
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
R8-2026-main-tsui-v2
```

2026本試・追試の**共通点だけを hard core** とし、両者の違いは正当な variation として扱う。片方だけにある flowchart / map / 実務行動 / reflection 等を全セットの必須テンプレートにはしない。

詳細：

- `docs/EXAM_SPEC_2026.md`
- `docs/ITEM_WRITING_DIRECTION_2026.md`
- `blueprints/q4_2026_reference_patterns.yaml`
- `blueprints/q4_2026_generation_profile.yaml`

## v0.3 系で重要になったこと

- 2026本試・追試を同格のdual baselineとして扱う
- arbitraryな「3 cross-material tasks」「4 material types」hard ruleを廃止
- `single_source / within_compound / cross_source / scenario_plus_source` で情報依存を表現
- compound source用 `bundle_id` を追加
- 追試に必要な `social_feed / schematic_map / annotated_diagram / memo / reflection` 等を原生サポート
- Bを「必ず実務行動」とせず、再文脈化・適用・総合・reflectionまで許容
- generatorには公式逐問配列を直接見せず、generation-safe profileのみを渡す
- blind reviewerからanswer keyだけでなく命題者側metadataも除去
- real full-Q4 pilotで見つかった欠陥をpromptへ反映
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

```bash
tabito-itemgen new-item \
  --topic "地域施設の利用改善" \
  --scope full
```

full Q4 の default difficulty は `official_like`。

`workspace/requests/*.request.md` を ChatGPT Plus にそのまま渡し、返答 JSON を保存する。

### 2. draft に取り込んで検証

```bash
tabito-itemgen import-response response.json
tabito-itemgen validate item_bank/draft/TABITO-CN-Q4-....json
```

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
docs/                exam spec, item-writing direction, audits
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

まず real full Q4 を5セット程度生成し、**人間がどこを何分直したか**を記録する。その結果から次の開発優先順位を決める。

## 次の優先順位

1. UIを使って real full Q4 を5セット content QA
2. 返工理由と修正時間を記録
3. 最も頻発する品質欠陥をprompt/schema/validatorへ反映
4. PDF renderer の本番版面改善
5. `used_in` と模試assembly
6. Q5 pipeline
7. Q1/Q2/Q3
