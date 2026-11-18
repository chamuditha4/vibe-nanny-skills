# Previewing and capturing an Expo / React Native app on web

A web build is the fastest way to *see* a redesign and to capture real screens
for store screenshots. Everything here is temporary: install without saving,
mark every edited line, and revert before finishing.

## 1. Dependencies without touching package files

```bash
cp package.json package-lock.json "$SCRATCH"/   # safety copies
npm install --no-save --no-audit --no-fund react-native-web@<sdk-matched> @expo/metro-runtime@<sdk-matched>
git status --short package.json package-lock.json   # must print nothing
```

Use the versions Expo expects for the SDK (`npx expo install --check` shows them; don't let it write).

Playwright: install `playwright-core` in a scratch folder (`npm i playwright-core`) and point `PLAYWRIGHT_CORE` at it. Use system Chrome if present.

## 2. Temporary stubs (mark with `PREVIEW-TEMP` / `SCREENSHOT-TEMP`)

| Problem on web | Temporary fix |
|---|---|
| `react-native-google-mobile-ads` imports `codegenNativeComponent` | `src/ads/<module>.web.ts` exporting no-op functions with the same names |
| `expo-sqlite` cannot resolve `wa-sqlite.wasm` | root `metro.config.js` adding `wasm` to `resolver.assetExts` and COOP/COEP headers (below) |
| Pro-gated screens redirect to paywall | early `return <>{children}</>` in the gate component |
| Store returns a test price (e.g. $99.99) | override the displayed price in the purchases provider / promo hook |
| Screenshot needs the spec's example date | set the calculator's initial state to that date |
| Purchase-availability notes ("use a dev build") | force the availability flag true |

```js
// metro.config.js — PREVIEW-TEMP
const { getDefaultConfig } = require('expo/metro-config');
const config = getDefaultConfig(__dirname);
config.resolver.assetExts.push('wasm');
config.server.enhanceMiddleware = (middleware) => (req, res, next) => {
  res.setHeader('Cross-Origin-Embedder-Policy', 'credentialless');
  res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
  return middleware(req, res, next);
};
module.exports = config;
```

Before patching, confirm the files have no uncommitted changes, so that `git checkout -- <files>` restores them exactly.

## 3. Running the server safely

- Start on a dedicated port: `CI=1 npx expo start --web --port 8090 --clear` (background). `CI=1` makes Expo non-interactive. If the port is taken it exits with "Input is required" — pick another port rather than killing processes.
- **The user may be running their own `expo start`.** Never kill processes by a pattern like `pkill -f "expo start"`. That can hit their server, and even your own shell (exit 144). Kill only the PID that is listening on *your* port (`ps -o pid,lstart,args`).
- While temporary patches exist, the user's dev server hot-reloads them onto connected devices. Keep the patch window short, and tell them to reload afterwards.
- A server started earlier can keep serving a stale bundle. If the patches don't show up, restart the server on a new port with `--clear`.
- Wait for readiness with a curl loop until you get `200`. A `500` means a bundling error, so grep the log for `Metro error`.

## 4. Capture gotchas

- `page.goto` reloads the app. First-launch flags that load asynchronously (e.g. "welcome seen") can re-show onboarding, so use `dismissAfterGoto`.
- React Native Web scroll views are nested `div`s. `capture_screens.cjs` scrolls the nearest scrollable ancestor to a text anchor; don't rely on `fullPage` screenshots.
- RN web doesn't expose every control with an ARIA role. Prefer `clickExact` on the visible label over `getByRole`.
- Seed history/favorites by really saving results in the same browser context; each new Playwright context starts with empty storage.
- Switching `colorScheme` live can leave some text colors stale on web. Capture dark screens after a fresh navigation, and check the result.
- Capture at viewport height = device height − 47 pt (status bar) and scale 3. The composer adds the status bar, Dynamic Island and home indicator.

## 5. Cleanup (always)

```bash
git checkout -- <every patched file>
rm -f metro.config.js src/ads/*.web.ts         # only the temp files you created
kill <your server pid>
grep -rn "SCREENSHOT-TEMP\|PREVIEW-TEMP" app src   # must print nothing
git status --short                                  # only intended changes
```

`react-native-web` stays in `node_modules` only (not saved). Mention it, and suggest `npm ci` if the user wants a pristine tree.
