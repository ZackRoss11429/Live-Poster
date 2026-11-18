# Conventions

## Branches

`type/reference/short-description`, e.g. `docs/issue3/adr-0001`.
Types: feat, fix, docs, test, refactor, chore, style. Only `/` and `-`.

Branch off `main`, merge back through a pull request, delete the branch after merging.

## Commits

Conventional Commits: `type: summary`, e.g. `feat: render date mini-app`.
Commit template: `git config commit.template .gitmessage`.

## Pull requests

Every change to `main` goes through a pull request using the template, even solo.

## Secrets

Never commit keys. The pre-commit hook (gitleaks) blocks them:
`pip install pre-commit && pre-commit install`.

## Decisions

Record decisions as ADRs in `docs/adr/`, copied from `0000-template.md`.
Don't edit accepted ADRs; supersede them with a new one.
