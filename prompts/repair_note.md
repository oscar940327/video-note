Review and repair the supplied Markdown note against the transcript in one pass.

Apply every safe correction directly to the note:
- Fill an empty section only when the transcript supports useful content; otherwise remove the empty heading.
- Remove or conservatively rewrite unsupported and overstated claims.
- Correct obvious transcription-derived technical terms in the note when context is decisive.
- Add important missing transcript points to the most relevant existing section.
- Repair Markdown structure, YAML frontmatter, heading hierarchy, and unbalanced code fences.

Do not invent facts, examples, conclusions, or comparisons. Preserve the note's useful structure, language,
frontmatter, source URL, timestamps, and intentional user-authored wording whenever it remains supported.

When the transcript or video is genuinely ambiguous, contradictory, or impossible to resolve, keep the most
neutral supported wording and insert this callout immediately after the relevant paragraph, not at the top of the note:

> [!warning] 需要人工確認
> [timestamp when available] Concisely explain the exact ambiguity and the competing interpretations.

Do not use checkboxes. Do not list issues that you already fixed. Do not add a general review section. Return the
complete repaired Markdown document and nothing outside the schema.
