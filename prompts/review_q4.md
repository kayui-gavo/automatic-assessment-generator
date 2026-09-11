# TABITO 共通テスト中国語 Q4 ブラインド独立審査 v0.3.2

以下は旅人教育の候補問題である。**標準解答・根拠・解説・生成者の自己評価は意図的に削除されている。**

生成者の答えを推測せず、まず受験者として各 task を独立に解き、その後に命題者として品質を審査すること。

本審査の item-writing baseline は **2026本試験 + 2026追・再試験を同格のTier-1** とする。2025以前は補助参考にすぎない。

## 審査順序

1. 全資料と設問だけを読み、各 task の答えを独立に決める。
2. 正答または正答集合が一意か、資料だけで根拠を確定できるか確認する。
3. 各資料が本当に必要か、A/Bで情報の使い方が変化しているか確認する。
4. 2026本試・追試の共通方向に合うか、どちらか一方の換皮になっていないか確認する。
5. 最後に中国語、日本語設問、誤答肢、難度勾配、資料構成を評価する。

## 重点項目

- 16 answer slots / A・B という hard structure が成立しているか（fullの場合）
- A/Bが一つの目的・活動として自然につながっているか
- BがAの単なる追加読解ではなく、再文脈化・適用・計画・条件照合・ケース判断・総合理解などへ進んでいるか
- **Bを無理に実務行動へ寄せていないか**。2026追試のような reflective synthesis も認める
- 資料タイプ数を稼ぐためだけの飾り資料がないか
- **図・地図・フローチャートに、本当に空間・経路・因果・階層・手順などの視覚的関係があるか。単なる「名称→分類」を箱にしただけなら table/list の方が適切であり、装飾的 visual と判定する**
- A/Bそれぞれに、単純な一資料の語句一致を超える情報処理があるか
- `within_compound` / `cross_source` と称しながら、実際は片方の資料だけで解けないか
- single-source の直接理解も適切に混在しているか。すべてを無理に複雑化していないか
- multi_select が「二つ選べ」を真似しただけでなく、複数記述を独立に検証させているか
- multi_slot_choice で共通選択肢を使う場合、選択肢の再利用可否が題面から明確か
- 数値資料が数学計算問題になっていないか
- 中国語が自然な現代語か。教材翻訳調・HSKドリル調・不自然な説明文になっていないか
- 選択肢が意図なく日本語文法と中国語文法を混在させていないか
- 日本語の設問が大学入試として簡潔・自然か
- 誤答肢に現実的な誤読経路があるか
- 架空統計を実在機関の公式データのように装っていないか
- 2026本試のペット系構造、追試の自動運転系構造の surface reskin になっていないか
- 2025以前の旧型を「昔よく出た」ために標準形として復活させていないか
- full 60点大問として情報量・変化・作業量が薄すぎないか、逆に過剰に複雑化していないか

## 2026 Blueprint

{{ blueprint_yaml }}

## 2026 Q4 Reference Patterns

{{ reference_patterns_yaml }}

## Q4 Template

{{ template_yaml }}

## Detailed Item-Writing Direction

{{ item_writing_direction }}

## 出力

JSON のみ。

必須フィールド：
- schema_version: `"0.2"`
- item_id
- verdict: `pass` / `revise` / `reject`
- independent_answers: `{task_id: [correct_option, ...]}`
  - multi_select は選択順を問わない
  - multi_slot_choice は answer_slots の順序に対応させる
- issues: severity(`high`/`medium`/`low`), task_id(optional), category, description, suggested_fix
- overall_comment_ja

## Blind Candidate

{{ item_json }}
