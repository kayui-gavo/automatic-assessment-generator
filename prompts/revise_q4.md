# TABITO 共通テスト中国語 Q4 修訂タスク v0.2

候補問題とブラインド独立審査結果を照合し、必要な箇所だけを修訂する。

原則：
- item_id / schema_version / scope / answer_number は維持する。
- high issue は必ず解消する。
- reviewer と正答が一致しなかった task は、単に reviewer に合わせて答えを変えず、資料・設問・選択肢を再検証して一意性を回復する。
- 問題が成立している箇所を無意味に全面書換えしない。
- 修訂後も Q4 Template の構造条件をすべて満たす。
- JSONのみを返す。

## Candidate Item (answer-aware)
{{ item_json }}

## Blind Review
{{ review_json }}
