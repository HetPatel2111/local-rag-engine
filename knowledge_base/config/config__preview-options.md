---
url: "https://vite.dev/config/preview-options"
title: "Preview Options"
created_at: "2026-05-26T05:14:58.728381+00:00"
---
# Preview Options

Unless noted, the options in this section are only applied to preview.

- Type: string | boolean
- Default: server.host

Specify which IP addresses the server should listen on. Set this to 0.0.0.0 or true to listen on all addresses, including LAN and public addresses.

This can be set via the CLI using --host 0.0.0.0 or --host .

There are cases when other servers might respond instead of Vite. See server.host for more details.

## preview.allowedHosts

- Type: string[] | true
- Default: server.allowedHosts

The hostnames that Vite is allowed to respond to.

See server.allowedHosts for more details.

- Type: number
- Default: 4173

Specify server port. Note if the port is already being used, Vite will automatically try the next available port so this may not be the actual port the server ends up listening on.

```
export default defineConfig ({ server: { port: 3030 , }, preview: { port: 8080 , }, })
```

- Type: boolean
- Default: server.strictPort

Set to true to exit if port is already in use, instead of automatically trying the next available port.

- Type: https.ServerOptions
- Default: server.https

Enable TLS + HTTP/2.

See server.https for more details.

- Type: boolean | string
- Default: server.open

Automatically open the app in the browser on server start. When the value is a string, it will be used as the URL's pathname. If you want to open the server in a specific browser you like, you can set the env process.env.BROWSER (e.g. firefox ). You can also set process.env.BROWSER_ARGS to pass additional arguments (e.g. --incognito ).

BROWSER and BROWSER_ARGS are also special environment variables you can set in the .env file to configure it. See the open package for more details.

- Type: Record<string, string | ProxyOptions>
- Default: server.proxy

Configure custom proxy rules for the preview server. Expects an object of { key: options } pairs. If the key starts with ^ , it will be interpreted as a RegExp . The configure option can be used to access the proxy instance.

Uses http-proxy-3 . Full options here .

- Type: boolean | CorsOptions
- Default: server.cors

Configure CORS for the preview server.

See server.cors for more details.

- Type: OutgoingHttpHeaders

Specify server response headers.
