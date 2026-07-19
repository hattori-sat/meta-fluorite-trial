# Evidence and handoff contract

## Purpose

専門agentとMCPが大量source/logをprimary contextへ流さず、domainの意味を保ったまま検証可能なfactsを受け渡すためのcontractを定める。これはdomain modelを共通化するschemaではない。

## Assignment contract

primary roleはsubagentへ最低限次を渡す。

| Field | Requirement |
| --- | --- |
| `ticket_id` | active ticket。ticketなしの非自明な作業を依頼しない。 |
| `question` | 一つの判定可能な問い。原因探索全体を丸投げしない。 |
| `source_context` | 問いの言葉を定義するbounded context。 |
| `target_role` | agent名またはresponsibility role。個人名を使わない。 |
| `scope` | 読んでよいrevision、path、evidence ID、target role。 |
| `required_inputs` | ticket、Domain README、既存evidence、acceptance criteria。 |
| `expected_output` | facts、unknowns、仮説比較、必要なdomain payload。 |
| `prohibited_actions` | edit、build、sync、target mutationなど依頼ごとの禁止事項。 |
| `output_budget` | excerpt/log件数、最大range、summary粒度。 |

別contextの問いが混ざる場合はassignmentを分ける。agentは隣接contextを推測で埋めず、`HANDOFF_NEEDED`と必要なcontext、問い、input contractを返す。

## Result contract

agentは次の順に短く返す。

1. `status`: `ANSWERED`、`PARTIAL`、`UNKNOWN`、`BLOCKED`、`HANDOFF_NEEDED`
2. `facts`: evidence IDまたはrepository-safe path/lineに紐づく観測
3. `inferences`: factsから導いたが直接観測ではない内容
4. `hypotheses`: 非自明な問題では最低2案、各案の反証条件
5. `unknowns`: まだ答えられない点と不足input
6. `domain_payload`: source context固有の用語で表した結果
7. `risks`: build-time、runtime、packaging、integration、privacyへの影響
8. `smallest_next_action`: 追加で必要な最小queryまたはhandoff

Read-only agentの`changes`は常に`none`である。Execution roleは別途`run_id`、approval class、actual side effectsを返す。

## Evidence envelope

すべてのMCPで共有してよいのは、次のtransport metadataだけである。

```text
EvidenceEnvelope
  schema
  bounded_context
  operation
  subject_id
  revision_or_image_id
  identity_status
  observed_at
  payload
  unknowns[]
  evidence_ids[]
  truncated
  warnings[]
  next_queries[]
  redaction_policy
  explainability
```

Rules:

- `bounded_context`は[Domain registry](../../domains/README.md)のIDに限定する。
- `payload`はcontext固有の観測shapeであり、原因推論を混ぜない。
- `revision_or_image_id`なしのsource/runtime evidenceは`identity_status=insufficient`と`unknowns`で明示する。
- configured identityはrole-local assertionであり、MCPがrootのGit HEADやartifact hashを自動検証したことを意味しない。
- 複数rootを持つcontextは、全rootのrevisionを固定するmanifest/combined digestを一つの`revision_or_image_id`として設定する。root集合が変わればidentityも変える。
- evidence IDはsubject、revision/image identity、redacted payloadから生成し、identityが変われば同じ観測でも別IDにする。
- raw source/logはdefault responseへ含めず、同じsubject/revision、tool、repository-safe root/path、rangeをlocatorとしてbounded readを再実行する。
- `evidence_ids`はresponse/auditのcorrelation IDであり、server再起動後に単独でdereferenceできる永続storage keyではない。durable ticketへIDだけを保存せず、identityとquery locatorも保存する。
- `truncated`がtrueなら切捨て位置と安全なnext queryを返す。
- domain固有fieldは`payload`へ置き、envelopeへ追加しない。

`explainability` is transport metadata and has this bounded shape:

```text
explainability
  classification: bounded_observation
  basis_evidence_ids[]
  causal_claims[]
  limitations[]
  next_actions[]
```

The kernel derives this block from the evidence ID, unknowns, warnings and
bounded next queries. An empty `causal_claims` list is intentional: a source or
runtime observation is not a root-cause conclusion. Agents still provide
facts, inferences and hypotheses in their handoff contract.

## Context isolation

- primary roleはactive ticket、decision、summaryを保持し、raw log/source調査を専門agentへ渡す。
- investigatorは自contextのREADME、依頼されたticket、直接必要なevidenceだけを読む。
- 同じ問いへ複数agentを使う場合も、write ownershipは重複させない。
- subagentの結論は会話だけに残さず、primary roleがticket、working log、またはevidence indexへ要約する。
- cross-context causalityは各contextのfactsが揃った後にprimary roleが比較し、PDCA checkerが根拠を監査する。

## Privacy and authority

- Git管理対象、handoff、evidenceには個人名、個人account、IP address、hostname、個人名を含むabsolute path、email、credentialを含めない。
- 接続先は`$BUILD_HOST`、sourceは`$AGL_ROOT`、targetは`$TARGET`のrole IDで表す。
- redactionした値をerror messageやchecker reportへ再掲しない。
- 任意shell文字列をMCP inputにしない。state-changing actionは[Execution context](../../domains/execution/README.md)のregistered runbookとapprovalを経由する。
