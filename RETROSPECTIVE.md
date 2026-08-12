# What 18 automated episodes taught us

Nitan Podcast began as a way to turn one week of USCardForum discussion into a short Chinese audio briefing. By August 11, 2026, the public feed contained 18 episodes: 16 weekly editions and two topic specials. The project has been useful less because every automation attempt succeeded than because the failures exposed the real contracts behind an automated podcast.

## What worked

- A six-minute show is long enough to explain several community stories and short enough to become a weekly habit.
- Source documents that establish what happened, evidence, caveats, and informative replies produce better audio than engagement statistics or a loose list of links.
- Category diversity prevents a high-engagement week from becoming seven versions of the same subject.
- Stable RSS, Apple Podcasts, Spotify, and a forum announcement thread give listeners several ways to follow the same show.
- Separating the reusable execution into [CastForge](https://github.com/lifan-builds/castforge) keeps the show repository opinionated without duplicating provider and publication code.

## Failures that changed the system

### Duration is an input-shape problem

NotebookLM did not reliably obey a written “six to eight minutes” instruction. In four launch experiments, the effective controls were its audio-length mode and the number of stories. The accepted weekly shape became `short` plus seven stories, which produced roughly six minutes.

### A valid MP3 is not automatically a valid podcast enclosure

GitHub Release assets were served as `application/octet-stream`; Apple Podcasts requires audio MIME metadata it can recognize. Moving public MP3s to GitHub Pages produced `audio/mpeg` and restored playback.

The first RSS implementation also emitted `enclosure length="0"` when the MP3 was not available locally during feed generation. Podcast players can reject that item even when the URL eventually works. RSS generation now refuses to publish without a positive byte length.

### Scheduling success is not publication success

The 30 most recent workflow runs at the August baseline were evenly split: 15 successful and 15 failed. Several failures happened after partial progress or during external validation. Three retry windows help, but only date-keyed idempotency and an atomic publication gate prevent partial public episodes.

W31 and W32 are the clearest example. Historical feed attempts referenced both weeks with zero-length enclosures, but no MP3 was committed, no release exists, and both public URLs return 404. W31 retained a source export; W32 did not retain a usable artifact. They are failed publication attempts, not missing episodes, and must not be restored without real audio.

### Provider state is production state

NotebookLM authentication is separate from an ordinary browser login, and uploaded temporary sources consume notebook capacity. CastForge now deletes its temporary source after success and after post-upload failures so a long-running show does not fill the notebook and stop future episodes.

## Listener feedback

The announcement thread produced concrete requests for transcripts, timestamps, more frequent episodes, and dedicated sub-forum coverage. The project initially prioritized Spotify distribution and better factual source material. The next show will use manifests, transcripts, and chapters from the start; those improvements can then return to Nitan without changing its public feed identity.

## What we would do first today

1. Define stable site, feed, GUID, and enclosure URL contracts before the first public episode.
2. Publish audio only after verifying its public status, MIME type, and byte length.
3. Preserve a machine-readable episode manifest with every citation.
4. Treat the LLM/audio provider as replaceable and keep credentials and editorial policy in the show repository.
5. Measure complete published episodes and external adopters, not workflow runs or GitHub stars alone.

## Next proof

[AI Builder Brief](https://github.com/lifan-builds/ai-builder-brief) will exercise the framework at daily cadence with English AI sources, NotebookLM dialogue, Cloudflare R2 audio, transparent manifests, and fail-closed publication. Its job is both to serve listeners and to prove that CastForge works outside the Nitan-specific forum pipeline.
