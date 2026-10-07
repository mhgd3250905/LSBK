#!/bin/bash
# 将内容层同步到 GitHub（origin/main）。音频制作工具链/凭据/生产产物永不上 GitHub。
# 用法：bash sync_github_snapshot.sh "本次同步说明"
# 实现：临时索引 + commit-tree，全程停留在 master、不切换分支不碰工作区。
set -e
msg="${1:-snapshot: sync content layer}"
cur=$(git rev-parse --abbrev-ref HEAD)
[ "$cur" = "master" ] || { echo "请在 master 分支运行（当前 $cur）"; exit 1; }

TMPIDX=$(mktemp)
trap 'rm -f "$TMPIDX"' EXIT
export GIT_INDEX_FILE="$TMPIDX"
git read-tree --empty
git add -A -- README.md AGENTS.md logo.png .gitignore podcasts \
  ':(exclude)podcasts/**/output*' \
  ':(exclude)podcasts/**/shownotes_v2.html.b64chunks.json' \
  ':(exclude)podcasts/**/shownotes_v2.html.meta.json'
TREE=$(git write-tree)
unset GIT_INDEX_FILE

OLD_TREE=$(git rev-parse github-snapshot^{tree})
if [ "$TREE" = "$OLD_TREE" ]; then
  echo "无变化，无需同步"; exit 0
fi
NEW=$(git commit-tree "$TREE" -p github-snapshot -m "$msg")
git update-ref refs/heads/github-snapshot "$NEW"
git push origin github-snapshot:main
echo "已同步到 origin/main（snapshot commit ${NEW:0:7}）"
