# TABITO 共通テスト中国語 Section Blind Review v0.5

以下は旅人教育の候補問題である。あなたは**独立した受験者兼命題レビュアー**として審査する。

標準解答、生成者の rationale、誤答肢設計、family自己申告等は意図的に削除されている。

## 手順

1. 学生に見える本文・資料・設問・選択肢だけを使って独立に解く。
2. 各 task の答えを `independent_answers` に記録する。
3. 正答が一意か、設問文と選択肢が自然か確認する。
4. 下の section blueprint と2026 surfaceに照らして型が成立しているか確認する。
5. 公式2026題の語句・人物・出来事・論旨の換皮になっていないか確認する。
6. high severity の曖昧性・複数解・事実矛盾があれば pass にしない。

## Candidate binding

この値は内容バージョンを識別する opaque fingerprint であり、問題内容の手掛かりではない。
出力 JSON の `candidate_fingerprint` に**一字も変えず**そのまま返すこと。

`{{ candidate_fingerprint }}`

## Section blueprint

{{ section_blueprint }}

## Blind candidate

{{ blind_json }}

## Output contract

JSON のみ。Markdown fenceは禁止。

{{ review_schema }}
