---
url: "https://vite.dev/config/worker-options"
title: "Worker Options"
created_at: "2026-05-26T05:14:59.445652+00:00"
---
# Worker Options

Unless noted, the options in this section are applied to all dev, build, and preview.

- Type: 'es' | 'iife'
- Default: 'iife'

Output format for worker bundle.

- Type: () => (Plugin | Plugin[])[]

Vite plugins that apply to the worker bundles. Note that config.plugins only applies to workers in dev, it should be configured here instead for build. The function should return new plugin instances as they are used in parallel rolldown worker builds. As such, modifying config.worker options in the config hook will be ignored.

## worker.rolldownOptions

- Type: RolldownOptions

Rolldown options to build worker bundle.

## worker.rollupOptions

- Type: RolldownOptions
- Deprecated

This option is an alias of worker.rolldownOptions option. Use worker.rolldownOptions option instead.
