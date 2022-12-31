# fluxcloud

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
[![PyPI](https://img.shields.io/pypi/v/flux-cloud)](https://pypi.org/project/flux-cloud/)

<a target="_blank" rel="noopener noreferrer" href="https://github.com/converged-computing/flux-cloud/blob/main/docs/images/logo-transparent.png">
    <img align="right" style="width: 250px; float: right; padding-left: 20px;" src="https://github.com/converged-computing/flux-cloud/raw/main/docs/images/logo-transparent.png" alt="fluxcloud Logo">
</a>

> deploy workflows to the flux operator in the cloud! ☁️

This library was originally created to make it easy to run automated experiments across
a series of machine types and sizes using the [Flux Operator](https://github.com/flux-framework-flux-operator)
in Google Cloud on Google Kubernetes Engine. It will also provide a library
of templates to make it easy to learn or get started with workflows.
It will be expanded as needed.

🚧️ **under development** 🚧️

Code is under development and will be added soon! In the meantime, for early documentation, see ⭐️ [docs](docs) ⭐️

## TODO

 - should have generic template provided by library
 - cloud-select could estimate the cost?
 - command mode that only shows commands?
 - run and add more cluster examples
 - add check in run that we don't bring up/down clusters if all jobs run (and force is False)

## 😁️ Contributors 😁️

We use the [all-contributors](https://github.com/all-contributors/all-contributors)
tool to generate a contributors graphic below.

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://vsoch.github.io"><img src="https://avatars.githubusercontent.com/u/814322?v=4?s=100" width="100px;" alt="Vanessasaurus"/><br /><sub><b>Vanessasaurus</b></sub></a><br /><a href="https://github.com/converged-computing/flux-cloud/commits?author=vsoch" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

#### License

This work is licensed under the [Apache-2.0](https://github.com/converged-computing/flux-cloud/blob/main/LICENSE) license.

SPDX-License-Identifier: Apache-2.0

LLNL-CODE-764420
