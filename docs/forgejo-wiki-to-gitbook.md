# Private Forgejo wiki to GitBook workflow

## Position

Use a **private Forgejo wiki** as the editorial surface for chapter drafts. This is a sensible choice when VanillaCore controls access: reviewers can read the material in its intended page structure, judge actual length, and comment on flow without exchanging large Word files.

The wiki is not public and does not need to be. Its history is available only to people who can access the wiki. Treat that access list as the control boundary.

## Workflow

1. Keep the chapter repository and its wiki private to the production and review group.
2. Use the wiki for readable draft pages, review checkpoints, and approved editorial structure.
3. Keep raw source research and restricted meeting material outside the wiki unless every wiki collaborator is authorised for it.
4. Mark a wiki revision as the candidate release after the internal control pass and human approval.
5. Export that approved state to Markdown, DOCX, or PDF.
6. Commit only the approved export and release assets to the GitBook import repository.
7. Import or sync the release repository into GitBook.

## Recommended repositories

- **Chapter repository + private wiki:** working drafts and controlled review.
- **`cloud-skills`:** agent integration plugin, with no chapter drafts or internal evidence.
- **GitBook release repository:** approved final Markdown and assets only.

## Review rule

No wiki page is a release merely because it is readable. The exported version must carry a human approval record and pass the release checks defined by the Chapter 1 production process.
