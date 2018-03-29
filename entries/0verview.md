---
title: 0-based Versioning
publish_date: March 3, 2018
---

* Software versions for minimalists
* Cutting-edge versioning scheme
* Open-source approved
* Hundreds of thousands of open-source users

Pretty much every project in the open-source world agrees: **Major
versions are for suckers**. The best versions are like arrays:
0-based.

[TOC]

List of popular projects using this scheme: cython, docutils, datadog,
werkzeug, flask, etc. toml call-out for hypocrisy. OpenSSL gets an
honorable mention for staying on v0 until 2015. scipy same, for 16
years. They lost their nerve and will be sorely missed. These projects
prove you can't rush perfection (but you can certainly delay it)
(more: dash, inkscape, pandas, wheel, ...)

# Featured Use Cases

The vanguard of the ZeroVer camp.

## TOML

Versioning scheme like SemVer and CalVer attempt to guide developers
away from the natural light of ZeroVer. In a surprising and exciting
move, the creator of SemVer appears to have seen the light himself.

So kudos to Tom, for helping ZeroVer triumph over his own SemVer,
TOML's stated versioning scheme since 0.1 in 2013. Leading a public
project, advertising dozens of public implementations, Tom has shown
great versioning fortitude in preventing the rise of TOML's major
version. <span title="Thom">Thanks Tom</span>.

## Hashicorp Vault and Terraform

Hashicorp's Vault project aims to be an enterprise secret management
service, comprising the bedrock of a modern, microservice-oriented
environment. And that's why it's one of ZeroVer's most important
adherents.

> *Low in the stack, low in the version, that's the Hashicorp way.*

Even further down the stack, Hashicorp's Terraform also complies with
ZeroVer's cutting-edge versioning scheme. With Vault and Terraform,
Hashicorp demonstrates industry recognition of the importance of
ZeroVer in infrastructure, even when the projects are
business-critical products, sold and supported.

## OpenSSL

While no longer technically a ZeroVer project, OpenSSL held out from
1998 to 2010 before finally succumbing to 1.0. The project managed to
change its name (from SSLeay) and implementation technology (from Perl
to C) all thanks to streamlined minimal versioning.

[openssl_1_release]: https://lwn.net/Articles/380949/

# ZeroVer Projects

[ZEROVER_PROJECT_TABLE]

# Selected Alumni

Graduates from the school of ZeroVer join the heralded ranks of
projects like OpenSSL. They will be missed.

[ALUMNI_PROJECT_TABLE]

TODO: links, initial release, number of releases, etc.

   Project           |  Initial release | Number of releases |  Current version
---------------------|------------------|--------------------|-----------------
[Werkzeug][werkzeug] |  0.1 (2007)      |  52                |   0.14.1 (2018-04-01)
[docutils][docutils] |  0.3 (2003)      |  19                |   0.14 (2018-04-01)
