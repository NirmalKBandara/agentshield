# Git and GitHub workflow

AgentShield uses GitHub Flow: `main` remains releasable and all changes arrive
through short-lived pull-request branches. A permanent `develop` branch is not
needed until the project adopts scheduled releases with a separate integration
phase.

## Branch naming

- `feat/<topic>` — new product or platform work
- `fix/<topic>` — bug fixes
- `docs/<topic>` — documentation-only changes
- `chore/<topic>` — maintenance and tooling

## Start work

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/my-change
```

## Review and publish work

```bash
git status
git add <specific-files>
git commit -m "feat(scope): concise description"
git push -u origin feat/my-change
gh pr create --base main --head feat/my-change --fill
```

Wait for CI and review, then squash-merge the PR in GitHub. Update locally:

```bash
git switch main
git pull --ff-only origin main
git branch -d feat/my-change
```

## Recommended branch protection

After the first CI run succeeds, configure a `main` ruleset in GitHub:

1. Require pull requests before merging.
2. Require one approval.
3. Require the `backend`, `frontend`, and `compose` CI jobs.
4. Require branches to be up to date before merging.
5. Block force pushes and branch deletion.

Repository administrators can configure this under **Settings → Rules →
Rulesets**. Keep the initial setup unblocked until the workflow exists on
`main`.
