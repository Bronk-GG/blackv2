# -*- mode: python ; coding: utf-8 -*-
import os
import playwright

# Resolve Playwright driver path relative to the playwright package itself.
# This works regardless of whether playwright is installed globally or per-user.
PLAYWRIGHT_DRIVER_PATH = os.path.join(os.path.dirname(playwright.__file__), 'driver')

a = Analysis(
    ['blackbird.py'],
    pathex=['.', 'src'],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('assets', 'assets'),
        # Bundle Playwright's node.js driver so the compiled exe can auto-install Chromium on first run.
        # Chromium itself (~150MB) is NOT bundled to keep the exe small.
        # It will be downloaded once to %LOCALAPPDATA%\ms-playwright at first launch.
        (PLAYWRIGHT_DRIVER_PATH, 'playwright/driver'),
    ],
    hiddenimports=[
        'modules.whatsmyname',
        'modules.core',
        'modules.utils',
        'modules.export',
        'modules.ai',
        'modules.sites',
        'modules.utils.hash',
        'modules.utils',
        'modules.whatsmyname.list_operations',
        'modules.core.username',
        'modules.core.email',
        'modules.export.csv',
        'modules.export.file_operations',
        'modules.export.json',
        'modules.export.pdf',
        'modules.core.ip',
        'modules.utils.file_operations',
        'modules.utils.permute',
        # Playwright hidden imports
        'playwright',
        'playwright.async_api',
        'playwright._impl._driver',
        'playwright._impl._transport',
        'playwright._impl._connection',
        'playwright._impl._browser',
        'playwright._impl._browser_context',
        'playwright._impl._page',
        # BeautifulSoup
        'bs4',
        'bs4.builder',
        'bs4.builder._html5lib',
        'bs4.builder._htmlparser',
        'bs4.builder._lxml',
        'soupsieve',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='blackbird',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
