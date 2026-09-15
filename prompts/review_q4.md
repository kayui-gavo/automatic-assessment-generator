# TABITO 共通テスト中国語 Q4 ブラインド独立審査 v0.5

以下の候補を、**受験者として独立に解いた後、命題レビュアーとして審査する。**

標準解答、rationale、evidence locator、dependency label、生成者のquality note等は意図的に削除されている。見えていない作者側metadataを推測して補わず、学生に見える題面だけで判断すること。

## Candidate binding

以下は問題内容ではなく保存先と内容バージョンを識別する opaque binding である。解答の手掛かりとして使わず、出力 JSON に一字も変えず返すこと。

- `item_id`: `{{ item_id }}`
- `candidate_fingerprint`: `{{ candidate_fingerprint }}`

## 審査原則

1. まず全資料・設問・選択肢だけを使い、各taskを独立に解く。
2. 正答または正答集合が一意か確認する。
3. Production Profileをauthoritative contractとして、指定2026 familyのsurface、情報密度、task progressionが成立しているか確認する。
4. Reference Patternsは観察例として使い、例示された資料型を新しい必須条件へ膨張させない。
5. 最短shortcutを探す。一語、常識、選択肢の長さ、露骨な反義語、単一資料だけで解ける場合はissueにする。
6. 二つ以上の資料を使う必要があるように見えるtaskはsource ablationする。各資料を一つずつ隠したと仮定し、残りだけで正答が一意なら実質的統合ではない。
7. distractorが正答から離れすぎず、条件・範囲・主体・時点・因果等の局所差で競合しているか確認する。
8. visual / table / chart / flow が装飾ではなく答えに必要か確認する。
9. 中国語が自然な現代簡体字、日本語設問が簡潔な試験文体か確認する。
10. 公式題の本文・数値・case・判断ロジックのreskinになっていないか確認する。

## Verdict

- `pass`: 独立解答が一意で、family surface、難度、誤答競合、情報依存に重大な問題がない
- `revise`: 正答は成立するが、易しすぎる、shortcut、名目だけの複数資料統合、弱い誤答、worksheet化等がある
- `reject`: 複数解、正答不成立、重大な言語/資料矛盾、実質的な公式題コピー等

## Production Profile — authoritative contract

{{ generation_profile_yaml }}

## 2026 Reference Patterns

{{ reference_patterns_yaml }}

## Output Template reference

{{ template_yaml }}

## Blind Candidate

{{ item_json }}

## 出力

JSONのみ。Markdown fenceは禁止。

必須フィールド：
- schema_version: `"0.2"`
- item_id: 上の opaque binding をそのまま返す
- candidate_fingerprint: 上の opaque binding をそのまま返す
- verdict: `pass` / `revise` / `reject`
- independent_answers: `{task_id: [correct_option, ...]}`
- issues: severity, task_id(optional), category, description, suggested_fix
- overall_comment_ja
