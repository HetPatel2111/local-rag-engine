---
url: "https://vite.dev/plugins/"
title: "Plugins"
created_at: "2026-05-26T05:15:06.263374+00:00"
---
# Plugins

Vite aims to provide out-of-the-box support for common web development patterns. Before searching for a Vite or Compatible Rollup plugin, check out the Features Guide . A lot of the cases where a plugin would be needed in a Rollup project are already covered in Vite.

Check out Using Plugins for information on how to use plugins.

Provides Vue 3 Single File Components support.

### @vitejs/plugin-vue-jsx

Provides Vue 3 JSX support (via dedicated Babel transform ).

### @vitejs/plugin-react

Provides React Fast Refresh support via Oxc Transformer .

### @vitejs/plugin-react-swc

Replaces Oxc with SWC during development for SWC plugin usage. During production builds, SWC+Oxc Transformer are used when using plugins. For big projects that require custom plugins, cold start and Hot Module Replacement (HMR) can be significantly faster, if the plugin is also available for SWC.

Vite supports React Server Components (RSC) through the plugin. It utilizes the Environment API to provide low-level primitives that React frameworks can use to integrate RSC features. You can try a minimal standalone RSC application with:

```
npm create vite@latest -- --template rsc
```

Read the plugin documentation to learn more.

### @vitejs/plugin-legacy

Provides legacy browsers support for the production build.

Check out Vite Plugin Registry for the list of plugins published to npm.

## Rolldown Builtin Plugins

Vite uses Rolldown under the hood and it provides a few builtin plugins for common use cases.

Read the Rolldown Builtin Plugins section for more information.

## Rolldown / Rollup Plugins

Vite plugins are an extension of Rollup's plugin interface. Check out the Rollup Plugin Compatibility section for more information.
