Independently compare the generated note against the transcript. Find only meaningful factual, completeness, or
transcription-derived problems. A faithful paraphrase does not need verbatim support. Do not critique style preferences.

Return three kinds of actionable results:

1. `safe_edits`: small, decisive corrections. `find` must be the shortest exact unique text copied from the note.
   `replace` must be ready to insert and preserve the note's language, detail, Markdown, timestamps, and callouts.
2. `ambiguities`: only genuinely unresolved source contradictions. `anchor` must be exact unique note text. The message
   explains what a human should verify. Do not report issues that can be safely corrected.
3. `critical_sections`: only major omissions or materially wrong explanations that require rewriting an entire section.
   `heading` must exactly match an existing Markdown heading without `#`. Include concise transcript evidence.

Prefer a safe edit over a critical rewrite. Return at most three critical sections. Do not return Markdown formatting
issues that Python can determine, including YAML presence, heading levels, empty headings, duplicate headings, code
fences, or Mermaid fences. Do not return supported claims or a long review report. Never rewrite the whole document.
