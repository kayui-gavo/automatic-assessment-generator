# TABITO Common Test Chinese Item Generator

旅人教育の内部教研向け **共通テスト中国語 命題 Workbench**。

現在は第4問（Q4）を優先し、**2026 本試験 + 2026 追・再試験を同格の唯一の一次蓝本**として、原创問題の命題・独立審査・人工QA・正式題庫化・学生版/教師版組版までをローカルUIで扱う。

API は不要。ChatGPT Plus を manual LLM backend として使う。

## 起動

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

## v0.4.2 の生产流程

UI は5つの仕事に分ける。

### 1. 📄 试卷

最初に学生視点で読む。

- **学生册**：A/B・問1〜3・小問・資料・解答欄を本番冊子に近い階層で確認
- **教师标注**：正答、根拠、解説、誤答肢分析
- **结构检查**：answer slot / response mode / dependency / material type

旧 Pilot・rejected sample はデフォルトで隠す。

### 2. ✨ 命题

1. `main_2026` / `makeup_2026` を選ぶ
2. 題材と追加条件を入力
3. UI が `request.md` / `spec.json` を生成
4. request を ChatGPT Plus の新規対話へ貼る
5. 返ってきた JSON を UI へ貼る
6. **Draft として保存し、その場で validation**

同じUI sessionで作った request がある場合、返答 JSON の

- `item_id`
- `surface_family`
- `blueprint_version`

を request spec と照合する。別の request の出力を誤って取り込まない。

### 3. ✅ 审题

順序は固定する。

```text
Deterministic QA
      ↓
Blind Review
      ↓
Human QA
```

Blind Review は author key / evidence / rationale / family label を見ない独立解答。reviewer JSON は `workspace/reviews/` に保存する。

Human QA では少なくとも以下を人間が確認する。

- 中国語の自然さ
- 日本語設問の自然さ
- 正答唯一性
- 誤答肢の妥当性
- 2026 surface fidelity
- 情報の流れ
- 図表・資料の必要性
- originality / 非換皮
- source integrity
- レイアウト可読性
- solution leak がないこと

返工時間と実際に起きた defect も構造化して `workspace/human_qa/` に保存する。

### 4. 🚀 Release

正式題庫へ入るには **4 gate 全部**が必要。

```text
1 deterministic validation
2 blind review
3 human QA
4 approved-bank similarity
```

さらに review / Human QA は `item_id` だけでなく、**その時点の内容 fingerprint** に結び付く。

したがって、審査後に設問・選択肢・正答・資料・解説・blueprint 等を1文字でも実質変更すると、旧 review / QA は自動的に stale になり、再審査が必要になる。

Approve は単なるファイルコピーではない。

- 全 gate を再確認
- canonical JSON の `workflow.state` を `approved` に変更
- `item_bank/approved/` へ保存
- 同一 draft を除去
- `workspace/releases/<item_id>.release.json` に fingerprint と gate 結果を記録

同じ `item_id` で内容の異なる approved item を上書きすることはできない。

### 5. 🛠 编辑 / 导出

通常は JSON を直接触らない。

必要な場合のみ高度な JSON editor を使う。保存すると canonical state は `draft` に戻り、内容 fingerprint が変われば旧 review / Human QA は無効になる。

网页预览は LaTeX 不要。PDF 生成だけ XeLaTeX が必要。

---

## 命题的一次蓝本

優先順位は固定する。

1. **Tier 0** — 2026 大学入試センター問題作成方針：測る能力の境界
2. **Tier 1** — **2026 本試験 + 2026 追・再試験**：Q4 の実際の型
3. **Tier 2** — 2025以前：語彙・文法レベル、誤答肢、日本語設問等の歴史的参考のみ

2025以前の題型を平均化して2026へ戻さない。

現在の blueprint：

```text
R8-2026-main-tsui-v3
```

## 2026 Q4 surface family

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

新規生成は `subsection_intros_ja.A/B` も持ち、A/B 冒頭の日本語導入まで題面として審査する。

詳細：

- `docs/Q4_SURFACE_GRAMMAR_2026.md`
- `docs/EXAM_SPEC_2026.md`
- `docs/ITEM_WRITING_DIRECTION_2026.md`
- `blueprints/q4_2026_reference_patterns.yaml`
- `blueprints/q4_2026_generation_profile.yaml`

## Pilot / benchmark

- `examples/` — schema / renderer fixture。質の見本ではない
- `pilots/` — real content-QA candidate
- `benchmarks/` — 将来、人間が本当に承認した gold exemplar のみ

現状：

- Pilot 001 — **REJECTED**。generic multi-source reading に寄りすぎた失敗例
- Pilot 002 — active `main_2026` candidate
- Pilot 003 v1 — **SUPERSEDED**。option-language surface が不十分
- Pilot 003 v2 — active `makeup_2026` candidate

## CLI

UI を使わない場合も同じ release rule を使う。CLI から gate を迂回する override は置かない。

```bash
# request
tabito-itemgen new-item --topic "地域施設の利用改善" --family main_2026

# ChatGPT JSON を draft 化
tabito-itemgen import-response response.json

# deterministic validation
tabito-itemgen validate item_bank/draft/TABITO-CN-Q4-....json

# blind review request
tabito-itemgen review-request item_bank/draft/TABITO-CN-Q4-....json

# reviewer JSON を current draft に bind して保存
tabito-itemgen import-review reviewer.json

# 必要なら revision prompt
tabito-itemgen revision-request \
  --item item_bank/draft/TABITO-CN-Q4-....json \
  --review workspace/reviews/TABITO-CN-Q4-....review.json

# 全 release gate を確認
tabito-itemgen release-check item_bank/draft/TABITO-CN-Q4-....json

# Human QA まで保存済みで全 gate PASS の場合のみ approve
tabito-itemgen approve item_bank/draft/TABITO-CN-Q4-....json

# PDF
tabito-itemgen render item_bank/approved/TABITO-CN-Q4-....json --compile
```

Human QA の入力は現在 UI が標準。CLI で無理に bypass しない。

## Repository

```text
blueprints/          2026 blueprint / official structural reference metadata
templates/           generation constraints
prompts/             generate / blind review / revise
docs/                exam spec / surface grammar / item-writing direction
examples/            schema regression fixtures; NOT gold content
pilots/              real content-QA candidates + revision history
benchmarks/          future human-approved gold exemplars
workspace/           local request / response / review / QA / release records
item_bank/draft/     unapproved candidates
item_bank/approved/  released items
item_bank/rejected/  rejected items
src/                 CLI / UI / schema / validation / presentation / rendering
tests/               regression tests
output/              generated TeX/PDF
```

`workspace/` の生成記録と `output/` は `.gitignore` でローカル保持する。

## 今やらないこと

API、LangChain、vector DB、fine-tuning、IRT、重いWeb frameworkは優先しない。

優先するのは：

1. `main_2026` / `makeup_2026` の候補問題を実際に作る
2. blind review + 中国語自然度 + 共通テスト命題観点で人間が直す
3. **何を何分直したか**を保存する
4. 頻発 defect だけを prompt / schema / validator に戻す
5. 学生が実際に読む冊子の可読性を上げる
