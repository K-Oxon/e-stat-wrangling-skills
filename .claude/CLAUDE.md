# CLAUDE

このリポジトリのWhyとWhat:
私には機械判読性が最悪なe-Statとの戦いによって得た細かいノウハウがある。またOpus 4.7をはじめとして、紙Excelと揶揄されるような帳票（従来は泣きながらcsvに転記してたもの）もかなりの精度でLLMによって情報解釈・再構築が可能になりつつある。これらを融合し、LLMのskillsとして誰でも魔境のe-Statから統計表を構造的に取得できるようにしたい。

## Usage of codex cli

planningを作成した時、実装タスクの固まりがひと段落した時、ユーザーに指示された時はcodex cliにレビューをもらい自分以外の視点での指摘を検討すること。

```
codex exec --model gpt-5.4  "review this plan [full path planning.md]"

# 一度レビューなどを依頼し、再依頼する場合は、resumeを使って会話履歴を引き継いで投げる
codex exec --model gpt-5.4 --resume "I have addressed your previous comments. Could you please review it again?"
```

## git関連

### git

commit message: Semantic Commit Messagesとする

branch: version 1.0まではmainで開発 それ以降はgithub flow
