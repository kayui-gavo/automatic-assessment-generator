# TABITO 共通テスト中国語 Q4 修訂タスク v0.5

候補問題とBlind Reviewを照合し、**必要な箇所だけを修訂して再びproduction qualityに戻す。**

## 修訂原則

1. `item_id` / `schema_version` / `scope` / `surface_family` / answer_number は維持する。
2. `workflow.blueprint_version` は `R8-2026-main-tsui-v4` とする。
3. high severity issue は必ず解消する。
4. reviewerとauthor keyが不一致なら、keyだけを都合よく変更しない。資料・設問・選択肢を再検討し、一意な問題へ直す。
5. ambiguityを消すために誤答を露骨に間違わせて難度を落とさない。修訂後もnear-missとshortcut resistanceを維持する。
6. cross-source issueを直す場合、一資料単独では候補が複数残り、資料を統合して初めて一意になる構造へ直す。資料を増やすだけでは解決としない。
7. 成立しているblockを理由なく全面書換えしない。ただしfamily scaffold自体が崩れている場合は関連blockをまとめて再構成する。
8. 中国語本文・数値・固有名詞・case・選択肢・具体的answer logicは原创を維持する。
9. 資料を細切れカード化せず、visualは本当に関係を表す場合だけ使う。
10. 修訂後にもう一度、正答一意性、single-source ablation、distractor競合、family surfaceを内部確認する。

詳細な公式reference sequenceは修訂モデルにも与えない。元candidateを2026実題へ近づけるための換皮ではなく、Production Profileの生成安全な範囲内でreview issueを直す。

規則が重なる場合は、Candidateの今回のidentityを除き、Production Profileをauthoritative contract、Output TemplateをJSON shapeとして扱う。

## Production Profile — authoritative contract

{{ generation_profile_yaml }}

## Output Template

{{ template_yaml }}

## Candidate Item — answer-aware

{{ item_json }}

## Blind Review

{{ review_json }}

## 出力

修訂後の完整JSONのみ。Markdown fenceや変更説明は禁止。
