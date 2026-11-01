# Repository implementation references

- GitHub user-site naming: https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- Sileo package architecture filter: https://github.com/Sileo/Sileo/blob/c9f70158a037dc76b91c450e72af2de0514dd3ee/Sileo/Backend/Package%20Manager/PackageListManager.swift
- RootHide Zebra native/foreign architecture ranking: https://github.com/roothide/Zebra/blob/96f7000b6c54bc1791e5cde7500c551ee8b183f6/Zebra/Database/ZBDatabaseManager.m
- Zebra reads the configured dpkg architecture: https://github.com/roothide/Zebra/blob/96f7000b6c54bc1791e5cde7500c551ee8b183f6/Zebra/ZBDevice.m
- RootHide native package scheme: https://github.com/roothide/Developer

Architecture labels identify package layout and jailbreak environment, not just the CPU. The flat index places native RootHide entries before same-version rootless variants so a RootHide client accepting rootless as a foreign architecture can prefer the native build even in a first-entry selection path. Standard native-architecture filtering and Zebra native-architecture ranking select the matching variant.

Compatibility descriptions come from the pinned public release and README for each project. Original asset checksums and unchanged payload/script checks are recorded in metadata-audit.json. No RootHide build is created by relabelling a rootless package.
