# TABITO 共通テスト中国語 Section Revision v0.5

以下の候補 section を、Blind Review の指摘だけを直すのではなく、2026 surface blueprint と原创性を維持したまま修訂する。

## 修訂原則

- high/medium issue は具体的に解消する。
- 正答唯一性を最優先する。
- 問題の型・解答番号・section family を勝手に変えない。
- 一つの曖昧性を直すために別の曖昧性を作らない。
- 公式2026題への類似度を上げる方向の修訂は禁止。
- Q5なら paragraph/anchor id を不用意に壊さない。
- Q2 ordering なら token_pool/correct_sequence/answer_positions の整合を保つ。
- 修訂後は完全な section JSON 全体を返す。差分だけ返さない。

## Section blueprint

{{ section_blueprint }}

## Current candidate

{{ item_json }}

## Review

{{ review_json }}

## Output schema

JSON Schema に完全適合する JSON だけを返す。Markdown fence、説明は禁止。

{{ json_schema }}
