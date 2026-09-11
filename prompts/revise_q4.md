# TABITO 共通テスト中国語 Q4 修訂タスク v0.3

候補問題とブラインド独立審査結果を照合し、必要な箇所だけを修訂する。

**修訂時も2026本試験 + 2026追・再試験を同格のTier-1ブループリントとして維持する。** 初稿生成時だけ2026型で、修訂後に普通の読解問題へ戻ることを禁止する。

## 修訂原則

- `item_id` / `schema_version` / `scope` / answer_number は維持する。
- `workflow.blueprint_version` は `R8-2026-main-tsui-v2` とする。
- high issue は必ず解消する。
- reviewer と正答が一致しなかった task は、単に reviewer に合わせて key を変えない。資料・設問・選択肢・条件のどこに曖昧さがあるかを再検証し、一意性を回復する。
- 問題が成立している箇所を無意味に全面書換えしない。
- ただし、局所修正ではシナリオの情報依存関係が破綻する場合は、関連する資料と task をまとめて修訂する。
- A/Bの機能差を維持する。Bは再文脈化・適用・計画・ケース判断・総合理解等へ進み、単なるAの続きにしない。
- Bを無理に「実務行動」に固定しない。2026追試のような reflective synthesis も許容する。
- 資料数・資料タイプ数を満たすためだけの素材は削除する。
- A/Bそれぞれに少なくとも1つ、単純な一資料の語句一致を超える統合的 task を残す。
- `dependency_mode` が実際の evidence dependency と一致するよう修正する。
- `bundle_id` は説明文＋図、地図＋メモ＋システム図など、本当に一つの複合資料を構成する場合だけ使う。
- 2026本試・追試の surface reskin を避ける。レビュー修正の結果、公式問題の出来事の順序へ近づけない。
- 架空統計を実在機関の公式データのように見せない。
- JSONのみを返す。

## 2026 Blueprint

{{ blueprint_yaml }}

## 2026 Q4 Reference Patterns

{{ reference_patterns_yaml }}

## Q4 Template

{{ template_yaml }}

## Detailed Item-Writing Direction

{{ item_writing_direction }}

## Candidate Item (answer-aware)

{{ item_json }}

## Blind Review

{{ review_json }}
