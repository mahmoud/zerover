---
title: "ZeroVer: 0-based Versions"
publish_date: March 3, 2018
---

<div style="text-align:center"><i>Cutting-edge software versioning for minimalists</i></div><br/>

With software releases at an all-time high, the consensus has never
been clearer: **Major versions are over**. So what does the past,
present, and future of software versioning look like?

[TOC]

<h2><span style="font-family:monospace">0</span>verview</h2>

The ZeroVer versioning scheme (AKA [0ver][0ver]) is simple: **Your
software's major version should never exceed the first and most
important number in computing: zero.** For instance:

**OK**: 0.0.1, 0.1.0dev, 0.4.0, 0.4.1, 0.9.8n, [0.999999999][html5lib_ouch]

**NOT OK**: 1.0, 1.0.0-rc1, 18.0, 2018.04.01

In short, software versioning best practice is like the modern
list/array: 0-based.

We'll leave it to computer scientists to determine exactly how master
coders channel the power of the "[zero-point][zpe]" to produce
top-notch software. Meanwhile, open-source and industry developers
agree: ZeroVer is software's most popular versioning scheme. And as
the examples below demonstrate, 0ver shows no sign of slowing down.

[0ver]: 0ver.org
[zpe]: https://en.wikipedia.org/wiki/Zero-point_energy
[html5lib_ouch]: https://github.com/html5lib/html5lib-python/commit/6a73efa01754253605284b5a5688de3961b120fa

# Featured Use Cases

These flagship ZeroVer projects know how to get the most out of their
zeroes.

## TOML

Versioning schemes like [SemVer][semver] and [CalVer][calver] attempt
to guide developers away from the natural light of ZeroVer. In a
surprising and exciting move, the creator of SemVer has returned to
the light himself!

So hats off to [Tom][toml_tom], it must not have been easy to turn his
back on his own SemVer, [TOML's stated versioning scheme since 0.1 in
2013][toml_2013]. In SemVer Tom's own words:

> *If your software is being used in production, it should probably already be 1.0.0.*

These days, leading a public project which [advertises dozens of
public implementations][toml_impls] used by who-knows-how-many
applications, ZeroVer Tom has shown great versioning fortitude in
preventing the rise of TOML's major version. <span title="Thom">Thanks
Tom</span>!

[semver]: http://semver.org/
[calver]: https://calver.org/
[toml_tom]: http://github.com/mojombo
[toml_2013]: https://github.com/toml-lang/toml/releases/tag/v0.1.0
[toml_impls]: https://github.com/toml-lang/toml/wiki#implementations

## Hashicorp Vault and Terraform

[Hashicorp's Vault][vault] project aims to be an enterprise secret
management service, comprising the bedrock of a modern,
microservice-oriented environment. And that's what makes it one of
ZeroVer's most important adherents.

> *Low in the stack, low in the version. That's the Hashicorp way.*

To drive the point home, even further down the stack, Hashicorp's
[Terraform][terraform] also complies with ZeroVer's cutting-edge
versioning scheme. With Vault and Terraform, Hashicorp demonstrates
industry recognition of the importance of ZeroVer in infrastructure.
ZeroVer works, even when the projects are business-critical products,
sold and supported.

[vault]: https://www.vaultproject.io/
[terraform]: https://www.terraform.io/

## OpenSSL

While no longer technically a ZeroVer project, [OpenSSL][openssl] held
out from 1998 to 2010 before finally succumbing to 1.0. The project
managed to change its name (from [SSLeay][ssleay]) and implementation
technology (from [Perl][ssleay_cpan] to C), not to mention [run
through half the alphabet][openssl_changelog] in micro versioning, all
thanks to streamlined minimal versioning.

[openssl]: https://en.wikipedia.org/wiki/OpenSSL
[openssl_1_release]: https://lwn.net/Articles/380949/
[ssleay]: https://en.wikipedia.org/wiki/SSLeay
[ssleay_cpan]: http://search.cpan.org/~mikem/Net-SSLeay-1.85/lib/Net/SSLeay.pod
[openssl_changelog]: https://www.openssl.org/news/changelog.html

# Popular ZeroVer Projects

The vanguard of the versioning revolution.

[ZEROVER_PROJECT_TABLE]

<br/>At the time of writing, the list is somewhat biased toward Python
projects. If you know of some prominent ZeroVer projects, submit them
here!

# Selected Alumni

Graduates from the school of ZeroVer, either from the table above or
from legend. We remember them fondly.

[ALUMNI_PROJECT_TABLE]

# More info

Check out the [About](/about.html) page.
