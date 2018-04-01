# ZeroVer

ZeroVer is the world's most popular software versioning convention,
and the only one shown to harness the innovative power of zero. The
benefits are innumerable and the effects on the software world are
profound.

Read more at **[0ver.org](https://0ver.org)**.

## Building

The site is statically generated using
[Chert](https://github.com/mahmoud/chert).

Content is all under `entries/`.

Tables of current and past ZeroVer users are generated from
`projects.yaml` into `projects.json` by `tools/gen_projects_json.py`
using the GitHub API. The project list has gotten long enough that
you'll need an API key.

`custom.py` uses Chert hooks to render and inject tables based off of
`projects.json`. `custom.py` and `tools/gen_projects_json.py` are both
written to only depend on libraries required by Chert. To bring things
full circle, Chert has been 0ver for almost 3 years at the time of
writing.
