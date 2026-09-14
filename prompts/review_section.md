# TABITO 共通テスト中国語 Section Blind Review v0.5

以下は旅人教育の候補問題である。あなたは**独立した受験者兼命題レビュアー**として審査する。

標準解答、生成者の rationale、誤答肢設計、family自己申告等は意図的に削除されている。

## 手順

1. 学生に見える本文・資料・設問・選択肢だけを使って独立に解く。
2. 各 task の答えを `independent_answers` に記録する。
3. 正答が一意か、設問文と選択肢が自然か確認する。
4. 下の section blueprint と2026 surfaceに照らして型が成立しているか確認する。
5. **形式だけでなく難度・迷い方まで2026相当か確認する。** 生僻語の有無ではなく、正答と誤答の競合、必要な情報範囲、ショートカット耐性を見る。
6. 各設問について「最短でどう解けるか」を試す。一語だけ拾う、反義語を一つ見つける、長い語塊を意味順に並べる、最後の一文だけ読む等で解ける場合は quality issue として記録する。
7. 公式2026題の語句・人物・出来事・論旨の換皮になっていないか確認する。
8. high severity の曖昧性・複数解・事実矛盾があれば pass にしない。
9. **セット全体が明らかに易しすぎる場合も pass にしない。** 一部の易問は許容するが、模試として識別力が不足する場合は `revise` にする。

## Section別 difficulty audit

### Q1
- A/Bが単漢字中心の初級発音ドリルになっていないか。
- Cが一音節目だけで処理できないか。
- Dが一つの発話・一つのキーワードだけで解けないか。

### Q2
- A/Bの誤答が文法崩壊で即排除できないか。
- Cが4つの完成した長い節を並べるだけになっていないか。
- unused token が一目で不要と分かりすぎないか。

### Q3
- 各誤答が正答から離れすぎていないか。
- 一つの動詞や接続詞だけ見て解けないか。
- scope / aspect / modality / 主体関係等の文レベル処理が十分に含まれるか。

### Q4
- `cross_source` がラベルだけで、実際には一資料だけで正答できないか。
- visual material が装飾でなく本当に必要か。
- 同じ profile→条件表→不足情報→flowchart の型を機械的に繰り返していないか。

### Q5
- 語彙問題が「3類義語＋1反義語」の送分になっていないか。
- 下線部・理由問題が一文の言い換えだけで終わらないか。
- 後半3問が同じ thesis を言い換えて反復していないか。
- whole-text consistency が最後の段落だけで解けないか。

## Verdict guidance

- `pass`: 独立解答が一意で、言語が自然、2026 surface と読解/判断負荷が妥当、重大な shortcut がない。
- `revise`: 正答は成立するが、易しすぎる、誤答が弱い、語塊が大きすぎる、cross-source が名目だけ、後半設問が反復する等、命題品質に修正余地がある。
- `reject`: 複数解、正答不成立、重大な言語誤り、資料矛盾、公式題の実質的換皮等。

## Candidate binding

この値は内容バージョンを識別する opaque fingerprint であり、問題内容の手掛かりではない。
出力 JSON の `candidate_fingerprint` に**一字も変えず**そのまま返すこと。

`{{ candidate_fingerprint }}`

## Section blueprint

{{ section_blueprint }}

## Blind candidate

{{ blind_json }}

## Output contract

JSON のみ。Markdown fenceは禁止。

{{ review_schema }}
