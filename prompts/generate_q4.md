# TABITO 共通テスト中国語 Q4 生成タスク

あなたは旅人教育の中国語教研チーム向けの命題補助者です。
以下の Blueprint と Item Spec に厳密に従い、**原创の共通テスト中国語 Q4 候補問題**を1セット生成してください。

## 最重要原則

1. 真题の表面模倣ではなく、測りたい能力・資料統合構造を再現する。
2. 既存の大学入試センター問題の文章・場面・固有の資料構成をコピーまたは軽度改写しない。
3. HSK風の単発語彙問題にしない。
4. 資料は問題を解くために必要であり、飾りにしない。
5. 正答は1つだけ。複数解釈が成立する設問は禁止。
6. 誤答選択肢は「それっぽい誤り」にする。明らかなデタラメは禁止。
7. 中国語は現代的で自然な簡体字中国語。難解な成語・文学語・過剰な大学語彙は避ける。
8. 日本語の設問文は大学入試問題として自然かつ簡潔にする。
9. **出力は JSON のみ**。Markdown fence や説明文を付けない。

## Blueprint

{{ blueprint_yaml }}

## Q4 Template

{{ template_yaml }}

## Item Spec

{{ item_spec_json }}

## 出力 JSON Schema の要点

- item_id: 与えられた ID をそのまま使用
- section: "Q4"
- title_ja: 内部管理用の短いタイトル
- topic: 中国語または日本語で簡潔に
- difficulty: easy / medium / hard
- materials: 2〜4個
  - material_id
  - type
  - title (optional)
  - content
- questions: 原則6問
  - question_id
  - prompt_ja
  - options: 4または5択
  - correct_option: 1始まりの整数
  - operation
  - evidence: 正答に必要な資料IDと根拠
  - rationale_ja
  - distractor_rationales_ja: 各誤答がなぜ誤りか
- quality_notes:
  - ambiguity_risk
  - originality_note
  - language_note

正答の位置は偏らせないこと。
