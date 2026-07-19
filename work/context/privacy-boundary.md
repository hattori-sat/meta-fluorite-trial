# Privacy boundary

## Blocking rule

次の情報をGit管理対象へ含めない。検出時は作業を止め、値をreportへ再掲せずredactする。

- 氏名や個人を直接識別できる文字列
- 個人accountや個人profile URL
- IP address、個別hostname、SSH destination
- 個人名を含むabsolute home path
- email address、credential、token、SSH key

## Repository-safe identifiers

- `$PROJECT_ROOT`: canonical clone root
- `$AGL_ROOT`: build hostのAGL source root
- `$BUILD_HOST`: Git対象外の接続設定が指すhost role
- `$TARGET`: QEMUまたはRaspberry Pi target role
- `$LEGACY_ROOT`: 過去のsource/artifactを置くGit対象外の参照root
- `origin`: canonical Git remote

## Local-only configuration

接続情報は`.fluorite.local.env`などGit対象外のfile、またはprocess environmentで管理する。example fileを作る場合も実値を入れず、変数名と説明だけを記載する。

## Logging

working logにはrole、operation、result、evidence IDを記録する。raw commandに個人情報が含まれる場合、そのcommandをそのまま貼らず、安全なtemplateへ置換する。
