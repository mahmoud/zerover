# ZeroVer

ZeroVer is the world's most popular software versioning convention, and the only one shown to harness the innovative power of zero. The benefits are innumerable and the effects on the software world are profound.

Read more at **[0ver.org](https://0ver.org)**.

## Description

The site is statically generated using [Chert](https://github.com/mahmoud/chert). The configuration for the Chert site is defined in [`chert.yaml`](chert.yaml) The pages for the site are located under [`entries/`](entries).

Tables of current and past ZeroVer users are generated from `projects.yaml` into `projects.json` by `tools/gen_projects_json.py` using the GitHub API. The project list has gotten long enough that you'll need [a GitHub API key](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token).

`custom.py` uses Chert hooks to render and inject tables based off of `projects.json`. `custom.py` and `tools/gen_projects_json.py` are both written to only depend on libraries required by Chert. To bring things full circle, Chert was 0ver for almost 3 years.

## Building

1. Create and enter a virtual environment if you haven't already
2. `pip install -r requirements.txt`

### Updating projects.json

1. Obtain a [personal access token from GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token). This token will not need any special permissions, the default options should be fine.
2. Set the envirnoment variables `GH_USER` to your GitHub username and `GH_TOKEN` to the token you just obtained.
3. Run `python tools/gen_projects_json.py`

### Serving the site

Simply run `chert serve`.

## CI/CD

0ver uses [GitHub Actions](https://github.com/features/actions) to validate `projects.yaml`, update `project.json`, and publish new versions of the site. To configure CI/CD in a fork, you only need to set the environment variables.

1. Navigate to the project's Settings -> Secrets abd variables -> Actions.
2. In the Secrets tab, add a new repository secret named `GH_TOKEN` and paste your personal access token.
3. In the Variables tab, add a new repository variable named `GH_USER` and enter your GitHub username.
