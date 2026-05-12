# Nitan Podcast

Nitan Podcast turns USCardForum discussions into short Chinese podcast episodes for listeners who want the week’s important forum context without reading every thread.

## Language

**Story Brief**:
A source-grounded mini-brief for one forum thread that establishes facts, stakes, representative replies, caveats, and only then a podcast angle.
_Avoid_: AI riff, title summary, hot-take segment

**Source Document**:
The NotebookLM-facing Markdown that carries canonical **Story Briefs** for an episode.
_Avoid_: raw dump, prompt-only guidance

**Category Voice Guide**:
A prescriptive editorial guide that defines how Nitan Podcast should handle each forum category.
_Avoid_: tone mimicry, weekly style scrape, forum cosplay

**Evidence From Source**:
Thread-specific facts, claims, numbers, dates, constraints, and replies that the podcast may rely on.
_Avoid_: inferred background, host guess, unsupported explanation

**Informative Reply**:
A forum response that adds facts, firsthand data points, corrections, constraints, or substantive interpretation.
_Avoid_: troll reply, pure joke, reaction-only comment, metadata

## Relationships

- An **Episode** contains one or more **Story Briefs**.
- A **Story Brief** is based on exactly one forum thread.
- A **Story Brief** treats commentary as secondary to factual setup.
- A **Story Brief** must establish **Evidence From Source** before interpreting community reaction.
- **Evidence From Source** prioritizes **Informative Replies** over usernames, likes, or low-information reactions.
- A **Source Document** owns the factual structure of each **Story Brief** before any audio style is applied.
- A **Category Voice Guide** informs **Story Briefs** without copying the forum's mood verbatim.

## Example Dialogue

> **Dev:** "Should the hosts open a thread segment with jokes from the replies?"
> **Domain expert:** "No. First make the **Story Brief** clear enough for someone who never opened the thread, then use replies for color and disagreement."

## Flagged Ambiguities

- "Review feedback" identified a conflict between factual digest and commentary-first entertainment; resolved: the default episode promise is source-grounded **Story Briefs** with light banter.
- Factual grounding belongs in the **Source Document**, not only in Gemini or NotebookLM prompting.
- Category tone is prescriptive: Nitan can inform the **Category Voice Guide**, but the show owns the editorial voice.
- The **Category Voice Guide** is a reviewed show artifact, not an environment-only prompt tweak.
- A **Source Document** includes the default voice once and injects only the relevant category note for each **Story Brief**.
- Reply handling should optimize for information density, not forum color: fetch deeper and filter out troll or reaction-only replies where possible.
- **Informative Replies** are identified with deterministic information-density signals before introducing an LLM classifier.
- **Informative Reply** filtering belongs in the Nitan extraction layer, before Gemini or NotebookLM sees the source.
