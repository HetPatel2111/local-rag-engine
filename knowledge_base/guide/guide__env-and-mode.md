---
url: "https://vite.dev/guide/env-and-mode"
title: "Env Variables and Modes"
created_at: "2026-05-26T05:15:03.555605+00:00"
---
# Env Variables and Modes

Vite exposes certain constants under the special import.meta.env object. These constants are defined as global variables during dev and statically replaced at build time to make tree-shaking effective.

```
if ( import . meta .env. DEV ) { // code inside here will be tree-shaken in production builds console. log ( 'Dev mode' ) }
```

Some built-in constants are available in all cases:

- import.meta.env.MODE : {string} the mode the app is running in.
- import.meta.env.BASE_URL : {string} the base url the app is being served from. This is determined by the base config option .
- import.meta.env.PROD : {boolean} whether the app is running in production (running the dev server with NODE_ENV='production' or running an app built with NODE_ENV='production' ).
- import.meta.env.DEV : {boolean} whether the app is running in development (always the opposite of import.meta.env.PROD )
- import.meta.env.SSR : {boolean} whether the app is running in the server .

import.meta.env.MODE : {string} the mode the app is running in.

import.meta.env.BASE_URL : {string} the base url the app is being served from. This is determined by the base config option .

import.meta.env.PROD : {boolean} whether the app is running in production (running the dev server with NODE_ENV='production' or running an app built with NODE_ENV='production' ).

import.meta.env.DEV : {boolean} whether the app is running in development (always the opposite of import.meta.env.PROD )

import.meta.env.SSR : {boolean} whether the app is running in the server .

Vite exposes env variables under the import.meta.env object as strings automatically.

Variables prefixed with VITE_ will be exposed in client-side source code after Vite bundling. To prevent accidentally leaking env variables to the client, avoid using this prefix. As an example, consider the following:

```
VITE_SOME_KEY=123 DB_PASSWORD=foobar
```

The parsed value of VITE_SOME_KEY – "123" – will be exposed on the client, but the value of DB_PASSWORD will not. You can test this by adding the following to your code:

```
console. log ( import . meta .env. VITE_SOME_KEY ) // "123" console. log ( import . meta .env. DB_PASSWORD ) // undefined
```

If you want to customize the env variables prefix, see the envPrefix option.

As shown above, VITE_SOME_KEY is a number but returns a string when parsed. The same would also happen for boolean env variables. Make sure to convert to the desired type when using it in your code.

VITE_* variables should not contain sensitive information such as API keys. The values of these variables are bundled into your source code at build time. For production deployments, consider a backend server or serverless/edge functions to properly secure secrets.

Vite uses dotenv to load additional environment variables from the following files in your environment directory :

```
.env                # loaded in all cases .env.local          # loaded in all cases, ignored by git .env.[mode]         # only loaded in specified mode .env.[mode].local   # only loaded in specified mode, ignored by git
```

Env Loading Priorities

An env file for a specific mode (e.g. .env.production ) will take higher priority than a generic one (e.g. .env ).

Vite will always load .env and .env.local in addition to the mode-specific .env.[mode] file. Variables declared in mode-specific files will take precedence over those in generic files, but variables defined only in .env or .env.local will still be available in the environment.

In addition, environment variables that already exist when Vite is executed have the highest priority and will not be overwritten by .env files. For example, when running VITE_SOME_KEY=123 vite build .

.env files are loaded at the start of Vite. Restart the server after making changes.

When using Bun , be aware that Bun automatically loads .env files before your script runs. This built-in behavior loads environment variables directly into process.env and can interfere with Vite's feature, as it respects existing process.env values. See oven-sh/bun#5515 for workarounds.

Also, Vite uses dotenv-expand to expand variables written in env files out of the box. To learn more about the syntax, check out their docs .

Note that if you want to use $ inside your environment value, you have to escape it with \ .

```
KEY=123 NEW_KEY1=test$foo   # test NEW_KEY2=test\$foo  # test$foo NEW_KEY3=test$KEY   # test123
```

Vite supports expanding variables in reverse order. For example, the .env below will be evaluated as VITE_FOO=foobar , VITE_BAR=bar .

```
VITE_FOO=foo${VITE_BAR} VITE_BAR=bar
```

This does not work in shell scripts and other tools like docker compose . That said, Vite supports this behavior as this has been supported by dotenv-expand for a long time and other tools in JavaScript ecosystem use older versions that support this behavior.

To avoid interop issues, it is recommended to avoid relying on this behavior. Vite may start emitting warnings for this behavior in the future.

Ignoring local .env files

.env.*.local files are local-only and can contain sensitive variables. You should add *.local to your .gitignore to avoid them being checked into git.

## IntelliSense for TypeScript

By default, Vite provides type definitions for import.meta.env in vite/client.d.ts . While you can define more custom env variables in .env.[mode] files, you may want to get TypeScript IntelliSense for user-defined env variables that are prefixed with VITE_ .

To achieve this, you can create an vite-env.d.ts in src directory, then augment ImportMetaEnv like this:

```
interface ViteTypeOptions { // By adding this line, you can make the type of ImportMetaEnv strict // to disallow unknown keys. // strictImportMetaEnv: unknown } interface ImportMetaEnv { readonly VITE_APP_TITLE : string // more env variables... } interface ImportMeta { readonly env : ImportMetaEnv }
```

If your code relies on types from browser environments such as DOM and WebWorker , you can update the lib field in tsconfig.json .

```
{ "lib" : [ "WebWorker" ] }
```

Imports will break type augmentation

If the ImportMetaEnv augmentation does not work, make sure you do not have any import statements in vite-env.d.ts . See the TypeScript documentation for more information.

## HTML Constant Replacement

Vite also supports replacing constants in HTML files. Any properties in import.meta.env can be used in HTML files with a special %CONST_NAME% syntax:

```
< h1 >Vite is running in %MODE%</ h1 > < p >Using data from %VITE_API_URL%</ p >
```

If the env doesn't exist in import.meta.env , e.g. %NON_EXISTENT% , it will be ignored and not replaced, unlike import.meta.env.NON_EXISTENT in JS where it's replaced as undefined .

Given that Vite is used by many frameworks, it is intentionally unopinionated about complex replacements like conditionals. Vite can be extended using an existing userland plugin or a custom plugin that implements the transformIndexHtml hook .

By default, the dev server ( dev command) runs in development mode and the build command runs in production mode.

This means when running vite build , it will load the env variables from .env.production if there is one:

```
VITE_APP_TITLE=My App
```

In your app, you can render the title using import.meta.env.VITE_APP_TITLE .

In some cases, you may want to run vite build with a different mode to render a different title. You can overwrite the default mode used for a command by passing the --mode option flag. For example, if you want to build your app for a staging mode:

```
vite build --mode staging
```

And create a .env.staging file:

```
VITE_APP_TITLE=My App (staging)
```

As vite build runs a production build by default, you can also change this and run a development build by using a different mode and .env file configuration:

```
NODE_ENV=development
```

It's important to note that NODE_ENV ( process.env.NODE_ENV ) and modes are two different concepts. Here's how different commands affect the NODE_ENV and mode:

The different values of NODE_ENV and mode also reflect on its corresponding import.meta.env properties:

NODE_ENV in .env files

NODE_ENV=... can be set in the command, and also in your .env file. If NODE_ENV is specified in a .env.[mode] file, the mode can be used to control its value. However, both NODE_ENV and modes remain as two different concepts.

The main benefit with NODE_ENV=... in the command is that it allows Vite to detect the value early. It also allows you to read process.env.NODE_ENV in your Vite config as Vite can only load the env files once the config is evaluated.
