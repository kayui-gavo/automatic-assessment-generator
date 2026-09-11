# TABITO 共通テスト中国語 Q4 ブラインド独立審査 v0.2.1

以下は旅人教育の候補問題である。**標準解答・根拠・生成者の自己評価は意図的に削除されている。**
生成者の答えを推測せず、受験者として各 task を独立に解いた後、命題者として品質を審査すること。

## 基準の優先順位

- 2026 本試験と2026 追・再試験を同格の第一級ブループリントとする。
- 両者の共通特徴を核とし、両者の違いは許容される変化幅とみなす。
- 2025以前は補助的な歴史資料であり、2026型の構造を上書きする根拠にしない。
- 2026本試または追試の固有シナリオ・資料順を換皮しただけの問題は減点する。

## 審査順序

1. まず全資料と設問だけを読み、各 task の答えを独立に決める。
2. 次に、答えが一意か、資料だけで根拠を確定できるかを確認する。
3. 最後に、2026型共通テストQ4としての状況進行・資料統合性・言語自然さ・誤答肢品質・難度を評価する。

重点項目：
- A/Bの状況進行が自然で、Bで情報の使い方が実際的な判断へ変わっているか
- 資料が実際に解答に必要か
- 単語一致だけで解ける task が多すぎないか
- 複数資料を統合する task が十分か
- 単純理解→比較/データ読解→統合→適用と認知操作が深まっているか
- multi_select / multi_slot の正答集合が一意か
- 数量資料が不必要な数学計算になっていないか
- 中国語が自然な現代語か
- 日本語の設問が大学入試として自然か
- distractor が雑ではないか（ただし生成者の rationale は見えていない）
- 2026本試・追試のどちらかの表面換皮になっていないか
- 旧年度の典型構成へ逆戻りしていないか
- scope=full なら60点大問として情報量・変化・作業量が薄すぎないか

## 2026 Item-Writing Direction

{{ direction_md }}

出力は JSON のみ。

必須フィールド：
- schema_version: "0.2"
- item_id
- verdict: pass / revise / reject
- independent_answers: {task_id: [correct_option, ...]}
  - multi_select は選択順を問わない
  - multi_slot_choice は answer_slots の順序に対応させる
- issues: severity(high/medium/low), task_id(optional), category, description, suggested_fix
- overall_comment_ja

## Blind Candidate

{{ item_json }}
