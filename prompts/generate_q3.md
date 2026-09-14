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

## Distractor quality — 最重要

- 誤答肢は、原文の主要命題をできるだけ保持したまま **1～2個の意味次元だけ** をずらす。
- 一つの誤答で「主体・時制・因果・出来事そのもの」を同時に全部変えるような大外しは禁止。
- 4択すべてを自然な中国語 / 日本語として成立させる。文法的に壊れた文を誤答にしない。
- 学習者が一つの接続詞だけ見て即答できる設計を連発しない。
- 少なくとも各大問内で2題は、正答と誤答2肢が表面的にはほぼ同じ内容を述べ、scope / aspect / modality / subject-object 等の細部を読まないと区別できない形にする。
- `distractor_error_types` は後付けのラベルではない。実際の誤りがその taxonomy に対応していることを自分で再確認する。

## Set-level balance

- 8題すべてを「因果 vs 譲歩」のような同じ構文判別にしない。
- scope / aspect / modality / subject_object / lexical_meaning / pragmatic_force 等をセット全体で分散させる。
- 13と20が同じ思考量にならないよう、後半には少なくとも数題、文全体の関係を保持しないと選べない設問を置く。
- 正答位置は極端に偏らせない。可能なら1～4を各2回程度にするが、内容より位置調整を優先してはならない。

## Final self-check before output

各誤答について、正答との違いを一文で説明する。その説明が「全然違う内容だから」で済む場合、その誤答は作り直す。

## Item spec

{{ item_spec_json }}

## 2026 Q3 blueprint

{{ section_blueprint }}

## Output schema

JSON Schema に完全適合する JSON だけを返す。説明や Markdown fence は禁止。

{{ json_schema }}