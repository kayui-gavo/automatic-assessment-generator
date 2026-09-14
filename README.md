# TABITO Common Test Chinese Mock-Exam Workbench

旅人教育の内部教研向け **大学入学共通テスト 中国語 模試制作システム**。

v0.5 から製品の中心は Q4 単問ではなく、**80分・200点・解答番号1–50の完整模試 production** です。Q1–Q5 は別々に生成・審査・返修し、最後に1冊の問題冊子として組み上げます。

LLM API は必須ではありません。ChatGPT を manual backend として使い、JSON / filesystem / Streamlit / XeLaTeX で production workflow を管理します。

## Model execution policy

正式命题では、モデル名よりも **推理强度と review の独立性** を固定します。

```text
Generation     GPT-5.6 Sol · High     fresh chat recommended
Blind Review   GPT-5.6 Sol · High+    fresh chat REQUIRED
Revision       GPT-5.6 Sol · High     fresh chat recommended
Human QA       人間                   release authority
```

ルール：

- production generation / review / revision に Instant / low-effort mode を使わない。
- Blind Review は、生成・返修・答案・rationale・教师标注を見ていない**全新对话**で実行する。
- 同じ ChatGPT conversation 内で生成した問題をそのまま「blind review」しても、release evidence として認めない。
- review import 時に model / reasoning / fresh-chat confirmation を candidate fingerprint と一緒に保存する。
- candidate を1文字でも実質修改した場合、旧 review / Human QA は stale になる。
- より強いモデルを使える場合も、deterministic validation / Blind Review / Human QA / PDF preflight を省略しない。

現在の manual-chat production policy は `src/tabito_itemgen/model_policy.py` にあり、生成される prompt 自体にも execution protocol が付与されます。

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

网页预览は LaTeX 不要。PDF compile だけ XeLaTeX が必要です。

## 命题基准

優先順位は固定します。

1. **Tier 0 — 2026 大学入試センター問題作成方針**：測る能力の境界だけを定義
2. **Tier 1 — 2026 本試験 + 2026 追・再試験**：唯一の current surface blueprint
3. **Tier 2 — 2025以前**：語彙・文法レベル、誤答肢、日本語設問、長期安定能力の参考のみ

2025以前の題型を平均して2026へ戻すことは禁止します。

Full-exam blueprint version：

```text
R8-2026-full-v1
```

## 完整模試

```text
Exam
├── Q1  発音・ピンイン             24点   1–6
├── Q2  語句                       16点   7–12
├── Q3  表現力                     40点  13–20
├── Q4  複合的な資料の読み取り     60点  21–36
└── Q5  長文読解                   60点  37–50

TOTAL 200点 / 80分 / 50解答欄
```

`main_2026` と `makeup_2026` の2 family を持ちます。Q1–Q3 は2026二套で安定している共通構造を使い、Q4/Q5 は本試・追試の違いを明示的に保持します。

## なぜ5回に分けて生成するか

「新建完整模試」は1つの Exam project を作りますが、LLM には Q1–Q5 を別々に依頼します。

```text
create Exam
   ↓
Q1 request → import → isolated blind review → Human QA
Q2 request → import → isolated blind review → Human QA
Q3 request → import → isolated blind review → Human QA
Q4 request → import → isolated blind review → Human QA
Q5 request → import → isolated blind review → Human QA
   ↓
Full Exam QA
   ↓
Release
```

これにより Q3 を直しても Q1/Q2/Q4/Q5 の section review は有効なままです。ただし整卷 fingerprint が変わるので Final Exam QA は stale になります。

## UI workflow

### 1. 新建完整模試

首页から：

- `2026 本試験型`
- `2026 追試験型`

を選び、必要なら模試名・Q4希望题材・Q5希望题材・教研备注を入力します。

作成後、Q1–Q5 五份の generation prompt が個別に用意されます。

### 2. Section production

各大题で：

```text
Generate Prompt (GPT-5.6 Sol · High)
→ JSON import
→ deterministic validation
→ Blind Review Prompt
→ NEW CHAT / GPT-5.6 Sol · High+
→ review import + execution provenance
→ Human QA
→ Revision Prompt（必要時）
→ 修订版 JSON 再导入
```

修訂版を再導入すると、その section だけ `draft` に戻り、旧 Blind Review / Human QA は fingerprint mismatch により自動で stale になります。返修に使った会話を次の Blind Review に再利用してはいけません。

### 3. Human QA

共通チェックに加え、各 section 専用チェックを持ちます。

- Q1：拼音、声母/韵母、声调、一/不变调、多音字、拼音版面、会话自然度、词汇负荷、辨音竞争性
- Q2：词汇用法、不适当项唯一性、语序唯一性、token 粒度、句法依赖、干扰 token 的局部可接续性
- Q3：拼音、翻译语义、干扰项错误类型、near-miss、keyword shortcut、语义操作多样性
- Q4：信息旅程、资料必要性、source integrity、2026 family fidelity、真正 cross-source dependency、认知操作多样性
- Q5：文章自然度、段落连贯、anchor、全文推理、词汇干扰强度、局部选项竞争、后半题功能多样性、著作权原创性、长文分页

Human QA では返工時間も保存します：

- first read
- language edit
- item edit
- layout edit
- biggest rework cause

この数据を使い、今後は「よく起きる返工原因」だけを prompt / schema / validator に戻します。

### 4. Final Exam QA

全 section ready 後に整卷だけを再確認します。

- 80分钟负荷
- 200分结构
- 1–50连续
- Q1–Q5视觉层级
- 难度节奏
- Q4/Q5题材重复
- 跨大题 solution leak
- 拼音 / 简体字 / 日本语设问统一
- 数字・标点・选项格式
- 分页・图表・长文可读性

### 5. Release

正式模試は次が全て通ったときだけ approve できます。

```text
Exam deterministic validation
+
Q1 ready
Q2 ready
Q3 ready
Q4 ready
Q5 ready
+
PDF artifact preflight
+
Final Exam Human QA
```

各 section の Blind Review gate は、正答一致だけでなく次も要求します。

```text
candidate fingerprint current
review verdict = pass
independent answers match
no high-severity issue
fresh chat confirmed
no authoring/revision context seen
reasoning >= High
current model-policy version
```

Approve は単なる copy ではありません。

- exam / section state を `approved` に変更
- `exam_bank/approved/<exam_id>/` に canonical copy を作成
- release fingerprint / gates / artifact evidence を記録
- 同一 draft を除去
- 同じ exam_id の別内容による上書きを禁止

Approved project は UI 上で read-only です。改题する場合は新版本を作ります。

## Version safety

Blind Review / Human QA は ID だけでなく **candidate content fingerprint** に binding されます。

```text
Q3 v1 → review/QA PASS
   ↓
Q3 を1文字でも実質修改
   ↓
Q3 v2 fingerprint changes
   ↓
Q3 review = stale
Q3 QA     = stale
Exam QA   = stale

Q1/Q2/Q4/Q5 evidence remains current
```

Multi-select は集合として比較しますが、Q2语序や multi-slot は解答位置に意味があるため **顺序を保持して比較**します。

## Section data models

Q1–Q5 を無理に1つの万能 Task に押し込みません。

- **Q1**：phonetic count / pinyin dialogue
- **Q2**：fill-choice / `token_pool + correct_sequence + answer_positions`
- **Q3**：ja→zh / zh→ja + distractor error taxonomy
- **Q4**：既存の rich multi-source `Item` をそのまま利用
- **Q5**：original paragraphs + stable anchors + long-reading tasks

Q4 は full Exam の Section 4 ですが、既存 Q4 JSON は引き続き load / validate / preview / render できます。

## Full booklet output

```text
output/<exam_id>/
├── student.tex
├── student.pdf
├── teacher.tex
├── teacher.pdf
├── answer_sheet.tex
├── answer_sheet.pdf
├── answer_key.json
└── artifact_manifest.json
```

1つの document 内で第1問→第5問を连续排版します。内部 ID、fingerprint、dependency metadata は学生版に出しません。

## CLI

日常は UI 推奨ですが、CLI も同じ production rule を使います。

```bash
# 完整模試 project + Q1–Q5 requests
tabito-itemgen new-exam --family main_2026 --title "旅人教育 中国語模試 第1回"

# Section JSON import
tabito-itemgen exam-import-section <EXAM_ID> Q1 q1_response.json

# Full validation
tabito-itemgen exam-validate <EXAM_ID>

# Section blind review prompt
tabito-itemgen exam-review-request <EXAM_ID> Q1

# Review は必ず全新对话で実行し、その事実を import 時に明示
tabito-itemgen exam-import-review <EXAM_ID> Q1 q1_review.json \
  --model "GPT-5.6 Sol" \
  --reasoning high \
  --fresh-chat-confirmed

# Revision
tabito-itemgen exam-revision-request <EXAM_ID> Q1

# Release gates
tabito-itemgen exam-release-check <EXAM_ID>

# Final Human QA は UI で保存後、全 gate PASS 時のみ approve
tabito-itemgen exam-approve <EXAM_ID>

# 連続冊子
tabito-itemgen exam-render <EXAM_ID> --compile
```

旧 Q4-only CLI (`new-item`, `validate`, `render` 等) は backward compatibility / 单独大题 production 用として残しています。

## Repository

```text
blueprints/                    2026 full-exam / section blueprints
prompts/                       Q1–Q5 generate / review / revise prompts
src/tabito_itemgen/            schema / production / validation / UI / renderer
examples/full_exam_schema_fixture/
                               schema + regression fixture; NOT quality exemplar
pilots/                        real content-QA candidates
benchmarks/                    future human-approved gold exemplars only
exam_bank/draft/               local unpublished full exams
exam_bank/approved/            local formally released full exams
item_bank/                     legacy Q4-only bank
workspace/exams/               local request / response / review / QA / release records
output/                        generated TeX/PDF
```

Live `workspace/exams/`, `exam_bank/draft/`, `exam_bank/approved/`, `output/` 内容は public repo に自動 commit しません。研究/回归用の候选题だけ `pilots/` に明确に置きます。

## Fixture / Pilot / Benchmark

- `examples/`：schema / renderer fixture。**質の見本ではない**
- `pilots/`：実際に content QA する候选模試・候选题
- `benchmarks/`：人間が正式に gold exemplar と認定したものだけ

既存 Q4 Pilot 001 は rejected、Pilot 002 / 003 v2 は Q4 surface regression 用に残します。

## 次に測ること

現段階では API、multi-agent framework、vector DB、fine-tuning、自動正答率予測、重い front-end は導入しません。モデルを増やす前に、production defect と受験者データを取ります。

まず測るのは：

1. 一套200点模試を最後まで作れるか
2. 各 section の人工返工に何分かかるか
3. 哪种 defect が何度起こるか
4. PDF に手修正がどれだけ必要か
5. 学生の section / item 解答時間
6. item difficulty（正答率）
7. distractor selection frequency
8. 上位群・下位群で正答率がどれだけ分かれるか

この実測がたまってから difficulty calibration / discrimination analysis / 必要なら IRT を導入します。`official_like` をモデルの自己申告だけで確定しません。
