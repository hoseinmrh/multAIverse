# GitHub repository setup

The repository itself is ready to push. These owner-only GitHub settings cannot
be stored completely in source control and should be reviewed after the first
push.

## First push

```bash
git add .
git commit -m "chore: prepare repository for contributors"
git push origin main
```

Do not use `git add` until `git status` confirms that `.env`, local databases,
dependency directories, and build output are absent.

## Repository details

In **Settings > General** and the repository **About** panel:

- Use a short description such as “A local-first fictional alternate-life
  simulation game.”
- Add topics such as `nextjs`, `fastapi`, `typescript`, `python`, `sqlite`,
  `simulation`, and `local-first`.
- Decide and add a license. Do not label the project open source until an
  explicit license is committed.
- Keep Issues enabled if you want to use the included issue forms.

## Actions and branch rules

1. Open the first **CI** run and confirm both `Backend` and `Frontend` jobs pass.
2. Create a ruleset for `main` under **Settings > Rules > Rulesets**.
3. Require pull requests and the two CI status checks before merge.
4. Block force pushes and branch deletion for `main`.
5. Optionally require approval and conversation resolution when additional
   maintainers begin reviewing changes.

Do not require a check until it has completed once; GitHub cannot select a
status check that the repository has never reported.

## Security settings

Under **Settings > Security** or **Security > Security overview**:

- Enable the dependency graph, Dependabot alerts, and Dependabot security
  updates.
- Enable private vulnerability reporting so the link in `SECURITY.md` and the
  issue chooser works for outside reporters.
- Review, rather than blindly merge, Dependabot version-update pull requests;
  CI verifies compatibility but does not replace code review.

No repository secret is required for the default CI workflow. Do not add an
OpenAI key to CI: all automated narrative tests use mocks, and the public
repository should remain verifiable without external model calls.

## Release check

Before tagging a release, verify that:

- CI is green on the exact commit.
- `docs/PROGRESS.md` accurately states known limitations.
- migration and clean-seed workflows pass.
- the chosen license and any attribution files are present.
- no `.env`, SQLite database, real profile data, API key, local build output, or
  package cache is tracked.
