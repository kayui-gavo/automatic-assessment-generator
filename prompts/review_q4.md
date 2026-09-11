# TABITO 共通テスト中国語 Q4 ブラインド独立審査 v0.2

以下は旅人教育の候補問題である。**標準解答・根拠・生成者の自己評価は意図的に削除されている。**
生成者の答えを推測せず、受験者として各 task を独立に解いた後、命題者として品質を審査すること。

## 審査順序

1. まず全資料と設問だけを読み、各 task の答えを独立に決める。
2. 次に、答えが一意か、資料だけで根拠を確定できるかを確認する。
3. 最後に、共通テストQ4としての資料統合性・言語自然さ・誤答肢品質・難度を評価する。

重点項目：
- A/Bの状況進行が自然か
- 資料が実際に解答に必要か
- 単語一致だけで解ける task が多すぎないか
- 複数資料を統合する task が十分か
- multi_select / multi_slot の正答集合が一意か
- 中国語が自然な現代語か
- 日本語の設問が大学入試として自然か
- distractor が雑ではないか（ただし生成者の rationale は見えていない）
- 最近の公式問題の換皮になっていないか
- scope=full なら60点大問として情報量・変化・作業量が薄すぎないか

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
