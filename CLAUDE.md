# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A CLI tool that extracts *visually distinct* frames from a video, published to PyPI as `distant-frames`. It samples one frame per second and keeps a frame only when it differs enough from the last frame it kept.

## Commands

```bash
uv sync --frozen                          # install deps
uv run distant-frames <video> [options]   # run installed entry point
uv run main.py <video> [options]          # run from clone without installing
uv build                                  # build wheel + sdist
```

There is **no test suite** — no pytest, no test files. CI (`.github/workflows/ci.yml`) only builds the package and checks that `distant-frames --help` runs. Verification is empirical, against real videos:

```bash
uv run generate_test_video.py             # writes test_video.mp4 with known scene changes
uv run main.py test_video.mp4             # expect exactly 2 frames (t=0 red, t=3 blue)
```

`generate_test_video.py` is the only verification helper in the repo. It produces a 5s 10fps clip and is a smoke test, not a metric benchmark — it is far too short and too synthetic to judge a metric change on. Anything touching the similarity metric or the refinement stage needs real footage and a side-by-side comparison of the frames actually emitted, not just a count.

There is **no labelled corpus**, which is the single biggest gap in this repo. Every cutoff in the refinement stage was tuned against synthetic clips generated ad hoc. Building a labelled set — a slide deck and a talking-head clip, keep/drop marked per sampled second — is the prerequisite for any confident tuning work.

## Architecture

Three files carry everything:

- `distant_frames/core.py` — all logic: the similarity metric, the extraction loop, the optional refinement stage, the optional Haar-cascade eye filter.
- `distant_frames/cli.py` — a thin Typer wrapper. Holds its own copy of the default threshold.
- `main.py` — a shim so a clone runs without installing.

### The extraction loop

Two separate concerns that are easy to conflate:

- **Where segments begin** — each sampled frame is compared against the frame that *started the current segment* (the last frame actually saved), never against the previous sample. This is deliberate: it lets a slow drift accumulate until it crosses the threshold. A consecutive-frame comparison merges gradual sequences into one segment and loses scenes. Don't "fix" it that way.

  Note that `skip_reference_frame` and `last_saved_frame` are always assigned the same frame, so the reference selection resolves identically down both paths — only the log label (`skip_ref` vs `last`) differs. The branch is vestigial.

- **Which frame represents a segment** — the frame that *triggered* the change is written. On animated content that means the frame is caught mid-transition: text still flying in, a logo half drawn. This is the cost of deciding and writing in the same pass, and it is why the refinement stage has a settling rule (below). The first sampled frame is always saved unconditionally, with no settle check, so a video that opens mid-animation yields a poor first frame.

- **Decoding** — the loop seeks once to `--start`, then walks the stream with `grab()`, calling `retrieve()` only on sampled seconds. Do **not** reintroduce a per-sample `cap.set(CAP_PROP_POS_FRAMES, ...)`: on inter-frame-coded video every seek restarts the decoder from the nearest keyframe. Measured on 120s of 720p, the seek-per-sample approach costs 4.90s against 0.96s sequential on H.264 with a 250-frame GOP (**5.09x**), while returning identical frame indices and identical pixels. Short-GOP files hide the difference (1.34x), so benchmark on realistic long-GOP H.264 or you will conclude it doesn't matter.

## The similarity metric

`calculate_similarity()` converts both frames to HSV and correlates their normalized Hue/Saturation histograms. That is the whole default metric. It is cheap and robust to lighting, and it has one important, measured blind spot:

**Flat graphic content has near-zero saturation, so different slides can produce near-identical H/S histograms.** A slide-to-slide text change on the reference deck scores **1.000** — literally indistinguishable from an identical frame. Whole scenes get dropped silently. This is not hypothetical; it is reproducible.

The reason is structural, and it applies to *any* whole-frame average, not just this histogram: a title changing on a flat background alters a few percent of the picture. Measured on that same pair, the change scores **1.14** as a frame-wide mean colour difference but **22.36** as a worst-tile difference, against **0.27** for a true duplicate. If you ever add a cheap global check, score it from the **worst tile, not the frame average**, or it will not fire at all. This mistake has been made in this codebase before.

Also note the metric is colour-based for a reason. A grayscale comparison collapses an equal-brightness cut between two saturated colours — the two frames become identical. Any luminance-only signal added here inherits that.

## The refinement stage (`--refine`, opt-in)

A second stage for frames the histogram wants to skip. It exists to cover the blind spot above without replacing the histogram, and it is deliberately asymmetric: it can only turn a **SKIP into a SAVE**, never the reverse. A missed scene change is unrecoverable; a redundant frame is cheap. Because of that, `--refine` output is always a strict superset of the same run without it, and `--threshold` keeps its exact meaning.

The pipeline:

1. **Guard** — worst-tile colour difference over an 8×8 grid of a 64px thumbnail. Escalates only; never decides. Cutoff `_GUARD_DELTA_CUTOFF = 4.0`.
2. **Route** — `_flat_fraction()` measures the share of the picture in near-uniform regions. At or above `_FLAT_FRACTION_CUTOFF = 0.45` the frame is graphic content and goes to **HOG under L2**; below it, camera footage, to **ORB under Hamming**. ORB descriptors are binary — use `NORM_HAMMING`, not L2. Slides yield few keypoints and the ones they do yield sit on the deck template (logo, rules, footer), identical across every slide, so ORB alone rates two different slides as a near-perfect match. That is what the router exists to avoid.
3. **Colour side-channel** — HOG is gradient orientation on luminance, so a cut between two flat frames of different colour scores exactly **0.000**. On the HOG route only, a region-scale colour shift (`_COLOUR_DISTINCT_DELTA = 60.0`) is therefore decided on colour alone.
4. **Settle** — a frame judged distinct is held until consecutive samples stop differing (`_SETTLE_DELTA = 4.0`), so an animation emits its settled state once rather than one frame per transition step. `_SETTLE_MAX_WAIT = 8` forces a save if content never settles, so continuously animating material cannot lose a scene outright.

On a 3-slide deck with titles flying in (ideal 3 frames): the default path finds **1 of 3 slides**; `--refine` without settling emits **9** frames; with settling, **4**, all three slides recovered as settled states. The settling rule is what makes this stage usable on motion graphics.

**Refined saves can lag** the change that caused them by a second or two, since the frame is held until motion stops. Frames saved by the histogram itself are unaffected.

## The unavoidable tradeoff

There is **no descriptor cutoff that classifies every case correctly**, and this has been measured rather than assumed. "An element moves within a busy slide" and "small text changes on a mostly-empty slide" produce localised differences of the same magnitude — geometrically they are the same event.

Measured with HOG/L2 across two clips, the gap between the least-similar true duplicate and the most-similar true change is **−0.118**: a true change at 0.635 sits *between* duplicates at 0.612 and 0.641. A sweep of 36 descriptor geometries (size × cell × blur) found only two marginally positive settings, +0.032 and +0.012, which is overfitting on a handful of pairs rather than a usable default.

The settling rule sidesteps this by using a **temporal** signal instead of a spatial one, which does separate cleanly: while a title flies in, consecutive samples differ by 7.7–32.7; once it lands, by 0.0–0.5. That is why the fix lives there and not in the descriptor. Don't try to solve the spatial overlap by re-tuning cutoffs — it has been measured and it does not separate.

### Prior findings from an unshipped metric

These were recorded against a tiled/blurred worst-tile metric that **is not in this tree** and never shipped. Keep them for context, but do not read them as describing current code:

- The same duplicate/change overlap was measured at −0.116 (no blur) to −0.029 (heavy blur) — never positive. Two independent metric families landing in the same place is good evidence the overlap is a property of the problem, not of a particular descriptor.
- A **displacement search** (matching tiles across small offsets) looks like the obvious fix for the movement case and was evaluated and rejected: taking the best match over candidate offsets can only *raise* a similarity score, so it lifts genuinely distinct pairs too and misses real scene changes.
- Content-dependent thresholds were measured at roughly `0.86` for graphic content and `0.75` for camera footage, with no overlap between the required values. No auto-selection exists in the current code — `--threshold` is a single value the user supplies.

## Gotchas

- **Higher `--threshold` saves MORE frames, not fewer.** The test is `similarity < threshold`, so raising it widens what counts as "different". This reads backwards at a glance and has already been miswritten in `cli.py`'s help text once ("Higher values mean stricter deduplication (fewer frames saved)" — the opposite of what the code does). All three descriptions now state the direction explicitly; keep it that way when editing them.
- **The threshold default lives in three places and they must be changed together**: `core.py` (`extract_frames(threshold=...)`), `cli.py` (the `--threshold` option default), and the `README.md` options table. They are currently aligned at **0.78**. The CLI default is what users actually get, so a disagreement there is silent — `core.py`'s value only surfaces when the function is called as a library.
- **The ORB route has never executed.** Across every sampled second of all test material the router chose HOG 161 times and ORB zero times, because that material is all graphic content (flat fraction 0.83–1.00). `_ORB_MATCH_CUTOFF`, `_ORB_HAMMING_CUTOFF` and `_orb_match_ratio()` are unexercised. Real camera footage is the missing test input.
- **Changing the metric changes what `--threshold` means.** Scores are not comparable across metric versions, and there is no conversion factor. Any metric change needs a new default threshold, a version bump, and a breaking-changes note in `RELEASE_NOTES.md`.
- **Pushing to `main` publishes to PyPI.** `.github/workflows/publish.yml` triggers on every push to `main`, not on tags. The version in `pyproject.toml` must be bumped first or the upload fails on a duplicate version. Use `uv version --bump minor`, then `uv lock` (the lockfile pins the project's own version).

## Conventions

- `uv` for everything; Python 3.12+.
- Docstrings are Google-style with `Args:`/`Returns:`, and explain *why* a non-obvious choice was made, not just what the code does. The refinement helpers carry their measured justification inline — keep that habit; the numbers are why the code looks the way it does.
- `RELEASE_NOTES.md` is maintained by hand, newest first, and documents breaking changes and known limitations explicitly.
- GPL-3.0-or-later.
