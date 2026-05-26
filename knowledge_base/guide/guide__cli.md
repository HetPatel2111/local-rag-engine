---
url: "https://vite.dev/guide/cli"
title: "Command Line Interface"
created_at: "2026-05-26T05:15:03.001941+00:00"
---
# Command Line Interface

Start Vite dev server in the current directory. vite dev and vite serve are aliases for vite .

```
vite [root]
```

Build for production.

```
vite build [root]
```

Pre-bundle dependencies.

Deprecated : the pre-bundle process runs automatically and does not need to be called.

```
vite optimize [root]
```

Locally preview the production build. Do not use this as a production server as it's not designed for it.

This command starts a server in the build directory (by default dist ). Run vite build beforehand to ensure that the build directory is up-to-date. Depending on the project's configured appType , it makes use of certain middleware.

```
vite preview [root]
```
