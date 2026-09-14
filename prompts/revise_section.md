# TABITO 共通テスト中国語 Section Revision v0.5

以下の候補 section を、Blind Review の指摘だけを直すのではなく、2026 surface blueprint・原创性・命題難度を維持したまま修訂する。

## 修訂原則

- high/medium issue は具体的に解消する。
- 正答唯一性を最優先する。
- 問題の型・解答番号・section family を勝手に変えない。
- 一つの曖昧性を直すために別の曖昧性を作らない。
- 公式2026題への類似度を上げる方向の修訂は禁止。
- **修正によって問題を安易化しない。** 語彙を平易にしても、正答と誤答の競合、必要な情報範囲、句法判断、cross-source dependency 等の認知負荷は保つ。
- review に difficulty / shortcut / weak distractor の指摘がなくても、修訂後に新しいショートカットが生まれていないか必ず再点検する。
- Q5なら paragraph/anchor id を不用意に壊さない。
- Q2 ordering なら token_pool/correct_sequence/answer_positions の整合を保つ。
- 修訂後は完全な section JSON 全体を返す。差分だけ返さない。

## Section別 regression check

### Q1
- A/B の target_index と下線対象を壊さない。
- A/B/C の pinyin は内部 metadata のまま。学生面で見える前提に変えない。
- 語彙を単漢字中心の初級ドリルへ戻さない。
- D を一発話・一キーワードだけで解ける形へ単純化しない。

### Q2
- ordering を長い完成節4個の並べ替えへ戻さない。
- unused token を露骨な垃圾选项にしない。
- 曖昧性除去のために、正解だけが文法的に成立する簡単な pool へしない。

### Q3
- 誤答を正答から遠ざけて曖昧性を消す修正は禁止。
- 可能な限り near-miss を維持し、scope / aspect / modality / subject-object / causal relation 等の一点差で競合させる。
- 一語だけ見れば消せる誤答を新たに作らない。

### Q4
- cross_source の修正後も、本当に複数資料が必要か再確認する。
- visual material を説明文へ置換して認知操作を失わない。
- schema を通すためだけに資料・設問の関係を単純化しない。

### Q5
- 語彙問題を「3類義語＋1反義語」の送分へ戻さない。
- 後半3問の認知操作を同じ thesis の反復へ収束させない。
- anchor 修正後も、設問が必要とする根拠範囲を狭めすぎない。

## Final self-check

修訂後の各変更点について次を確認する。

1. issue は解消したか。
2. 正答唯一性は保たれたか。
3. 以前より短いショートカットで解けるようになっていないか。
4. distractor が正答から不必要に遠ざかっていないか。
5. blueprint の `quality_calibration` / `human_qa` 条件を引き続き満たすか。

## Section blueprint

{{ section_blueprint }}

## Current candidate

{{ item_json }}

## Review

{{ review_json }}

## Output schema

JSON Schema に完全適合する JSON だけを返す。Markdown fence、説明は禁止。

{{ json_schema }}
