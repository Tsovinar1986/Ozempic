#!/usr/bin/env bash
# Save this run's data and bring every copy of the data branch to the same, complete state.
#
# Usage: scripts/save_and_sync.sh <data checkout> <main repo> <copy repo>=<TOKEN_ENV_VAR>...
#   e.g. scripts/save_and_sync.sh data UitbreidenAI/drug-exp-api \
#          Tsovinar1986/Ozempic=GH_TOKEN adele-kha/uitbreiden_drug_experience=TEAM_REPO_TOKEN
#
# More than one collector writes the data branch (drug-exp-api runs its own), and a copy can
# also end up ahead of the main repository. A plain push then fails ("fetch first") and the
# run's work is lost. Instead, this script:
#   1. commits whatever this run collected (if anything);
#   2. fetches the data branch of the main repository and of every copy and merges each one
#      in. Day files are written at fixed paths, so the union of both sides is the complete
#      data; where both sides wrote the same day, this run's file is kept. The checkpoint takes,
#      per stream, the later of the two dates, and the export CSV and data README are rebuilt;
#   3. pushes the result to the main repository, then to every copy. Because the result
#      contains every copy's history, each push is a fast-forward: nothing is ever forced.
# It runs even when nothing new was collected, so a copy that fell behind or diverged is
# brought up to date. If another collector pushes in between, it retries from step 2.
#
# The main repository is reached with the auth already stored in the checkout's git config;
# copies use the token in the named environment variable. GIT_BASE (default
# https://github.com) is the URL prefix, overridable for tests.
set -uo pipefail

data=$1 main=$2
shift 2
base=${GIT_BASE:-https://github.com}
branch=${DATA_BRANCH:-data}
code_dir=$(cd "$(dirname "$0")/.." && pwd)
gha() { [ -n "${GITHUB_ACTIONS:-}" ] && echo "::$1::$2" || echo "$1: $2" >&2; }

cd "$data" || { gha error "No data checkout at $data; nothing to save or sync"; exit 1; }
g() {
  git -c user.name="github-actions[bot]" \
      -c user.email="41898237+github-actions[bot]@users.noreply.github.com" "$@"
}
oldest() { jq -r '[.[]] | min // "partial day"' state/checkpoint.json 2>/dev/null || echo "partial day"; }

# git with the token from env var $2 for repository $1 (empty header first drops stored auth).
with_token() {
  local repo=$1 var=$2; shift 2
  local token auth
  token=$(printf %s "${!var:-}" | tr -d '[:space:]')
  auth=$(printf 'x-access-token:%s' "$token" | base64 | tr -d '\n')
  [ -n "${GITHUB_ACTIONS:-}" ] && echo "::add-mask::$auth"
  g -c http.https://github.com/.extraheader= \
    -c http.https://github.com/.extraheader="AUTHORIZATION: basic $auth" "$@"
}

rebuild_outputs() {
  ( cd "$code_dir" &&
    python3 scripts/extract_ozempic_comments.py --input "$OLDPWD/curated/comments" \
      --output "$OLDPWD/exports/ozempic_100k_comments.csv" &&
    python3 scripts/write_data_readme.py --data "$OLDPWD" ) >/dev/null
}

# Merge ref $1 (named $2 in messages) into HEAD. Returns 0 if HEAD changed.
merge_in() {
  local ref=$1 name=$2 ours theirs
  git merge-base --is-ancestor "$ref" HEAD 2>/dev/null && return 1
  ours=$(git show HEAD:state/checkpoint.json 2>/dev/null || echo '{}')
  theirs=$(git show "$ref":state/checkpoint.json 2>/dev/null || echo '{}')
  echo "Merging data from $name"
  if ! g merge --quiet --no-edit --allow-unrelated-histories -X ours \
         -m "Merge data from $name" "$ref"; then
    # Conflicts -X ours can't settle (e.g. a file deleted on one side): keep this side's.
    git diff --name-only --diff-filter=U | while IFS= read -r f; do
      git checkout --ours -- "$f" 2>/dev/null || git rm --quiet -- "$f"
    done
    git add -A && g commit --quiet --no-edit || return 1
  fi
  # Every day before the later checkpoint was collected by one side or the other.
  printf '%s\n%s\n' "$ours" "$theirs" | jq -s \
    '[.[] | to_entries[]] | group_by(.key) | map({key: .[0].key, value: (map(.value) | max)}) | from_entries' \
    > state/checkpoint.json.tmp && mv state/checkpoint.json.tmp state/checkpoint.json
  return 0
}

# 1. This run's own data.
git add -A
if git diff --cached --quiet; then
  echo "No new data from this run"
else
  # Report the stream furthest behind, so the message doesn't overstate progress.
  g commit --quiet -m "Collect data (oldest next day: $(oldest))"
fi

# Merge needs history to find a common ancestor; the checkout is shallow.
if [ "$(git rev-parse --is-shallow-repository)" = true ]; then
  git fetch --quiet --unshallow origin "$branch" || { gha error "could not fetch $main history"; exit 1; }
fi

failed=0
for attempt in 1 2 3; do
  # 2. Fetch every copy and merge in whatever this checkout doesn't have yet.
  merged=0
  if git fetch --quiet origin "+refs/heads/$branch:refs/remotes/origin/$branch"; then
    merge_in "origin/$branch" "$main" && merged=1
  else
    gha warning "could not fetch $main"
  fi
  for spec in "$@"; do
    repo=${spec%%=*} var=${spec#*=}
    if with_token "$repo" "$var" fetch --quiet "$base/$repo.git" \
         "+refs/heads/$branch:refs/remotes/copy/$repo"; then
      merge_in "copy/$repo" "$repo" && merged=1
    else
      echo "could not fetch $repo (no $branch branch yet, or no access); pushing to it anyway"
    fi
  done
  if [ $merged = 1 ]; then
    rebuild_outputs || gha warning "could not rebuild export/README after merging"
    git add -A
    git diff --cached --quiet || g commit --quiet -m "Combine collected data (oldest next day: $(oldest))"
  fi

  # 3. Push: main repository first (source of truth), then each copy.
  if ! git push --quiet origin "HEAD:refs/heads/$branch"; then
    echo "$main changed during this run; merging again (attempt $attempt)"
    continue
  fi
  echo "Saved to $main (oldest next day: $(oldest))"
  failed=0
  for spec in "$@"; do
    repo=${spec%%=*} var=${spec#*=}
    if with_token "$repo" "$var" push --quiet "$base/$repo.git" "HEAD:refs/heads/$branch"; then
      echo "Synced $branch to $repo"
    else
      gha error "sync to $repo failed"
      failed=1
    fi
  done
  exit $failed
done
gha error "could not save to $main after 3 attempts"
exit 1
