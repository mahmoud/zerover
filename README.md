# ZeroVer

ZeroVer is the world's most popular software versioning convention, and the only one shown to harness the innovative power of zero. The benefits are innumerable and the effects on the software world are profound.

Read more at **[0ver.org](https://0ver.org)**.

## Description

The site is statically generated using [Chert](https://github.com/mahmoud/chert). The configuration for the Chert site is defined in [`chert.yaml`](chert.yaml) The pages for the site are located under [`entries/`](entries).

Tables of current and past ZeroVer users are generated from `projects.yaml` into `projects.json` by `tools/gen_projects_json.py` using the GitHub API. The project list has gotten long enough that you'll need [a GitHub API key](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token).

`custom.py` uses Chert hooks to render and inject tables based off of `projects.json`. `custom.py` and `tools/gen_projects_json.py` are both written to only depend on libraries required by Chert. To bring things full circle, Chert was 0ver for almost 3 years.

## Contributing

Are you or someone you know a prominent ZeroVer user who's missing from our list? Feel free to contribute to the site and add this project!

Qualifications in notable [0ver.org](https://0ver.org) entries:

- A current ZeroVer-compliant version (`0.*`) or long history of ZeroVer usage, and
- Very wide exposure (i.e., 1,000+ GitHub stars), or
- Active promotion as part of a paid product or service (e.g., Hashicorp Vault), or
- Relative maturity and infrastructural importance (e.g., Compiz, docutils)

To add a project, follow the guide below.

1. Fork and clone this repository, then create a new branch. GitHub has [a great guide](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project) on contributing to open-source projects like this.
2. On the new branch, add your project to [`projects.yaml`](projects.yaml). See the [`project.yaml` keys description](#project-yaml-keys-description) below.
3. Commit the change and create a pull request on GitHub.

## project.yaml Keys Description

- [Simple GitHub Projects](#simple-github-projects) (ZeroVer tags used)
- [Complex GitHub Projects](#complex-github-projects-or-non-github-projects) (ZeroVer tags not used)
- [Non-GitHub Projects](#complex-github-projects-or-non-github-projects)
- [Emeritus Complex GitHub Projects](#emeritus-complex-github-projects-or-emeritus-non-github-projects)
- [Emeritus Non-GitHub Projects](#emeritus-complex-github-projects-or-emeritus-non-github-projects)

### Simple GitHub Projects

If the project you are adding is hosted on GitHub with ZeroVer compatible tags, you simply need to add the following snippet to the [`projects.yaml`](projects.yaml) file. This will work with currently ZeroVer projects and emeritus projects.

```yaml
- name: Project Name
  gh_url: https://github.com/example/test
```

Additionally, you can add a homepage URL, Wikipedia URL and/or reasoning like this:

```yaml
- name: Project Name
  url: https://example.com
  gh_url: https://github.com/example/test
  wp_url: https://www.wikipedia.org/
  reason: This project is a core component of a large system used by millions of users around the world.
```

If the project did not begin on GitHub, the tags may not extend to the origin of the project. You may want to fix these by manually entering the first release data found on the project website or other sources.

```yaml
- name: Project Name
  url: https://example.com
  gh_url: https://github.com/example/test
  reason: This project is a core component of a large system used by millions of users around the world.
  first_release_date: 2000-01-01
  first_release_version: 0.1 # This release isn't tagged on GitHub, see here: https://example.com/releases/0.1
```

### Complex GitHub Projects or Non-GitHub Projects

If the project you are adding is hosted on GitHub with incompatible ZeroVer tags (e.g. tags are prefixed with odd text) or the project is not on GitHub, you will need to fill out a more detailed entry in the [`projects.yaml`](projects.yaml) file.

```yaml
- name: Project Name
  url: https://example.com
  first_release_date: 2000-01-01
  first_release_version: 0.1 # Reference: https://example.com/releases
  latest_release_date: 2024-12-28
  latest_release_version: 0.37.2 # Reference: https://example.com/releases
```

If the repository is available but not on GitHub, you can add the `repo_url` key.

```yaml
- name: Project Name
  url: https://example.com
  repo_url: https://gitlab.com/example
  first_release_date: 2000-01-01
  first_release_version: 0.1 # Reference: https://example.com/releases
  latest_release_date: 2024-12-28
  latest_release_version: 0.37.2 # Reference: https://example.com/releases
```

If the release count is available you can add the `release_count` key.

```yaml
- name: Project Name
  url: https://example.com
  repo_url: https://gitlab.com/example
  first_release_date: 2000-01-01
  first_release_version: 0.1 # Reference: https://example.com/releases
  latest_release_date: 2024-12-28
  latest_release_version: 0.37.2 # Reference: https://example.com/releases
  release_count: 100 # Reference: https://example.com/releases
```

### Emeritus Complex GitHub Projects or Emeritus Non-GitHub Projects

If a complex GitHub project or non-GitHub project is no longer ZeroVer and needs to be added to the emeritus list, you will need to change several keys.

```yaml
- name: Project Name
  url: https://example.com
  emeritus: true
  first_release_date: 2000-01-01
  first_release_version: 0.1 # Reference: https://example.com/releases
  first_nonzv_release_date: 2024-12-30
  last_zv_release_version: 0.37.2 # Reference: https://example.com/releases
  release_count_zv: 100 # Reference: https://example.com/releases
```

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
