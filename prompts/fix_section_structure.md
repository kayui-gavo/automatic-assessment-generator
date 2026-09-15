# TABITO 共通テスト中国語 Section Structure Repair v0.5

以下の candidate は JSON schema として読み込めるが、決定的な構造検証に失敗している。
この工程では命題内容を作り直さず、列挙された構造エラーだけを確実に解消する。

## 修正原則

- section family、解答番号、配点、問題構造を勝手に変えない。
- 本文・選択肢・正答・難度は、エラー解消に必要な場合を除いて変更しない。
- 欠落 metadata や不整合だけを最小限修正する。
- Q1 の内部 pinyin / target_index、Q2 ordering の token 整合、Q5 anchor など、学生には見えない metadata も validator の要求に合わせて修正する。
- 構造修正を口実に問題を簡単化しない。
- 公式問題や reviewer-only reference を参照・模倣しない。
- 修正後は完全な section JSON 全体を返す。差分や説明は返さない。

## Deterministic validation errors

{{ validation_errors }}

## Section blueprint

{{ section_blueprint }}

## Current candidate

{{ item_json }}

## Output schema

JSON Schema に完全適合する JSON だけを返す。Markdown fence、説明は禁止。

{{ json_schema }}
