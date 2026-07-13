Compare the note against the supplied transcript. Identify important supported claims, unsupported or overstated
claims, missing key points, and likely transcription errors. Be conservative: lack of verbatim wording does not
make a faithful paraphrase unsupported. The score is a quality hint, not a guarantee. Do not introduce new facts.

Make every review item actionable inside the Markdown note:
- For each unsupported claim, include the note section heading, the shortest exact note excerpt that can be searched,
  and a concise reason. Format: `〈section〉「exact note excerpt」— reason`.
- For each possible transcription error, include the nearest transcript timestamp, an exact transcript excerpt, and
  a concise reason. Format: `[HH:MM:SS] "exact transcript excerpt" — reason`.
- For each missing key point, include the transcript timestamp and a concise description of what is missing.
- Return an empty array when a category has no issue. Do not use vague items such as "check this section".
