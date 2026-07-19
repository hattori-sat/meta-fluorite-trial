# Evidence index

巨大なimage、cache、full BitBake logはGitへ置かない。ここには次を保存する。

- artifactの絶対pathまたは保管場所
- SHA-256
- 作成日時とbuild identity
- manifestや短いlog excerpt
- 実行commandと対応ticket
- screenshot/videoのindex

秘密情報、SSH鍵、credentialは保存しない。外部pathが消える可能性がある場合は、その保持期間と代替取得方法を明記する。
