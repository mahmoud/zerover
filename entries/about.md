---
title: About
special: true
---

ZeroVer is the world's most popular software versioning convention,
and the only one shown to harness the innovative power of zero. The
benefits are innumerable and the effects on the software world are
profound.

ZeroVer is satire. [Seriously, don't actually use it][poes].

On April Fools' Day 2018, [Mahmoud Hashemi][mahmoud] roped in Mark,
Moshe, Kurt, and a few other long-suffering collaborators to unleash
version 0.0.1. He's mostly busy with [FinFam][finfam] these days.

If this humble attempt at programmer humor wrecked your release
schedule, well, *someone* didn't scroll all the way to the bottom of
the page (or click on "About").

[poes]: https://en.wikipedia.org/wiki/Poe%27s_law

# Real talk

<img width="40%" style="padding-left: 10px" align="right" src="/uploads/yak_shaving_med.png">

Software is hard. Versioning is nuanced. Creative projects rarely obey
strict schedules. There are many reasons why software gets left in
prerelease mode. But there's no shortage of yak to shave.

If your project has made the ZeroVer list, it definitely meets
consensus criteria for having a public release. You've built something
useful and great, and continuing to advertise prerelease status hurts
adoption, especially for adopters trying to convince others that your
software is as dependable as practice shows.

Here are recommended guidelines from two of the most popular
versioning schemes:

* [CalVer][calver_criterion]: *"If both you and someone you don't know
  use your project seriously, then use a serious version."*
* [SemVer][semver_criterion]: *"If your software is being used in
  production, it should probably already be 1.0.0."*

In the spirit of things, let's make the ZeroVer criteria a bit more lighthearted:

* **ZeroVer**: *If a project has a logo or Wikipedia article, but not a major version, it's officially 0ver.*

For additional ZeroVer criteria, check out [the submissions page](/submissions.html).

[Here's a Wikidata Query][wd_query] that helped find some notable 0ver users.

[wd_query]: https://query.wikidata.org/#SELECT%20%3Fsoftware%20%3FsoftwareLabel%20%3Fsoftware_version%20WHERE%20%7B%0A%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22%5BAUTO_LANGUAGE%5D%2Cen%22.%20%7D%0A%20%20%3Fsoftware%20wdt%3AP31%20wd%3AQ7397.%0A%20%20%3Fsoftware%20wdt%3AP348%20%3Fsoftware_version.%0A%20%20FILTER%20REGEX%20%28%3Fsoftware_version%2C%20%22%5E0%5C%5C..%2a%22%29.%0A%0A%7D%0ALIMIT%20100

# What to do

[0ver.org][0ver] may list some auspicious names, but it's not a very
good look. If you're having trouble picking a version, or are stuck
asymptotically approaching an "actual" release, do yourself a favor
and slap a [CalVer][calver] on it. [You'll be in much better
company][calver_users].

[mahmoud]: https://github.com/mahmoud/
[finfam]: https://finfam.app/
[calver_criterion]: https://sedimental.org/designing_a_version.html#fn:2
[semver_criterion]: https://semver.org/#faq
[calver_users]: https://calver.org/users.html
[calver]: https://calver.org
[0ver]: https://0ver.org
