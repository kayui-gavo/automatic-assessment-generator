# TABITO 共通テスト中国語 Q4 修訂タスク v0.4.1

候補問題とブラインド独立審査結果を照合し、必要箇所を修訂する。

## 最重要

修訂後も、候補が選択した2026 surface familyを維持する。

- `main_2026`：本試型
- `makeup_2026`：追試型

修訂のために一般的な「多資料読解」に戻してはならない。

### 冊子導入
- `subsection_intros_ja.A/B` を維持または改善する。
- 誰が何の目的で資料を読むかを自然に示す。
- 答え・結論・資料の読み方を先に説明しすぎない。
- BはAの言換えだけにせず、情報の用途や場面の変化を示す。

### 共通A 21〜28
- 21・22：中国語会話文 + 二つ選べ
- 23〜26：調査・表・グラフ・説明文＋図等の4枠資料読解
- 27・28：講演まとめ / memo / まとまりある説明資料 + 二つ選べ

### main_2026 B
- 29・30：checklist / 条件資料 + 二つ選べ
- 31〜33：profile/candidate照合2枠 + 必要な追加情報1枠
- 34〜36：rule/flow/process の一般原則1枠 + 二つのcase適用2枠

### makeup_2026 B
- 29・30：時系列運用情報を使った計画・日時等の二つ選択
- 31〜34：compound operational source 2枠 + practical document 2枠
- 35・36：reflection / summary / opinion text + 二つ選べ

## 修訂原則

- `item_id` / `schema_version` / `scope` / `surface_family` / answer_number は維持する。
- `workflow.blueprint_version` は `R8-2026-main-tsui-v3`。
- high issue は必ず解消する。
- reviewer とkeyが不一致なら、keyだけ変更せず資料・設問・選択肢の曖昧さを直す。
- 成立している部分を無意味に全面書換えしない。
- ただしsurface familyが崩れている場合は、関連ブロックをまとめて再構成する。
- 中国語本文・数値・固有名詞・case・正誤関係は原创を維持する。
- 公式本文の軽い言換えや名詞置換はしない。
- 逆に、原创性を理由に2026の設問骨格から離れない。
- 資料を細切れカードにしすぎず、共通テスト冊子らしい密度を保つ。
- 図・地図・flowは本当に視覚関係が必要なときだけ使う。
- JSONのみ返す。

## 2026 Blueprint

{{ blueprint_yaml }}

## 2026 Q4 Generation Profile

{{ generation_profile_yaml }}

## 2026 Q4 Surface Grammar

{{ surface_grammar }}

## Q4 Template

{{ template_yaml }}

## Detailed Item-Writing Direction

{{ item_writing_direction }}

## Candidate Item (answer-aware)

{{ item_json }}

## Blind Review

{{ review_json }}
