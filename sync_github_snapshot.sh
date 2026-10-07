#!/bin/bash
# 将内容层同步到 GitHub（origin/main）。音频制作工具链/凭据/生产产物永不上 GitHub。
# 用法：bash sync_github_snapshot.sh "本次同步说明"
set -e
msg="${1:-snapshot: sync content layer}"
git fetch origin -q
git checkout -q github-snapshot
# 用 master 的内容层整体替换快照分支（保留 podcasts 下非产物文件；排除 output*/校验json）
git rm -r --cached . -q
git add README.md AGENTS.md logo.png .gitignore -- podcasts \
  ':(exclude)podcasts/**/output*' \
  ':(exclude)podcasts/**/shownotes_v2.html.b64chunks.json' \
  ':(exclude)podcasts/**/shownotes_v2.html.meta.json'
git diff --cached --quiet && { echo "无变化，无需同步"; git checkout -q master; exit 0; }
git commit -q -m "$msg"
git push origin github-snapshot:main
git checkout -q master
echo "已同步到 origin/main"
