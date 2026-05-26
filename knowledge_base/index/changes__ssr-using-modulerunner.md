---
url: "https://vite.dev/changes/ssr-using-modulerunner"
title: "SSR Using ModuleRunner API"
created_at: "2026-05-26T05:14:57.972760+00:00"
---
# SSR Using ModuleRunner API

Give us feedback at Environment API feedback discussion

server.ssrLoadModule has been replaced by importing from a Module Runner .

Affected scope: Vite Plugin Authors

ModuleRunner was first introduced in v6.0 . The deprecation of server.ssrLoadModule is planned for a future major. To identify your usage, set future.removeSsrLoadModule to "warn" in your vite config.

The server.ssrLoadModule(url) only allows importing modules in the ssr environment and can only execute the modules in the same process as the Vite dev server. For apps with custom environments, each is associated with a ModuleRunner that may be running in a separate thread or process. To import modules, we now have moduleRunner.import(url) .

Check out the Environment API for Frameworks Guide .

server.ssrFixStacktrace and server.ssrRewriteStacktrace do not have to be called when using the Module Runner APIs. The stack traces will be updated unless sourcemapInterceptor is set to false .
