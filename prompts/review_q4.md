# TABITO 共通テスト中国語 Q4 ブラインド独立審査 v0.4

以下は旅人教育の候補問題である。標準解答・根拠・解説・生成者の自己評価は意図的に削除されている。

まず受験者として独立に解き、その後に命題者として品質を審査する。

## 最重要

2026本試験・追試験を、抽象的能力だけでなく**Q4のsurface grammar**として審査基準にする。

full Q4 では、候補が `main_2026` / `makeup_2026` のどちらのfamilyを狙っているかを判定し、次を確認する。

### 共通A 21〜28
- 21・22：中国語会話文 + 二つ選べ
- 23〜26：調査・表・グラフ・説明文＋図等による4枠の資料読解
- 27・28：講演まとめ / memo / まとまりある説明資料 + 二つ選べ

### main_2026 B
- 29・30：checklist / 条件資料 + 二つ選べ
- 31〜33：profile/candidate照合2枠 + 必要な追加情報の推論1枠
- 34〜36：rule/flow/process の一般原則1枠 + 二つのcase適用2枠

### makeup_2026 B
- 29・30：時系列運用情報を使った計画・日時等の二つ選択
- 31〜34：compound operational source 2枠 + 別のpractical document 2枠
- 35・36：reflection / summary / opinion text + 二つ選べ

この型から大きく外れ、ただの「多資料読解」になっている場合は、内容が良くても `revise` 以上とする。

## 審査順序

1. 全資料と設問だけを読み、各taskを独立に解く。
2. 正答集合が一意か確認する。
3. 21〜36の配置が選択した2026 familyのsurface grammarに沿うか確認する。
4. 中国語、日本語設問、誤答肢、資料密度を評価する。
5. 公式本文・case・数値の軽い言換えになっていないか確認する。

## 重点項目

- Aが「会話2 → 調査資料4 → 講演/memo2」になっているか
- Bがmain型またはmakeup型として明確に成立しているか
- 本試型と追試型を無秩序に混ぜていないか
- 資料が細切れカード化されず、共通テスト冊子らしい情報密度があるか
- 日本語が課題を設定し、中国語資料が実際の情報を担っているか
- 二つ選べが自然に多く、単選ばかりのworksheetになっていないか
- 図・地図・フローが装飾ではなく本当に関係を表しているか
- 正答肢・誤答肢に自然な読解差があるか
- 数値問題が重い計算ではなく情報読解になっているか
- 中国語が自然な現代簡体字か
- 日本語設問がDNC冊子に置いて違和感のない文体か
- ペット→別商品、自動運転→別交通のような名詞置換reskinになっていないか
- 逆に、原创性を意識しすぎて2026の題型から離れていないか

## 2026 Blueprint

{{ blueprint_yaml }}

## 2026 Q4 Reference Patterns

{{ reference_patterns_yaml }}

## 2026 Q4 Surface Grammar

{{ surface_grammar }}

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
- issues: severity(`high`/`medium`/`low`), task_id(optional), category, description, suggested_fix
- overall_comment_ja

## Blind Candidate

{{ item_json }}
