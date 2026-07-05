# qiita-publish-with-approval

## Goal

Publish Qiita articles safely, with explicit user approval before any publish action.

## Mandatory Approval Gate

1. Before running any publish command, ask for explicit approval
2. Show:
   - Target article(s)
   - Visibility scope (public or private/limited)
   - Exact command to run
3. Do not execute until the user clearly approves
4. If approval is ambiguous, ask again
5. Never change article front matter `id`

## Covered Commands

- `npx qiita publish <article>`
- `npx qiita publish --all`
- `npx qiita push`
- Any workflow trigger that results in publishing

## Safe Procedure

1. Validate front matter (`title`, `tags`, `private`, `id`)
2. Run preview and final checks
3. Request approval with target/scope/command
4. Execute only after approval
5. Report execution result and affected articles
