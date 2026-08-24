# CastForge Integration

Nitan Podcast uses `CastForge` for reusable pipeline stages while retaining ownership of the public show and its publication workflow. The migration is complete; this document records the current boundary so future changes do not recreate local compatibility layers.

## Repository roles

### `castforge`

CastForge owns reusable source-to-export orchestration, briefing and export stages, NotebookLM integration, and framework contracts. Provider SDK imports remain lazy so offline extraction and validation do not require optional integrations.

### `nitan-podcast`

Nitan owns:

- Nitan MCP extraction and thread-selection behavior;
- prompts, category voice, editorial rules, and forum templates;
- podcast metadata, RSS identity, and public compatibility tests;
- the weekly schedule, self-hosted runner configuration, workflow gates, and publication;
- `docs/feed.xml`, `docs/episodes/*.mp3`, and show assets.

## Runtime dependency

`requirements.txt` is the single operational owner of CastForge. It installs the existing `v0.1.3` release tag:

```text
castforge @ git+https://github.com/lifan-builds/castforge.git@v0.1.3
```

The workflow creates or reuses the repository virtual environment and installs that requirements file once. It must not install another CastForge revision separately. NotebookLM browser dependencies remain optional and are installed from `requirements-integrations.txt` when the audio phase is enabled.

## Canonical module boundary

`run_pipeline.py` is a thin show-specific composition layer. It imports `PipelineHooks` and `main` from `castforge.pipeline`; tests and any direct callers import reusable stages from their canonical modules:

- `castforge.briefing` — optional Gemini briefing;
- `castforge.export` — UTF-8 Markdown export;
- `castforge.notebooklm_audio` — `publish_audio` and `publish_audio_async`.

Nitan no longer carries `_castforge.py` path mutation or local `briefing_writer.py`, `notebooklm_export.py`, and `notebooklm_audio.py` compatibility facades. This keeps one owner for each reusable behavior and makes a missing dependency fail at installation/configuration time instead of being hidden by a sibling checkout.

## Subscriber contract

The integration must preserve all subscriber-visible endpoints and retained artifacts:

- `https://lifan-builds.github.io/nitan-podcast/feed.xml`;
- `https://lifan-builds.github.io/nitan-podcast/`;
- `https://lifan-builds.github.io/nitan-podcast/episodes/weekly_meika_YYYY-Www.mp3`;
- episode GUIDs in the `nitan-podcast-YYYY-Www` format;
- every tracked file under `docs/episodes/`.

The CastForge migration changes code ownership only; it does not rewrite the feed, site, GUIDs, or historical media.

## Validation

Run the offline suite with the current CastForge checkout when developing the two repositories together:

```bash
PYTHONPATH=/path/to/castforge pytest tests/ -v
```

The fixture smoke remains offline and disposable:

```bash
EXTRACTION_FIXTURE_PATH=fixtures/sample_extraction.json \
  python run_pipeline.py --skip-briefing --dated
```

Do not use live MCP, NotebookLM, forum, publication, or feed checks as generic migration validation.
