# TABITO Common Test Chinese Item Generator

旅人教育の内部教研向けに、**共通テスト中国語の原创問題を短時間で作成・独立審査・題庫化・組版するための命題支援ツール**。

現在の v0.2 は第4問を優先している。API は不要で、ChatGPT Plus を manual LLM backend として使う。

## 命題ブループリント

命題方向の第一級ブループリントは、**2026（令和8年度）本試験と2026追・再試験の2セット**。

- 2026本試と2026追試は同格の primary references
- 両者の共通点を「2026型の核」とする
- 両者の差を「許容される設計の幅」とする
- **2025以前は historical reference only**
- 旧年度は語彙・文法レベル、安定した測定能力、誤答肢、日本語設問表現の確認には使うが、2026の構造を上書きしない
- 旧年度と2026が衝突する場合は必ず2026を優先する

詳細は `docs/ITEM_WRITING_DIRECTION_2026.md` と `docs/EXAM_SPEC_2026.md`。

## v0.2 で重要になったこと

v0.1 は「2–4資料 + 6個の普通MCQ」という抽象化が強すぎ、実際の共通テストQ4を表現できなかった。v0.2 では 2026 本試・追試を参照基準として、full Q4 を次のように扱う。

- A / B の二段階
- 解答番号 21–36 の16 answer slots
- `single_choice` / `multi_select` / `multi_slot_choice`
- dialogue / table / timetable / chart / profile / checklist / flowchart 等の構造化資料
- 情報取得→比較/統合→後半の実際的な計画・条件照合・ルール/プロセス適用・総合判断という進行
- 生成者の正答を見せない blind independent review
- review answer と answer key の自動照合
- approved bank との軽量類似度チェック
- 表・グラフ・フローチャート対応 LaTeX renderer

詳しい旧版の問題点は `docs/AUDIT_v0.1.md` を参照。

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
  --topic "地域イベント" \
  --difficulty medium \
  --domain daily_life \
  --scope full
```

必要なら自由メモも渡せる。

```bash
tabito-itemgen new-item \
  --topic "オープンキャンパス" \
  --notes "大学案内の換皮ではなく、情報取得→比較→後続行動が自然につながる構成"
```

`workspace/requests/*.request.md` を ChatGPT Plus にそのまま渡し、返答 JSON を保存する。生成 request には2026 dual-baselineの命題方針が自動的に埋め込まれる。

### 2. draft に取り込んで検証

```bash
tabito-itemgen import-response response.json
tabito-itemgen validate item_bank/draft/TABITO-CN-Q4-....json
```

full Q4 では特に以下を機械チェックする。

- answer number 21–36 がちょうど1回ずつあるか
- A/B 両方が存在するか
- cross-material task が最低3つあるか
- structured/visual material があるか
- evidence locator があるか
- answer-position の極端な偏り
- distractor rationale の不足
- multi-slot task では各 answer slot ごとの誤答理由が揃っているか

### 3. ブラインド独立審査

```bash
tabito-itemgen review-request item_bank/draft/TABITO-CN-Q4-....json
```

生成される review request からは、**正答・evidence・解説・生成者自己評価を自動的に除去**してある。reviewer には同時に2026本試・追試ベースの命題方向が渡される。できれば生成時とは別 Chat に渡す。

返ってきた review JSON を保存後：

```bash
tabito-itemgen import-review review.json

tabito-itemgen review-check \
  --item item_bank/draft/TABITO-CN-Q4-....json \
  --review workspace/reviews/TABITO-CN-Q4-....review.json
```

reviewer が独立に解いた答えと author key が食い違えば FAIL になる。

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

`approve` は、通常は blind review が `pass` で、独立解答が key と一致しない限り通らない。緊急時のみ明示的 override を使う。

### 6. 学生版 / 教師版を組版

```bash
tabito-itemgen render item_bank/approved/TABITO-CN-Q4-....json --compile
```

`output/<item_id>/` に student / teacher の TeX と PDF ができる。

## Repository

```text
blueprints/          試験全体の versioned blueprint
templates/           Q4 の具体的生成制約
prompts/             generate / blind review / revise
docs/                exam spec・命題方向・設計監査
examples/            schema-valid examples
workspace/           manual ChatGPT handoff
item_bank/draft/     未承認
item_bank/approved/  使用可能
item_bank/rejected/  不採用
src/                 CLI / schema / validation / rendering
tests/               regression tests
output/              generated TeX/PDF
```

## まだやらないこと

現段階では API、LangChain、vector DB、fine-tuning、IRT、Web UI を優先しない。まず実際の候補問題を生成し、**教研担当者の修正時間がどこで発生するか**を確認してから自動化範囲を増やす。

## 次の優先順位

1. 2026本試・追試 dual baseline で full Q4 を5セット生成して human QA
2. prompt/schema の返工原因を記録
3. 2026追試で重要な地図・複合図など、現schemaで表現しにくい資料形式を必要に応じて追加
4. renderer のページ分割・図表品質を本番レベルへ
5. `used_in` と模試 assembly
6. Q5 pipeline
7. Q1/Q2/Q3
