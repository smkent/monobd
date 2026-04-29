---
title: One time setup
icon: lucide/package-plus
---

# One time setup

These steps only need to be completed once after the project is first created.

## GitHub repository

[Settings → General][repo-settings]:

- [x] Allow merge commits
- [ ] Allow squash merging
- [ ] Allow rebase merging
- [x] Automatically delete head branches

[Settings → Branches][repo-settings-branches] → Add branch protection rule
for the Default branch (`main`):

- [x] Restrict deletions
- [x] Require a pull request before merging
- [x] Block force pushes

## Renovate

Ensure the [Renovate app][renovate] is installed on your account, then
enable it for `smkent/monobd`.

## GitHub Pages

[Settings → Pages][repo-settings-pages] → Source → GitHub Actions

[renovate]: https://github.com/apps/renovate
[repo-releases]: https://github.com/smkent/monobd/releases
[repo-settings]: https://github.com/smkent/monobd/settings
[repo-settings-branches]: https://github.com/smkent/monobd/settings/branches
[repo-settings-pages]: https://github.com/smkent/monobd/settings/pages
