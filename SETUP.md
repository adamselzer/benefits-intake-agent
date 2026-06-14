# Setup notes

## GitHub

Already on GitHub (created and pushed with the `gh` CLI as `adamselzer`):

```
https://github.com/adamselzer/benefits-intake-agent
```

Push further changes with `git add -A && git commit && git push`.

## The rules core dependency

The screen step uses the `rules-as-code-mcp` project. Install it editable from the
sibling checkout:

```bash
pip install -e ../rules-as-code-mcp
```

(If the sibling repo is elsewhere, adjust the path or `pip install` it from its Git
URL.)

## API key

The deterministic pipeline, the eval harness (`--extractor truth`), and the tests
all run with **no API key**. Real Claude-vision extraction and the
`--extractor vision` eval need one:

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env   # .env is gitignored
```

Commit identity is set per-repo to `Adam Selzer <hello@aselzer.com>`.

## Regenerating cases

The per-case directories and PDFs are gitignored (regenerable); only
`data/cases/labels.json` is committed. Regenerate the full set with:

```bash
python data/generate_cases.py
```
