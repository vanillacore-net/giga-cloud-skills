# GitBook release workflow

## Recommended repository model

1. **Private authoring repository:** drafts, review notes, working contracts, and iteration history. Restricted to the production team.
2. **Release repository:** approved Markdown and assets only. It is the GitBook import source.
3. **Skills repository:** reusable, public-safe skills and validation tooling. It contains no chapter drafts or internal evidence.

Do not use a wiki as the security boundary. A wiki is useful for internal navigation only if the same collaborators may see its full revision history.

## Release sequence

1. Draft against a versioned chapter contract in the authoring repository.
2. Run the approved public-release control review and resolve all must-fix findings.
3. Human owner approves the release.
4. Export the approved state as Markdown, DOCX, or PDF.
5. Commit only approved Markdown and assets to the release repository, preferably as a clean release commit.
6. Import or sync that release repository into GitBook.

## Required release artefacts

- approved Markdown source
- source manifest with public-only citations
- asset manifest with accessibility text
- control-pass verdict
- release version and approver
