# TABITO 共通テスト中国語 Q4 生成タスク v0.3.1

旅人教育の内部教研用に、共通テスト中国語 第4問の**原创候補問題**を作成する。

このタスクの基準は、**2026本試験と2026追・再試験を同格のTier-1ブループリント**とする。2025以前は歴史的参考にすぎず、2026型の構造を上書きしてはならない。

重要なのは「資料を何種類置くか」ではなく、**一つの目的・課題が進行する中で、受験者が中国語で得た情報を理解・比較・整理し、後の局面で再利用・適用・統合すること**である。

## 命題原則

1. 2026本試・追試の**共通点**だけを hard core として扱う。片方にしかない表面的特徴を必須化しない。
2. 2026本試のペット相談・保護センター・譲渡・リスクフローを別テーマに置換しただけの問題は禁止。
3. 2026追試の自動運転研究・SNS運行情報・交通略図・安全チラシを別テーマに置換しただけの問題も禁止。
4. full Q4 は A/B の二部構成、解答番号21〜36を**ちょうど1回ずつ**使用する。
5. AとBは同じ目的・活動の続きだが、情報の使い方を変える。Aは状況把握・調査・比較・整理を中心にし、Bは再文脈化・適用・計画・条件照合・ケース判断・振り返り等へ進める。
6. **Bを必ず実務行動で終わらせる必要はない。** 2026追試のような反省・総合理解も正当な終盤形式である。
7. 資料数・資料タイプ数を満たすために素材を増やさない。各資料にはシナリオ上の「読む理由」が必要である。
8. full では A・B それぞれに少なくとも1つ、単純な一資料の語句一致では解けない統合的 task を置く。
9. multi_select は2026両試験で重要だが、形式だけを真似しない。複数の記述を個別に検証させる必要があるときに使う。
10. 数値資料は計算力ではなく中国語での情報処理を測る。比較・割合・増減・条件判断を中心にし、重い計算を要求しない。
11. 中国語は自然な現代簡体字。専門語・低頻度語は必要に応じて glosses を付ける。HSK練習問題のような文法ドリル感を避ける。
12. 日本語の設問文は大学入試として簡潔・自然にする。説明口調・AI口調は禁止。
13. 正答または正答集合は一意。誤答肢は、部分一致・条件取り違え・範囲の読み違い・因果逆転・過剰推論など、現実的な誤読経路を持たせる。
14. 統計・制度・組織名を使う場合、架空の数値を実在機関の公式データのように見せない。内部原创の synthetic data ならその前提で設計する。
15. evidence は資料IDだけでなく locator に、該当発話・表セル・投稿・図の関係・条件等を人間が確認できる粒度で記す。
16. **下記 Generation Profile は2026二試験から抽象化済みである。公式問題の逐問配列を推測・復元し、それに沿って新題を並べない。**
17. JSON以外を出力しない。Markdown fence、前置き、後書きは禁止。

## Difficulty

`difficulty = official_like` の場合、16 answer slots 全体を均一な「中」にしない。2026本試・追試のように、直接理解・資料読解・比較・統合・適用が混在する**内部勾配**を作る。LLMの難度ラベルを実測難度とは扱わない。

## 複合資料と dependency_mode

各 task に `dependency_mode` を明示する。

- `single_source`: 1資料だけで答えが確定する。
- `within_compound`: 1つの複合資料、または同じ `bundle_id` の複数コンポーネントを組み合わせる。
- `cross_source`: 別資料・別bundleを組み合わせないと答えが確定しない。
- `scenario_plus_source`: それまでのシナリオ文脈と新しい資料を併用する。

説明文＋図、交通略図＋現地メモ＋システム図など、複数オブジェクトで一つの資料単位を構成する場合は同じ `bundle_id` を付ける。

## 使用可能な資料型

text:
- dialogue
- notice
- poster
- short_explanatory_text
- profile
- checklist
- memo
- reflection
- interview
- instructions

structured / visual:
- table
- timetable
- chart (`bar`, `horizontal_bar`, `stacked_bar`, `line`)
- flowchart
- social_feed
- schematic_map
- annotated_diagram

`social_feed` は複数投稿を時系列に持つ。`schematic_map` / `annotated_diagram` は node と edge で構成し、必要なら x/y を指定する。

## Blueprint

{{ blueprint_yaml }}

## 2026 Q4 Generation Profile

以下は本試・追試の**生成用に抽象化した設計空間**である。公式の逐問順序は意図的に含まれていない。

{{ generation_profile_yaml }}

## Q4 Template

{{ template_yaml }}

## Detailed Item-Writing Direction

{{ item_writing_direction }}

## Item Spec

{{ item_spec_json }}

## JSON設計上の注意

- `schema_version`: `"0.2"`
- `scope`: `full` / `mini`
- `difficulty`: `official_like` / `easy` / `medium` / `hard`
- `workflow.blueprint_version`: `"R8-2026-main-tsui-v2"`
- materials と tasks は subsection(A/B) と order を持つ。同じ subsection 内で order を重複させない。
- 必要に応じて material に `bundle_id` を付ける。
- task.response_mode:
  - `single_choice`: answer_slots は1個
  - `multi_select`: 同一選択肢群から複数正答。answer_slots は2〜3個
  - `multi_slot_choice`: 複数空所・複数ケース等を別々に解答。answer_slots は2〜3個
- fullの場合 answer_number は21〜36をちょうど一度ずつ使用。
- operations は task ごとに1〜3個。`organize` / `plan` / `synthesize` も使用できる。
- `dependency_mode` は全taskで明示する。
- single_choice / multi_select では `distractor_rationales_ja` に正答以外の全選択肢の誤り理由を書く。
- multi_slot_choice では `slot_distractor_rationales_ja` に各slotごとの誤答理由を書く。
- `quality_notes.ambiguity_risk` は原則 low。high の問題は納品しない。
- `quality_notes.source_integrity_note` に、資料が synthetic/original か、公的資料を参照した場合はその扱いを簡潔に書く。

出力前に、次を内部確認すること：

- A/Bが本当に一つの活動としてつながっているか
- 2026本試または追試の出来事の並びを換皮していないか
- 本試と追試の逐問パターンを交互に並べただけの hybrid になっていないか
- 2025以前の旧型が無意識に標準形として復活していないか
- 各資料が少なくとも一つの設問またはシナリオ進行に必要か
- A/Bそれぞれに統合的な情報処理があるか
- 後半が「同じ読解の続き」だけになっていないか
- 正答集合に曖昧さがないか

最終JSONだけを返すこと。
