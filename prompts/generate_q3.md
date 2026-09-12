# TABITO 共通テスト中国語 第3問 生成

2026本試験・追試験を同格の一次 surface blueprint として、完全原创の第3問を作る。

## Hard surface

- A：13–16、4題。日本語→中国語。選択肢は声調符号付きピンイン。
- B：17–20、4題。声調符号付きピンイン中国語→日本語。
- 単語の1対1対応ではなく、文全体の意味、語用、否定範囲、条件、結果・原因等を判断させる。
- 各誤答肢には `distractor_error_types` と具体的な日本語 rationale を付ける。
- error type は schema の taxonomy から選ぶ。
- 正答・誤答とも自然な言語表現にする。露骨な誤文で難度を作らない。
- 2026公式文の構文・意味関係をそのまま名詞置換しない。

## Item spec

{{ item_spec_json }}

## 2026 Q3 blueprint

{{ section_blueprint }}

## Output schema

JSON Schema に完全適合する JSON だけを返す。説明や Markdown fence は禁止。

{{ json_schema }}
