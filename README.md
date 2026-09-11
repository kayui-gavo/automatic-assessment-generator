# TABITO Common Test Chinese Item Generator

旅人教育の内部教研向けに、**共通テスト中国語の原创問題を短時間で作成・独立審査・題庫化・組版するための命題支援ツール**。

現在は第4問（Q4）を優先している。API は不要で、ChatGPT Plus を manual LLM backend として使う。

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
- `docs/AUDIT_v0.2_2026_BASELINE.md`

## v0.3 で重要になったこと

v0.2 は production architecture としては成立したが、「公式事実」と「内部heuristic」を混同していた。

v0.3 では：

- 2026本試・追試を同格のdual baselineとして全promptへ注入
- arbitraryな「3 cross-material tasks」「4 material types」hard ruleを廃止
- `single_source / within_compound / cross_source / scenario_plus_source` で情報依存を表現
- compound source用 `bundle_id` を追加
- 追試に必要な `social_feed / schematic_map / annotated_diagram / memo / reflection` 等を原生サポート
- Bを「必ず実務行動」とせず、再文脈化・適用・総合・reflectionまで許容
- `official_like` をfull Q4のdefault difficultyにし、内部難度を均一化しない
- blind reviewとrevisionにも同じ2026 baseline contextを渡す
- example fixture と gold benchmark を分離

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## 最短の実務フロー

### 1. 生成依頼を作る

```bash
tabito-itemgen new-item \
  --topic "地域施設の利用改善" \
  --scope full
```

full Q4 の default difficulty は `official_like`。

必要なら：

```bash
tabito-itemgen new-item \
  --topic "学校の国際交流企画" \
  --difficulty hard \
  --domain school_life \
  --notes "公式問題の場面換皮ではなく、情報収集から後半の判断へ自然に用途が変わる構成"
```

`workspace/requests/*.request.md` を ChatGPT Plus にそのまま渡し、返答 JSON を保存する。

生成requestには自動的に以下が入る。

- overall blueprint
- 2026本試・追試の構造メタデータ
- Q4 template
- detailed item-writing direction
- item spec

### 2. draft に取り込んで検証

```bash
tabito-itemgen import-response response.json
tabito-itemgen validate item_bank/draft/TABITO-CN-Q4-....json
```

full Q4 では特に：

- answer number 21–36 がちょうど1回ずつか
- A/B 両方があるか
- A/Bそれぞれに genuinely integrative な task があるか
- `dependency_mode` と evidence が矛盾していないか
- compound source の `bundle_id` が成立しているか
- structured/visual information があるか
- 飾り資料が多すぎないか
- direct extraction が大半を占めていないか
- multi-select が2026型として十分存在するか
- evidence locator があるか
- distractor rationale が揃っているか

を確認する。

material type の数や cross-source task の数は、公式根拠のない固定quotaとしては扱わない。

### 3. ブラインド独立審査

```bash
tabito-itemgen review-request item_bank/draft/TABITO-CN-Q4-....json
```

review packet からは：

- correct answer
- evidence
- rationale
- distractor rationale
- generator self-assessment

を除去する。一方で、2026 dual-baseline の命題基準は reviewer に渡す。

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

revision prompt にも generation と同じ blueprint / reference patterns / template / item-writing direction が入る。

### 5. 類似度を確認して approve

```bash
tabito-itemgen similarity revised_item.json

tabito-itemgen approve revised_item.json \
  --review workspace/reviews/TABITO-CN-Q4-....review.json
```

`approve` は blind review gate を通常必須とする。schema/validatorを通っても、人間が内容を確認せずにapproveしない。

### 6. 学生版 / 教師版を組版

```bash
tabito-itemgen render item_bank/approved/TABITO-CN-Q4-....json --compile
```

`output/<item_id>/` に student / teacher の TeX / PDF を生成する。

現在のrendererは：

- text / dialogue / memo / reflection
- table / timetable
- bar / horizontal-bar / stacked-bar / line chart
- flowchart
- social feed
- schematic map
- annotated diagram

を扱う。

教師版には正答・根拠・解説・情報依存・誤答肢理由も出す。

## Repository

```text
blueprints/          versioned blueprint + 2026 structural reference metadata
templates/           Q4 generation constraints
prompts/             generate / blind review / revise
docs/                exam spec, item-writing direction, audits
examples/            schema/regression fixtures; NOT gold content
benchmarks/          future human-approved gold exemplars
workspace/           manual ChatGPT handoff
item_bank/draft/     unapproved candidates
item_bank/approved/  usable items
item_bank/rejected/  rejected items
src/                 CLI / schema / validation / rendering
tests/               regression tests
output/              generated TeX/PDF
```

## Examples are not gold items

`examples/q4_example_response.json` はschemaとrendererの回帰用fixtureであり、命題品質の見本ではない。

本当に質が確認された問題だけを将来 `benchmarks/` に入れる。

## まだやらないこと

現段階では API、LangChain、vector DB、fine-tuning、IRT、Web UI を優先しない。

まず実際の full Q4 を5セット程度生成し、**人間がどこを何分直したか**を記録する。その結果から v0.3/v0.4 の開発優先順位を決める。

## 次の優先順位

1. 2026 dual baselineで real full Q4 を5セット生成して content QA
2. 返工理由と修正時間を記録
3. 最も頻発する品質欠陥をprompt/schema/validatorへ反映
4. renderer の本番版面改善
5. `used_in` と模試assembly
6. Q5 pipeline
7. Q1/Q2/Q3
