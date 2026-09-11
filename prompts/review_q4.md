# TABITO 共通テスト中国語 Q4 独立审题

以下の候補問題を、**生成者とは独立した审题者**として检查してください。
目的は褒めることではなく、旅人教育の授業・模試で実際に使える品質かを判定することです。

重点检查：
- 正答は本当に一意か
- 問題文だけから正答根拠を説明できるか
- 誤答肢は自然で、かつ誤りの理由が明确か
- 複数資料を読む必要がある設問になっているか
- 中国語が自然か
- 日本語の設問表現が不自然でないか
- HSK型の単純知識問題に寄っていないか
- 既存共通テスト問題の「換皮」になっていないか
- 難易度ラベルが明らかに不適切でないか

出力は JSON のみ。

必須フィールド：
- item_id
- verdict: pass / revise / reject
- independent_answers: 各設問を独立に解いた正答番号
- issues: severity(high/medium/low), question_id(optional), category, description, suggested_fix
- overall_comment_ja

## Candidate Item

{{ item_json }}
