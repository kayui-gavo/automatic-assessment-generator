# TABITO Common Test Chinese Mock-Exam Workbench

旅人教育の内部教研向け **大学入学共通テスト 中国語 模試制作システム**。

v0.5 は Q1–Q5 を別々に生成・審査・返修し、最後に **80分・200点・解答番号1–50** の1冊の模試へまとめる production workbench です。

LLM API は必須ではありません。現在の標準運用は ChatGPT を manual backend とし、JSON / Streamlit / filesystem / XeLaTeX で制作状態と release evidence を管理します。

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

ブラウザ UI は通常 `http://localhost:8501`。网页预览は LaTeX 不要、PDF compile だけ XeLaTeX が必要です。

## 模試構成

```text
Q1  発音・ピンイン             24点   1–6
Q2  語句                       16点   7–12
Q3  表現力                     40点  13–20
Q4  複合的な資料の読み取り     60点  21–36
Q5  長文読解                   60点  37–50

TOTAL 200点 / 80分 / 50解答欄
```

`main_2026` と `makeup_2026` の2 family を持ちます。2026本試験・追試験を current surface blueprint とし、2025以前は難度・語彙・誤答肢等の補助参考に限定します。

Full-exam blueprint version：`R8-2026-full-v1`

## Production workflow

正式運用は次の順序です。

```text
Generate
  ↓
deterministic validation
  ↓
独立审题
  ↓
教师确认
  ↓
必要なら返修 → 新版本に対して再び独立审题
  ↓
Q1–Q5 すべて已就绪
  ↓
PDF preflight
  ↓
整卷教师确认
  ↓
Release
```

### Model execution policy

現在の manual-chat production baseline：

```text
Generation       GPT-5.6 Sol · High
独立审题          GPT-5.6 Sol · High 以上
Revision         GPT-5.6 Sol · High
教师确认          人間
```

production generation / review / revision に Instant / low-effort mode を使いません。

### 独立审题の隔離条件

普通の「新しい Chat」だけでは release evidence として十分ではありません。cross-chat memory が適用される可能性があるため、独立审题は **memory-isolated context** で実行します。

現在許可する context mode：

```text
non_personalized_temporary_chat
stateless_api
other_memory_isolated
```

UI の標準手順は **非個性化 Temporary Chat** です。

独立审题モデルには学生に見える題面だけを渡します。標準解答、rationale、distractor rationale、evidence locator、dependency / operation label、Q1 A/B/C の内部拼音、authoring metadata 等は blind packet から削除します。

review import 時には以下を candidate fingerprint と一緒に保存します。

- model
- reasoning level
- memory-isolated context mode
- independent-context confirmation
- authoring / revision context を見ていないこと
- production policy version

candidate を実質修改すると旧 review / 教师确认は stale になります。

## UI

左側の制作ナビ：

```text
总览
Q1 发音・拼音
Q2 词语
Q3 表达
Q4 综合资料
Q5 长文阅读
定稿发布
```

主な teacher-facing status：

```text
未出题
需修正
待独立审题
待教师确认
需要返修
不采用
已就绪
已定稿
```

内部 pipeline 名ではなく、老师が次に何をすべきかで表示します。

### Section workflow

各大题では：

```text
出题
→ JSON 导入
→ 格式与结构检查
→ 独立审题
→ 教师确认
→ 必要なら返修
```

- 構造エラーは独立审题より前に修正します。
- review execution の隔離条件だけが失敗した場合は **改题せず、重新独立审题** します。
- review 内容または教师确认が `revise` の場合だけ返修します。
- `reject` は「不采用」として扱い、現在版本を历史に残したまま重新出题します。
- 教师确认で「通过」を選ぶ場合、通用检查＋Section专项检查をすべて満たす必要があります。

### Version safety / rollback

新しい candidate を导入する前に現在版本を自動で content-addressed history に保存します。

```text
exam_bank/draft/<exam_id>/history/q1/<fingerprint>.json
...
```

UI の「历史版本 / 回退」から復元できます。復元時も現在版本は先に history へ保存されるため、回退自体も不可逆操作ではありません。

同一 fingerprint に binding された過去の review / QA evidence は、current production policy を満たす場合のみ再び有効になります。

## Deterministic surface contracts

Pydantic の型チェックだけでなく、実際の学生題面を壊す組み合わせを入庫前に拒否します。

現在の主な hard checks：

- Q1 A/B 候補 label は model-controlled content とせず、booklet convention の `a–d` に正規化
- Q1 A/B の multi-character target は underline position 必須
- Q2 ordering は4 blank / 4-token sequence を一致させる
- Q2 answer position / answer number は左→右の順序を保持
- Q5 marker は対象段落で一意
- Q5 underline `source_excerpt` は visible marker 直後の実テキストと一致
- Q5 blank anchor は source excerpt を持たない

Browser preview と XeLaTeX booklet は Q2 ordering / Q5 anchor に同じ surface helper を使います。

## Human QA

### Section 共通检查

- 中文自然度
- 日本語設問自然度
- 正答唯一性
- distractor competition
- 2026 surface fidelity
- official-like difficulty
- shortcut resistance
- originality
- layout readability
- no solution leak

加えて Q1–Q5 それぞれに专项检查があります。

### 整卷教师确认

Q1–Q5 がすべて Ready かつ current PDF が preflight 済みになった後に実施します。

- 80分で解けるか
- 200点 / 1–50 が完整か
- Q1–Q5 の视觉层级
- 难度节奏
- Q4 / Q5 题材の重複
- 跨大题 solution leak
- 拼音 / 简体字 / 日本語設問の统一
- 数字・标点・选项形式
- 分页・图表・长文可读性

## PDF / artifact safety

出力：

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

PDF preflight は missing character、重大な overfull、PDF hash 等を検査します。

`artifact_manifest.json` は exam fingerprint と **renderer implementation fingerprint** に binding されます。renderer / surface / answer-sheet / preflight 実装が変わった場合、同じ問題内容でも旧 PDF は current release evidence として使えません。再生成が必要です。

一方、過去に定稿した artifact manifest 自体は将来の renderer 更新後も audit 用に読み取れるようにします。

## Release gate

正式模試は次がすべて通った場合だけ approve できます。

```text
Exam deterministic validation
+
Q1 Ready
Q2 Ready
Q3 Ready
Q4 Ready
Q5 Ready
+
current PDF artifact preflight
+
整卷教师确认
```

各 Section の独立审题 gate は最低限：

```text
candidate fingerprint current
review verdict = pass
independent answers match author key
no high-severity issue
memory-isolated context confirmed
no authoring / revision context seen
reasoning >= production minimum
current model-policy version
```

Approve 時：

- exam / section state を `approved` に変更
- `exam_bank/approved/<exam_id>/` に canonical copy
- current artifacts を同梱
- release fingerprint / gate evidence / review execution provenance を保存
- draft を除去
- 同じ exam_id の別内容による上書きを禁止

Approved project は UI 上 read-only です。

## CLI

日常制作は UI 推奨ですが、CLI も同じ production data を使います。

```bash
# 新建模试
tabito-itemgen new-exam --family main_2026 --title "旅人教育 中国語模試 第1回"

# Section import
tabito-itemgen exam-import-section <EXAM_ID> Q1 q1_response.json

# Validation
tabito-itemgen exam-validate <EXAM_ID>

# 独立审题 request
tabito-itemgen exam-review-request <EXAM_ID> Q1

# Revision request
tabito-itemgen exam-revision-request <EXAM_ID> Q1

# Full booklet + PDF preflight
tabito-itemgen exam-render <EXAM_ID> --compile

# Release readiness
tabito-itemgen exam-release-check <EXAM_ID>

# 全 gate PASS 後のみ
tabito-itemgen exam-approve <EXAM_ID>
```

独立审题 import の実際の context mode / execution options は current CLI help と `src/tabito_itemgen/model_policy.py` を正とします。README の古い `fresh chat` 表現を運用根拠にしないでください。

旧 Q4-only CLI (`new-item`, `validate`, `render` 等) は backward compatibility / 单独大题 production 用として残しています。

## Repository layout

```text
blueprints/                    2026 section blueprints
prompts/                       Q1–Q5 generate / review / revise prompts
src/tabito_itemgen/            schema / production / validation / UI / renderer
examples/                      schema / renderer fixtures
pilots/                        content-QA candidates
benchmarks/                    future human-approved gold exemplars only
exam_bank/draft/               unpublished full exams
exam_bank/approved/            released full exams
workspace/exams/               requests / responses / review / QA / release records
output/                        generated TeX / PDF / manifests
```

Live `workspace/exams/`, `exam_bank/draft/`, `exam_bank/approved/`, `output/` は public repo に自動 commit しません。

## 次に測ること

現段階では API / multi-agent framework / vector DB / fine-tuning / IRT を先に増やしません。まず実際の production defect と学生データを取ります。

- 1套200点模試を最後まで作れるか
- Section ごとの人工返工時間
- defect frequency
- PDF 手修正量
- 学生の item / section 解答時間
- 正答率
- distractor selection frequency
- 上位群 / 下位群の discrimination

`official_like` はモデルの自己申告ではなく、Human QA と pilot data で更新します。
