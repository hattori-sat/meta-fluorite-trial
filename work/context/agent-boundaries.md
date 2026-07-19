# Agent boundaries

## Principle

agentは専門性だけでなく、権限と成果物で分離する。同じfileを複数agentが同時編集しない。checkerは実装者と分ける。

| Agent | Reads | May change | Output | Must not do |
| --- | --- | --- | --- | --- |
| primary | dashboard、active ticket、必要context | active ticketで所有したfile | 統合判断、ユーザー報告 | 無ticketの非自明作業 |
| yocto-investigator | manifest、conf、layer、recipe、log | none | facts、仮説比較、最小案 | build、clean、編集 |
| build-runner | approved ticket、conf、cache/process | build outputのみ | progress、artifact、first error | recipe編集、cache削除 |
| log-analyzer | log、recipe、symbols | none | causal error、反証、追加証拠 | symptomだけでpatch提案 |
| target-validator | image、target log、validation plan | 承認されたtarget操作のみ | boot/graphics/input結果 | build設定編集 |
| pdca-checker | ticketと全linked evidence | none | PASS/FAIL/UNKNOWN gate | 実装、自己承認 |

## Handoff contract

handoffにはticket ID、問い、対象file/path、読み込むcontext、期待output、禁止事項を含める。subagentの回答はworking logまたはevidence indexへ要約し、会話contextだけに残さない。

Whoは個人名でなくroleとして記録する。接続user、IP、hostname、個人account、個人名を含む絶対pathをhandoffや成果物へ含めない。

## File ownership

書き込み作業を委任する場合は、ticketのDoへ所有fileを明記する。他agentの変更を戻さず、競合時はprimaryへ返す。
