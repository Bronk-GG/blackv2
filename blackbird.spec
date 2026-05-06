# -*- mode: python ; coding: utf-8 -*-
import os
import playwright
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# ── Playwright driver ────────────────────────────────────────────────────────
PLAYWRIGHT_DRIVER_PATH = os.path.join(os.path.dirname(playwright.__file__), 'driver')

# ── Collect third-party packages (data + binaries + submodules) ──────────────
# collect_all() is the correct way to ensure nothing is silently missed.
_packages = ['rich', 'aiohttp', 'dotenv', 'bs4', 'soupsieve', 'playwright']

_datas    = []
_binaries = []
_hidden   = []

for _pkg in _packages:
    _d, _b, _h = collect_all(_pkg)
    _datas    += _d
    _binaries += _b
    _hidden   += _h

# Extra submodules that collect_all may not walk into
_hidden += collect_submodules('aiohttp')
_hidden += collect_submodules('rich')
_hidden += collect_submodules('bs4')
_hidden += collect_submodules('playwright')

# ── Analysis ─────────────────────────────────────────────────────────────────
a = Analysis(
    ['blackbird.py'],
    pathex=['.', 'src'],
    binaries=_binaries,
    datas=_datas + [
        ('data', 'data'),
        ('assets', 'assets'),
        (PLAYWRIGHT_DRIVER_PATH, 'playwright/driver'),
    ],
    hiddenimports=_hidden + [
        # ── Local project packages ────────────────────────────────────────
        'config',
        'modules',
        'modules.whatsmyname',
        'modules.whatsmyname.list_operations',
        'modules.core',
        'modules.core.username',
        'modules.core.email',
        'modules.core.ip',
        'modules.utils',
        'modules.utils.hash',
        'modules.utils.file_operations',
        'modules.utils.permute',
        'modules.utils.filter',
        'modules.utils.parse',
        'modules.utils.http_client',
        'modules.utils.log',
        'modules.utils.input',
        'modules.utils.precheck',
        'modules.utils.userAgent',
        'modules.export',
        'modules.export.csv',
        'modules.export.file_operations',
        'modules.export.json',
        'modules.export.pdf',
        'modules.export.dump',
        'modules.sites',
        'modules.sites.instagram',
        'modules.sites.r6siege',
        'modules.ai',
        'modules.ai.client',
        'modules.ai.key_manager',
        # ── Playwright internals ──────────────────────────────────────────
        'playwright._impl._driver',
        'playwright._impl._transport',
        'playwright._impl._connection',
        'playwright._impl._browser',
        'playwright._impl._browser_context',
        'playwright._impl._page',
        # ── BeautifulSoup parsers ─────────────────────────────────────────
        'bs4.builder._html5lib',
        'bs4.builder._htmlparser',
        'bs4.builder._lxml',
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
