# 🎮 exFAT Image Builder

**The Ultimate Windows Toolkit for Building, Editing & Backporting PS5
Game Images**

Build • Edit • Convert • Backport • Deploy

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-blue)
![Python](https://img.shields.io/badge/Python-3.14-yellow)
![License](https://img.shields.io/github/license/kerrdec97/ps5-exfat-builder)
![Release](https://img.shields.io/github/v/release/kerrdec97/ps5-exfat-builder)
![Downloads](https://img.shields.io/github/downloads/kerrdec97/ps5-exfat-builder/total)


------------------------------------------------------------------------

## 🚀 Overview

**exFAT Image Builder** is an all-in-one Windows application for
creating, editing, converting and managing mountable PS5 game images
from your own game dumps.

Whether you're building an **exFAT image**, generating a **compressed
FFPFSC**, creating an **FFPKG**, applying **backports**, managing
**DLC**, or transferring directly to your PS5, everything is available
from one modern interface.

Designed for speed, reliability and ease of use.

> ⚠️ **Homebrew & Personal Backup Tool**
>
> This software is intended only for games and content **you legally own
> and have dumped yourself**.
>
> It **does not** download games, decrypt retail packages, bypass DRM or
> provide copyrighted content.

------------------------------------------------------------------------

# ✨ Features

## 📦 Image Builder

-   ✅ Build exFAT Images
-   ✅ Build FFPKG (UFS2)
-   ✅ Build Compressed FFPFSC Images
-   ✅ Automatic Image Verification
-   ✅ Queue Multiple Builds
-   ✅ Automatic Game Detection

## 🛠 Image Editor

-   Replace Files
-   Add Files
-   Delete Files
-   Rebuild without recreating the entire image

## 🔥 Backport Toolkit

-   Auto Backport
-   SDK Detection
-   Fakelib Support
-   DLC Support
-   Language Stripper
-   Automatic AMPR Generation
-   Restore Original Files

## 🎮 PS5 Integration

-   FTP Browser
-   Remote Content Manager
-   Payload Sender
-   Live Kernel Log Viewer
-   Console Diagnostics
-   Direct PS5 Deployment

## 📚 Library

-   Automatic Cover Art
-   Metadata Detection
-   Bulk Rename
-   Batch Queue
-   Format Conversion
-   Game Browser

## 🌍 Languages

Supports **17 interface languages**, maintained by the community.

------------------------------------------------------------------------

# 📸 Screenshots

> Add screenshots of the Build, Backports, Library, FTP and Console
> Tools tabs here.

------------------------------------------------------------------------

# ⚡ Quick Start

1.  Install Windows 10/11, Python 3.14, uv, OSFMount and (.NET 8 for FFPKG).
2.  Sync the project environment:

    ```powershell
    uv sync
    ```

3.  Run the application:

    ```powershell
    uv run python exfat_builder.py
    ```

4.  Open the **Build** tab.
5.  Select your PS5 game dump.
6.  Choose **exFAT**, **FFPKG** or **FFPFSC**.
7.  Click **Add to Queue** then **Build All**.
8.  Wait for Scan → Build → Copy → Verify to complete.

------------------------------------------------------------------------

# Developer Setup

This repository is configured for **Python 3.14** and **uv**.

Create or refresh the local environment:

```powershell
uv sync
```

Run the GUI from source:

```powershell
uv run python exfat_builder.py
```

Run through the package entrypoint:

```powershell
uv run ps5-exfat-builder
```

Inspect or run AMPR routes from the core CLI:

```powershell
uv run ps5-exfat-builder-core ampr-dry-run --source game --target out.ampr --tool C:\Tools\Lazy_AMPR --performance-preset max
uv run ps5-exfat-builder-core ampr-convert --source game --target out.ampr --tool C:\Tools\Lazy_AMPR --performance-preset max --worker-count 16
```

Build the Windows executable:

```powershell
uv sync --group build
.\build.bat
```

Architecture notes for adding new formats live in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

------------------------------------------------------------------------

# 📦 Supported Formats

  Format     Description
  ---------- --------------------------
  📀 exFAT   Standard mountable image
  📦 FFPKG   UFS2 Image
  🗜 FFPFSC   Compressed PFS Image

------------------------------------------------------------------------

# ⭐ Why exFAT Image Builder?

-   Modern Windows Interface
-   Multiple Image Formats
-   Integrated Backport Engine
-   Automatic Metadata Detection
-   Built-in FTP Client
-   Queue System
-   Live Kernel Logs
-   DLC Support
-   Active Development

------------------------------------------------------------------------

# ❤️ Credits

Thanks to everyone in the PS5 Homebrew community, especially:

-   Nazky
-   BestPig
-   SvenGDK
-   drakmor
-   PSBrew
-   john-tornblom
-   ps5-payload-dev
-   idlesauce
-   NookieAI
-   stonemodder

See **THIRD_PARTY_NOTICES.md** for full licensing information.

------------------------------------------------------------------------

# ⚠ Disclaimer

This software is intended only for content you legally own.

It is **not affiliated with or endorsed by Sony Interactive
Entertainment**.

Use at your own risk.

------------------------------------------------------------------------

# ⭐ Support the Project

If you enjoy exFAT Image Builder:

-   ⭐ Star the repository
-   🐞 Report bugs
-   💡 Suggest features
-   ❤️ Support the PS5 Homebrew community

Made with ☕ and a passion for PS5 homebrew.


