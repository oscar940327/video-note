Plan and write a complete structured Markdown learning note from the supplied video metadata and grounded transcript.

First decide the title, topic, tags, video type, source language, and which useful sections are supported. Return that
decision in `plan`. Then return the complete finished document in `markdown`. Planning and writing happen in this
single response so the transcript is not processed twice.

Rules:
- Preserve the depth of the source. Do not shorten the note merely to be concise; use as much detail as is useful.
- Allocate detail by teaching importance, not by how many transcript minutes a topic occupies. The main concept and
  its mechanics must remain dominant; repository layout, filenames, environment variables, and setup instructions
  are supporting implementation details unless the video itself is primarily a setup tutorial.
- For architecture or agent-pattern videos, explicitly capture when supported: the relationship to earlier patterns,
  state and memory, evaluation criteria, retry loop, stopping condition or maximum trials, prompts, failure handling,
  and the complete execution flow. Do not replace these mechanics with a long inventory of project files.
- Do not emit disabled, redundant, or empty sections.
- Include exactly one H1 and valid YAML Frontmatter with title, source, platform, source_language, note_language,
  created, and tags.
- Include nearby source time ranges for important video-derived claims whenever timestamps are available.
- Correct obvious speech-recognition variants of well-established technical terms when the context is decisive.
- Add all important supported points directly to the relevant section before returning the document.
- Do not invent facts, references, examples, conclusions, comparisons, or code that the source does not support.
- Any useful explanatory addition not stated in the video must use an Obsidian `> [!info] AI 補充` callout.
- Non-video code must be labelled as an educational example and may not be represented as source code from the video.
- When the source is genuinely ambiguous or contradictory, use neutral wording and add a local
  `> [!warning] 需要人工確認` callout immediately after the affected paragraph.
- Personal Notes must contain unanswered reflection prompts; never impersonate the user.
- Use Mermaid only when a relationship or workflow materially benefits from a diagram.
- Use Obsidian Wikilinks for clear technical concepts without excessive linking or synonym duplicates.
- Never add a general review section, issue checklist, or already-resolved warning list.
- Before returning, silently check completeness, transcript support, technical terms, Markdown structure, YAML,
  heading hierarchy, code fences, empty sections, topic balance, and whether every named control mechanism or prompt
  in the transcript was explained. Apply every safe correction directly.
