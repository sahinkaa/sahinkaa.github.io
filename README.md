# sahinkaa

APT repository: **https://sahinkaa.github.io/**

Add the URL to Sileo or Zebra. Repository label: **sahinkaa**. The icon is the account's GitHub profile picture.

The root is a flat Debian repository. Both flat and suite Release files include `Components: main`, which Sileo requires even for flat sources. `Release` advertises `iphoneos-arm64` (rootless) and `iphoneos-arm64e` (native RootHide). `Packages` contains separate entries for both builds with the original package IDs and unchanged versions. Current clients select by their jailbreak's package architecture, not the phone CPU name. RootHide requires a RootHide-aware package manager.

There are 15 released tweaks and 28 packages. Two projects have only rootless releases and are distributed as rootless only. The repository does not relabel or convert those packages. A native RootHide release can be added later after it is built and tested.

Each package has an HTML depiction for Zebra and a native JSON depiction for Sileo, with compatibility information and links to its original project. GitHub release assets remain unchanged. Repository copies add compatibility text when missing, HTTP icons and depiction links. Versions, dependencies, maintainer scripts and executable payloads are preserved. `metadata-audit.json` records original/repository checksums and changed fields.

`Packages`, `.gz`, `.bz2` and `.xz` variants and their Release hashes are generated together. An optional `dists/stable/main/binary-<architecture>` layout is also provided. The normal source URL uses the flat index. This is an unsigned HTTPS repository, as is common for jailbreak sources; no private signing key is included.

## Updating

Only add published packages belonging to this account. Keep genuine rootless and RootHide builds separate. Preserve `Package`, `Version`, `Architecture` and dependency requirements. Refresh all package sizes and hashes whenever a .deb changes, then regenerate compressed indexes and Release hashes. Do not edit a .deb after indexing it.

The reproducible builder is `maintenance/build_repo.py`, with pinned source-release checksums and compatibility data alongside it. Run `python3 maintenance/build_repo.py` from a clone to rebuild, or `python3 maintenance/build_repo.py --verify` to check the committed repository without downloading anything. The builder verifies that metadata changes preserve the complete data archive and non-control maintainer files. Downloaded upstream .debs are stored outside the published repository.

Package licenses and original developer credits remain in each package and source project. See each tweak's project for its license and device-testing details.
