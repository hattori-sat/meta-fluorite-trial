# Work system

このdirectoryは人間向け完成文書ではなく、AIと人間が問題解決を継続するための作業記録です。

## Separation of context

| Directory | Stores | Must not store |
| --- | --- | --- |
| `tickets/` | problem、target、scope、PDCA、acceptance criteria | 巨大log、一般説明 |
| `context/` | 再利用する事実、環境、制約、既知状態 | 時系列の作業日記 |
| `logs/` | 実行したcommand、観測、時刻、次の一手 | 後付けの美化された説明 |
| `decisions/` | 選択肢、採用理由、trade-off | 生log |
| `evidence/` | manifest、hash、短いlog抜粋へのindex | image、cache、巨大log本体 |

## Flow

1. 気づきを`TASKS.md`のInboxへ置く。
2. 作業の目的と、目的達成を判定する指標を確認する。
3. What / Where / When / Who(role) / Howで現象を層別する。Whyはこの段階へ混ぜない。
4. 影響、頻度、再現性、downstream阻害、riskから重点を1つ選ぶ。
5. 重点対象のprocessを入力から出力まで解析し、正常との差が生じる問題点を特定する。
6. 問題点を説明できる原因仮説を比較し、反証可能な方法で真因を確認する。
7. 真因に対する最小対策をPlanへ置き、最重要ticketだけをIn Progressにする。
8. Doのcommandと結果を日別working logへ追記する。
9. Checkで期待値と実測値を比較する。
10. PDCA checkerが証拠、scope、privacyを監査する。
11. Actで標準化、追加ticket、rollback、終了を決める。

## Priority rule

優先度はおおむね`再現性の阻害 × downstream影響 × 不確実性 ÷ 変更risk`で考える。ただし安全・data loss・秘密情報のriskは常に最優先する。

## Privacy blocker

氏名、個人account、IP address、hostname、個人名を含む絶対path、credentialをrepositoryへ保存しない。検出した場合はticketの進行を止め、値を回答やlogへ再掲せずrole名へ置換する。接続情報はGit対象外の`.fluorite.local.env`等で管理する。
