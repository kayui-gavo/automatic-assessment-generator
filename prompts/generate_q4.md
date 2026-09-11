# TABITO 共通テスト中国語 Q4 生成タスク v0.2

旅人教育の内部教研用に、共通テスト中国語 第4問の**原创候補問題**を作成する。
これは「中国語の読解問題を6問作る」タスクではない。下記 Blueprint / Q4 Template / Item Spec に従い、
**一つの現実的な状況が進行し、その中で複数形式の資料を読み、情報を整理・比較・統合して判断する問題群**を作ること。

## 絶対条件

1. 共通テストの測定構造を再現し、近年本試験の文章・話題・固有の資料配列をコピーしない。
2. 2026本試の「動物保護センター→ペット資料→譲渡→フローチャート」のような固有シナリオを別テーマに置換しただけの問題は禁止。
3. scope=full の場合、解答番号21〜36を**ちょうど1回ずつ**使い、16 answer slots を作る。
4. A/Bの二段階を持たせる。Aは情報を受け取って理解・比較する局面、Bは後続行動で情報を利用して選択・判断する局面を中心にする。
5. fullでは6〜10資料程度を目安にし、少なくとも4種類の資料形式を用いる。表・時刻表・グラフ・フローチャートのいずれかを必ず含める。
6. 少なくとも3 tasks は2資料以上を本当に組み合わせないと解けないようにする。資料は飾りにしない。
7. single_choice だけにしない。multi_select または multi_slot_choice を少なくとも2 tasks 含める。
8. 正答（または正答集合）は一意。選択肢は文法的に自然で、誤答は明確な「読み違いの経路」を持つ。
9. 中国語は自然な現代簡体字。日本の高校で中国語を学ぶ受験生を想定し、専門語・低頻度語は必要に応じて glosses に注を付ける。
10. 日本語の設問文は大学入試として簡潔・自然にする。説明口調・AI口調は禁止。
11. evidence は「資料ID」だけでは不足。locator に、該当発話・表セル・グラフ系列・条件等を人間が確認できる粒度で書く。
12. JSON以外を出力しない。Markdown fence、前置き、後書きは禁止。

## Blueprint

{{ blueprint_yaml }}

## Q4 Template

{{ template_yaml }}

## Item Spec

{{ item_spec_json }}

## JSON設計上の注意

- schema_version: "0.2"
- scope: full / mini
- materials と tasks は subsection(A/B) と order を持つ。order は同じ subsection 内で重複させない。
- material type は schema で定義された形式を使う。
- task.response_mode:
  - single_choice: answer_slots は1個
  - multi_select: 同一選択肢群から複数正答。answer_slots は2〜3個
  - multi_slot_choice: 複数の空所・ケース等を別々に解答。answer_slots は2〜3個
- answer_slots の各要素:
  - slot_id
  - answer_number
  - correct_option (1始まり)
- fullの場合 answer_number は21〜36をちょうど一度ずつ使用。
- operations は task ごとに1〜3個。
- single_choice / multi_select では distractor_rationales_ja を用い、**正答以外の全選択肢番号**をキーにする。
- multi_slot_choice では slot_distractor_rationales_ja を用い、各 slot_id ごとに、その slot の正答以外の全選択肢番号の誤り理由を書く。
- quality_notes.ambiguity_risk は原則 low。high の問題は納品しない。

内部で十分に検討してから、最終JSONだけを返すこと。
