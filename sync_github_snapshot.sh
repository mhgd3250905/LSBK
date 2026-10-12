#!/bin/bash
# 将项目内容同步到 GitHub（origin/main）。
# 2026-10-12 起范围放宽（用户指令"都可以放上去，除了音频"）：除音频媒体与合成中间产物外
# 全部上 GitHub（含根目录生产工具链脚本、.agents、agent、analysis、doubao_sdk_ref、transcripts 等）。
# 凭据（豆包api.txt/*token*/*secret* 等）与音频（*.mp3/*.m4a/*.wav）由 .gitignore 永久拦截；
# podcasts/**/output*（音频成品+合成中间产物）不上。
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
git add -A \
  ':(exclude)podcasts/**/output*' \
  ':(exclude)podcasts/**/shownotes_v2.html.b64chunks.json'
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
