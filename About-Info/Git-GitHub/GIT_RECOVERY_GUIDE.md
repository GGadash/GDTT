# Git Recovery Guide

Always start with `git status`, `git diff`, and `git log --oneline --decorate -n 20`.

## Changed but not committed

Inspect first. To discard one known file only when certain:

```powershell
git restore -- path/to/file
```

## Staged the wrong file

Keep the working edit but unstage it:

```powershell
git restore --staged -- path/to/file
```

## Bad local or published commit

Prefer a new inverse commit:

```powershell
git revert <commit-id>
```

## Inspect an older version

```powershell
git show <commit-id>:path/to/file
git diff <older-commit>..<newer-commit>
```

## Conflict

Read `git status`, resolve only marked files, test, then stage them. If abandoning an
uncommitted merge is safe, use `git merge --abort`.

## Wrong branch point or deleted branch

Create a corrected branch from an inspected commit and cherry-pick known coherent commits.
For a recently deleted local branch, inspect `git reflog` and recreate it from the verified
commit. Ask for help before rewriting history.

`git reset --hard`, force pushes, tag deletion, and broad restores are destructive and are
not part of the normal recovery workflow.
