---
title: "ZeroVer: 0-based Versioning"
publish_date: April 1, 2018
---

<div style="text-align:center"><i>Cutting-edge software versioning for minimalists</i></div><br/>

With software releases at an all-time high, the consensus has never
been clearer: **Major versions are over**. So what does the past,
present, and future of software versioning look like? Welcome to
ZeroVer 0.0.1.

[TOC]

<h2><span style="font-family:monospace">0</span>verview</h2>

Unlike other versioning schemes like [Semantic Versioning][semver] and
[Calendar Versioning][calver], ZeroVer (AKA [0ver][0ver]) is simple:
**Your software's major version should never exceed the first and most
important number in computing: *zero*.**

A down-to-earth demo:

**YES**: 0.0.1, 0.1.0dev, 0.4.0, 0.4.1, 0.9.8n, [0.999999999][html5lib_ouch], [0.0](/uploads/sensor_0.0.jpg)

**NO**: 1.0, 1.0.0-rc1, 18.0, 2018.04.01

In short, software versioning best practice is like the modern
list/array: 0-based.

We'll leave it to computer scientists to determine how expert coders
wield the power of the "[zero-point][zpe]" to produce top-notch
software. Meanwhile, open-source and industry developers agree:
ZeroVer is software's most popular versioning scheme for good reason.

Just take a look at the list below. Some thought leaders might
surprise you.

[0ver]: https://0ver.org
[zpe]: https://en.wikipedia.org/wiki/Zero-point_energy
[html5lib_ouch]: https://github.com/html5lib/html5lib-python/commit/6a73efa01754253605284b5a5688de3961b120fa

# Notable ZeroVer Projects

The growing vanguard of the versioning revolution. [Add your project
here](/submissions.html).

<!-- see projects.yaml/json for source material of table below -->
[ZEROVER_PROJECT_TABLE]

<br/>At the time of writing, the list is somewhat biased toward Python
projects. If you know of some prominent ZeroVer projects, [submit them
here](/submissions.html)!


# Featured Use Cases

These flagship ZeroVer projects know how to get the most out of their
zeroes.

## HashiCorp Vault and Terraform

<img align="left" style="padding-right: 15px" width="15%" src="/uploads/vault_logo.png">
[HashiCorp's Vault][vault] project aims to be an enterprise secret
management service, comprising the bedrock of a modern,
microservice-oriented environment. And that's what makes it one of
ZeroVer's most important adherents.

> *Low in the stack, low in the version. That's the HashiCorp way.*

<img align="right" width="30%" style="padding-left: 15px" src="/uploads/terraform_logo.png">

To drive the point home, even further down the stack, HashiCorp's
[Terraform][terraform] also complies with ZeroVer's cutting-edge
versioning scheme. With Vault and Terraform, HashiCorp demonstrates
industry recognition of the importance of ZeroVer in infrastructure.

HashiCorp knows ZeroVer works, especially when the projects are
business-critical products, sold and supported.

[vault]: https://www.vaultproject.io/
[terraform]: https://www.terraform.io/

## TOML

Versioning schemes like [SemVer][semver] and [CalVer][calver] attempt
to guide developers away from the natural light of ZeroVer. In a
surprising and exciting move, the creator of SemVer
[himself][toml_tom] has seen the light.

Aside from [one small typo in 2013][toml_2013], his new project, TOML,
has been a model ZeroVer user. These days TOML [advertises dozens of
public implementations][toml_impls], many of which missed the ZeroVer
message. They're probably caught up in Tom's own words from 2011:

> *"If your software is being used in production, it should probably already be 1.0.0."*

No doubt older and wiser, [Tom][toml_tom] has shown great versioning
fortitude in averting a rise in TOML's major version and promoting
ZeroVer conventions. <span title="Thom">Thanks Tom</span>!

[semver]: http://semver.org/
[calver]: https://calver.org/
[toml_tom]: http://github.com/mojombo
[toml_2013]: https://github.com/toml-lang/toml/releases/tag/v0.1.0
[toml_impls]: https://github.com/toml-lang/toml/wiki#implementations

## Apache Kafka

<img align="right" width="30%" style="padding-left: 15px" src="/uploads/kafka_logo.png">
One of the strongest brands in modern software also subscribed to the
strongest versioning scheme. To understand the version scheme, we have
to understand the name, as the software shares quite a bit in common
with its namesake.

[Apache Kafka][a_kafka] was named after [Franz Kafka][f_kafka], who
lived as an author in turn-of-the-20th-century Austria. Like the
project named after him, he was [slow to start][kafka_slow_start],
[inconsistent in delivery][kafka_jepsen], and left [a mess of
unpublished work][kafka_unpublished] after a tragically early
death. Most experts have come to agree, for all their complexity and
absurdity, Kafka's writings have been influential, despite [the
prevalence of bugs][kafka_bugs]. Still, true consensus is only found
in the one true Kafka fact: most invocations of the name "Kafka" are
attempts at appearing smart by those with relatively little experience
on the topic.

So how does ZeroVer fit in to the Kafka brand? Whereas the Kafka name
mirrors his writing style, for over four years, Apache Kafka's ZeroVer
policy mirrored Franz Kafka's own life and relationships: short,
intense, and [rarely conjugated or
consummated](https://en.wikipedia.org/wiki/Franz_Kafka#Private_life).

*ZeroVer: the most [Kafkaesque][kafkaesque] versioning scheme.*

[a_kafka]: https://en.wikipedia.org/wiki/Apache_Kafka
[f_kafka]: https://en.wikipedia.org/wiki/Franz_Kafka
[kafka_slow_start]: http://mail-archives.apache.org/mod_mbox/kafka-dev/201709.mbox/%3C04F3F442-0BD3-4A2D-A93D-AFF0C108FFC8@simplemachines.com.au%3E
[kafka_jepsen]: https://aphyr.com/posts/293-jepsen-kafka
[kafka_unpublished]: https://qz.com/754322/kafkaesque-instructions-on-what-to-do-with-franz-kafkas-manuscripts-produce-a-kafkaesque-legal-battle/
[kafka_bugs]: https://en.wikipedia.org/wiki/The_Metamorphosis
[kafkaesque]: https://www.theguardian.com/books/booksblog/2016/may/18/kafkaesque-a-word-so-overused-it-has-lost-all-meaning

## OpenSSL

Has there ever been a library more auspicious? By now it should come
as no surprise that OpenSSL has its roots in ZeroVer.

<img align="center" width="50%" src="/uploads/openssl_logo.png">

While no longer technically a ZeroVer project, [OpenSSL][openssl] held
out from 1998 to 2010 before finally succumbing to 1.0. What happened
after that is beyond the scope of this document, but let it serve as a
warning to those who might stray beyond 0.

In the good old days of 0ver OpenSSL, the project managed to change its name (from
[SSLeay][ssleay]) and implementation technology (from
[Perl][ssleay_cpan] to C), not to mention [run through half the
alphabet][openssl_changelog] in micro versioning.

That's the power of a streamlined and minimal ZeroVer version.

[openssl]: https://en.wikipedia.org/wiki/OpenSSL
[openssl_1_release]: https://lwn.net/Articles/380949/
[ssleay]: https://en.wikipedia.org/wiki/SSLeay
[ssleay_cpan]: http://search.cpan.org/~mikem/Net-SSLeay-1.85/lib/Net/SSLeay.pod
[openssl_changelog]: https://www.openssl.org/news/changelog.html

# Selected Emeriti

Dearly departed from the school of ZeroVer, either from above or from
legend. We remember them fondly.

<!-- see projects.yaml/json for source material of table below -->
[EMERITUS_PROJECT_TABLE]

<br/>With any luck, these projects will realize their folly.

# More info

Check out the [About](/about.html) page.
