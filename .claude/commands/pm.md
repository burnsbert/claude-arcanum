---
description: Start the Arcanum Package Manager
allowed-tools: Bash
---

Start the Arcanum Package Manager. Run these steps in order:

1. Kill any existing electron-vite or Electron processes for the package manager (ignore errors if none running)
2. `cd` to the `package-manager/` directory relative to the repository root
3. If `node_modules/` doesn't exist, run `npm install`
4. If `out/renderer/index.html` doesn't exist, or any file in `src/` is newer than it, run `npx electron-vite build`
5. Launch with `nohup npx electron-vite dev > /tmp/arcanum-pm-dev.log 2>&1 &`
6. Confirm the app is running
