# TABITO 共通テスト中国語 第2問 生成

2026本試験・追試験を同格の一次 surface blueprint として、完全原创の第2問を作る。

## Hard surface

- A：解答7。中国語文の空欄に入る最も適当な語句を4択から選ぶ。
- B：解答8。同様の形式だが、適当でないものを選ぶ。`selection_rule=inappropriate` を明示する。
- C：和文中訳の語順問題2題。各題は8 tokenから必要な4 tokenを選び、正しい中国語文を組む。解答枠は9–10、11–12。
- Cは ordinary multiple choice に変形しない。token_pool / correct_sequence / answer_positions を完全に記録する。
- 文は高校中国語として自然で、公式文の語句置換や構文コピーを避ける。
- 正答は一意。Bの「不適当」も複数解にならないよう確認する。

## Item spec

{{ item_spec_json }}

## 2026 Q2 blueprint

{{ section_blueprint }}

## Output schema

JSON Schema に完全適合する JSON だけを返す。説明や Markdown fence は禁止。

{{ json_schema }}
