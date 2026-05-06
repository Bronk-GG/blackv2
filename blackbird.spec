# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import importlib.util
import site as _site
import playwright
from PyInstaller.utils.hooks import collect_all, collect_submodules

# ── Playwright driver ────────────────────────────────────────────────────────
PLAYWRIGHT_DRIVER_PATH = os.path.join(os.path.dirname(playwright.__file__), 'driver')

# ── Locate every site-packages directory this Python knows about ─────────────
# This is the root cause fix: rich is in user site-packages which PyInstaller
# sometimes misses. Adding all site-packages dirs to pathex guarantees it finds them.
_site_dirs = []
try:
    _site_dirs += _site.getsitepackages()
except AttributeError:
    pass
try:
    _user_site = _site.getusersitepackages()
    if _user_site not in _site_dirs:
        _site_dirs.append(_user_site)
except AttributeError:
    pass

# ── Directly copy pure-Python packages as datas ──────────────────────────────
# Belt-and-suspenders: physically copies the .py files into _MEIPASS/<pkg>
# so the frozen exe can import them regardless of hook or hiddenimport behaviour.
def _find_pkg_dir(name):
    try:
        spec = importlib.util.find_spec(name)
        if spec and spec.submodule_search_locations:
            return list(spec.submodule_search_locations)[0]
    except Exception:
        pass
    return None

_pure_python_pkgs = [
    'rich',              # terminal formatting  (pure Python)
    'bs4',               # BeautifulSoup        (pure Python)
    'soupsieve',         # CSS selector engine  (pure Python)
    'dotenv',            # python-dotenv        (pure Python)
    'markdown_it',       # required by rich     (pure Python)
    'mdurl',             # required by rich     (pure Python)
    'pygments',          # required by rich     (pure Python)
    'certifi',           # SSL certs            (pure Python)
    'charset_normalizer',# requests dep         (pure Python)
    'requests',          # HTTP library         (pure Python)
    'urllib3',           # requests dep         (pure Python)
    'idna',              # requests dep         (pure Python)
    'chardet',           # charset detection    (pure Python)
]

_direct_datas = []
for _pkg in _pure_python_pkgs:
    _dir = _find_pkg_dir(_pkg)
    if _dir and os.path.isdir(_dir):
        _direct_datas.append((_dir, _pkg))

# ── collect_all for packages with compiled C extensions ──────────────────────
_datas    = []
_binaries = []
_hidden   = []

for _pkg in ['aiohttp', 'playwright']:
    try:
        _d, _b, _h = collect_all(_pkg)
        _datas    += _d
        _binaries += _b
        _hidden   += _h
    except Exception:
        pass

_hidden += collect_submodules('aiohttp')
_hidden += collect_submodules('playwright')
_hidden += collect_submodules('rich')
_hidden += collect_submodules('bs4')

# ── Analysis ─────────────────────────────────────────────────────────────────
a = Analysis(
    ['blackbird.py'],
    pathex=['.', 'src'] + _site_dirs,
    binaries=_binaries,
    datas=_direct_datas + _datas + [
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
        # ── Rich internals ────────────────────────────────────────────────
        'rich',
        'rich.console',
        'rich.live',
        'rich.text',
        'rich.panel',
        'rich.table',
        'rich.progress',
        'rich.markup',
        'rich.highlighter',
        'rich.theme',
        'rich.style',
        'rich.segment',
        'rich.measure',
        'rich.pretty',
        'rich.syntax',
        'rich.traceback',
        'rich.logging',
        'rich.group',
        # ── Playwright internals ──────────────────────────────────────────
        'playwright._impl._driver',
        'playwright._impl._transport',
        'playwright._impl._connection',
        'playwright._impl._browser',
        'playwright._impl._browser_context',
        'playwright._impl._page',
        # ── BeautifulSoup parsers ─────────────────────────────────────────
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
