# TABITO 共通テスト中国語 命題支援ツール

旅人教育の内部教研用。**v0.1 は共通テスト中国語 第4問（複合資料読解）に限定**し、ChatGPT Plus を手動生成エンジンとして利用する。

このプロジェクトの目的は研究用の自動採点基盤を作ることではなく、教研担当者が高品質な原创問題を短時間で作り、审题し、题库化し、学生版・教师版へ整形できるようにすること。

## v0.1 の設計方針

- API 不要。ChatGPT Plus との手動往復を前提にする。
- 真题の文章や场景をコピーしない。再現するのは能力・资料结构・判断形式。
- LLM に全部任せず、Blueprint / Template / JSON Schema を固定する。
- 生成物は必ず draft から始め、人間が approve する。
- Python は「正誤判断」ではなく、形式・構造・整合性チェックを担当する。
- Q4 が安定してから Q1/Q2/Q3/Q5 を追加する。

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## 最短ワークフロー

### 1. 新規 Q4 の生成依頼を作る

```bash
tabito-itemgen new-item \
  --topic "学校文化祭" \
  --difficulty medium \
  --domain school_life
```

`workspace/requests/` に以下ができる。

- `*.spec.json`
- `*.request.md`

`request.md` を ChatGPT Plus にそのまま渡す。

### 2. ChatGPT の JSON を保存する

ChatGPT の返答を例えば：

```text
workspace/responses/TABITO-CN-Q4-xxxx.json
```

として保存。

### 3. draft に取り込む

```bash
tabito-itemgen import-response workspace/responses/TABITO-CN-Q4-xxxx.json
```

### 4. 自動チェック

```bash
tabito-itemgen validate item_bank/draft/TABITO-CN-Q4-xxxx.json
```

現在は主に以下を检查する。

- JSON / Pydantic schema
- 资料 ID / 设问 ID の重複
- correct_option の範囲
- 选项重复
- evidence が存在する资料を参照しているか
- Q4 に複数资料統合問題が最低1問あるか
- 正答位置の極端な偏り
- cognitive operation の種類
- distractor rationale の不足

### 5. 独立审题 Prompt を作る

```bash
tabito-itemgen review-request item_bank/draft/TABITO-CN-Q4-xxxx.json
```

生成された `workspace/reviews/*.review_request.md` を**できれば別 Chat**に渡す。

返ってきた JSON を保存後：

```bash
tabito-itemgen import-review review.json
```

### 6. 修订依頼を作る

```bash
tabito-itemgen revision-request \
  --item item_bank/draft/TABITO-CN-Q4-xxxx.json \
  --review workspace/reviews/TABITO-CN-Q4-xxxx.review.json
```

### 7. 教研确认後 approve

```bash
tabito-itemgen approve revised_item.json
```

### 8. 学生版 / 教师版 LaTeX を生成

```bash
tabito-itemgen render item_bank/approved/TABITO-CN-Q4-xxxx.json
```

XeLaTeX が使える环境なら：

```bash
tabito-itemgen render item_bank/approved/TABITO-CN-Q4-xxxx.json --compile
```

## ディレクトリ

```text
blueprints/          共通テスト中国語全体の命題方針
templates/           各大問の具体的な生成制約
prompts/             ChatGPT Plus 用 prompt
workspace/requests/  生成依頼
workspace/responses/ ChatGPT 返答の一時保存
workspace/reviews/   独立审题・修订依頼
item_bank/draft/     未承認题
item_bank/approved/  授业・模试で使ってよい题
item_bank/rejected/  不採用题
src/                 CLI / validator / renderer
output/              LaTeX / PDF
```

## v0.2 候補

優先順位は实际使用後に決めるが、現時点では：

1. Q4 の资料 renderer（表・時間表・簡易チャート）
2. 題庫内 n-gram 重複チェック
3. 使用履歴 `used_in` と重复出题防止
4. 模試単位の assembly
5. Q5 长文 pipeline
6. Q1/Q2/Q3

API backend、Web UI、vector DB、fine-tuning、IRT は当面対象外。
