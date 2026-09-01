# Git and GitHub Guide

## Concepts in plain language

- A **repository** is the project plus its saved history.
- The **working tree** is the files currently being edited.
- **Staging** selects exact changes for the next snapshot.
- A **commit** is a named local snapshot.
- A **branch** is a movable line of development.
- A **merge** combines branches; a **pull request** proposes/reviews that combination.
- A **remote** is another repository, commonly on GitHub.
- A **tag** names a specific commit; a GitHub **release** adds notes and downloads to a tag.

## Local setup

```powershell
git --version
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git status
```

This repository is already initialized on `main`. Do not rerun `git init`. Review before
staging:

```powershell
git status
git diff
git add <intended-files>
git diff --staged
git commit -m "feat: describe one coherent change"
```

Codex does not commit by default.

## Normal feature workflow

1. Confirm the tree is clean and update `main` after a remote exists.
2. `git switch -c feature/short-name`
3. Make the smallest coherent change and run tests.
4. Review `git diff` and stage intended files only.
5. Commit with `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `perf:`, `build:`, `ci:`, or `chore:`.
6. `git push -u origin feature/short-name`
7. Open a pull request, review checks, merge, delete the merged remote branch, and pull `main`.

## GitHub Desktop

Add this existing local repository, inspect every changed file, enter a specific Summary,
and commit to the current branch. After a remote is approved, use Publish repository or
Push origin. Create/switch branches from the Current Branch menu, use Fetch/Pull before
work, and open a pull request for substantial changes.

## Publishing later

After implementation and release checks are complete, create an empty GitHub repository
without an auto-generated README/license. Then, only with owner approval:

```powershell
git remote add origin <repository-url>
git remote -v
git push -u origin main
```

Choose public/private deliberately. Add a clear description and topics, verify README
rendering, then configure `main` rules to prevent force pushes and eventually require
stable CI checks. Remote details or credentials must not be stored in source files.
