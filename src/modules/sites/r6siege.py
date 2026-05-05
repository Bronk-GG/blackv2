import sys
import os
import asyncio
import random

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)

# Global or local import of playwright
try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

# Custom logError to handle both packaged and standalone execution
try:
    from utils.log import logError
except ImportError:
    try:
        from ..utils.log import logError
    except ImportError:
        def logError(e, msg, config=None):
            if config and hasattr(config, 'console'):
                config.console.print(f"[red]{msg}: {e}[/red]")
            else:
                print(f"ERROR: {msg}: {e}")

# Platforms to search on Tracker Network
PLATFORMS = [
    ("uplay", "pc"),
    ("xbl", "xbox"),
    ("psn", "psn"),
]

async def handle_consent(page, config):
    """Handle cookie consent overlays that can block content."""
    try:
        selectors = [
            "button:has-text('Akzeptieren')", 
            "button:has-text('Accept')", 
            "button:has-text('Agree')", 
            "button:has-text('Allow All')",
            "button:has-text('Alle akzeptieren')",
            "#L2AGLb", # Google Agree
            "button[name='agree']", # Yahoo/AOL
            "button.accept-all"
        ]
        for sel in selectors:
            btn = page.locator(sel)
            if await btn.count() > 0:
                if config and config.verbose:
                    config.console.print("    [dim]Dismissing cookie consent...[/dim]")
                await btn.first.click()
                await page.wait_for_timeout(2000)
                return True
        for frame in page.frames:
            for sel in selectors:
                try:
                    btn = frame.locator(sel)
                    if await btn.count() > 0:
                        if config and config.verbose:
                            config.console.print("    [dim]Dismissing cookie consent (iframe)...[/dim]")
                        await btn.first.click()
                        await page.wait_for_timeout(2000)
                        return True
                except:
                    continue
    except Exception:
        pass
    return False

async def get_r6_stats(username, session, config):
    """Fetch R6 Siege stats for a username via Tracker Network using Playwright."""

    if not async_playwright:
        if config and config.verbose:
            config.console.print("  [yellow]⚠️ [R6 Siege] Playwright not installed.[/yellow]")
        return []
    
    if getattr(sys, 'frozen', False):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "ms-playwright")

    results = []

    try:
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
            except Exception:
                import subprocess
                from playwright._impl._driver import compute_driver_executable, get_driver_env
                try:
                    driver_exec = compute_driver_executable()
                    subprocess.run([driver_exec[0], driver_exec[1], "install", "chromium"], env=get_driver_env(), check=True)
                    browser = await p.chromium.launch(headless=True)
                except Exception:
                    return []
                
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                locale="en-US,en;q=0.9",
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1
            )
            
            # Advanced Stealth Script
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                const getParameter = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type) {
                    const context = getParameter.apply(this, arguments);
                    if (type === 'webgl' || type === 'experimental-webgl') {
                        const originalGetParameter = context.getParameter;
                        context.getParameter = function(parameter) {
                            if (parameter === 37445) return 'Intel Inc.';
                            if (parameter === 37446) return 'Intel(R) Iris(TM) Plus Graphics 640';
                            return originalGetParameter.apply(this, arguments);
                        };
                    }
                    return context;
                };
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({ query: async () => ({ state: 'granted' }) })
                });
            """)
            
            page = await context.new_page()

            for platform_tracker, platform_label in PLATFORMS:
                domains = ["https://tracker.gg", "https://r6.tracker.network"]
                found_for_platform = False
                
                for domain in domains:
                    if found_for_platform: break
                    url = f"{domain}/r6siege/profile/{platform_tracker}/{username}/overview"
                    
                    try:
                        if config and config.verbose:
                            config.console.print(f"    [dim]Checking {platform_label} via {domain}...[/dim]")
                        
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                        await page.goto(f"{domain}/r6siege", wait_until="domcontentloaded", timeout=30000)
                        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                        
                        # Cloudflare Wait
                        for _ in range(4):
                            content = await page.content()
                            if any(x in content for x in ["Verify you are human", "Checking your browser", "cloudflare"]):
                                if config and config.verbose:
                                    config.console.print("    [dim]Cloudflare detected, waiting...[/dim]")
                                await page.wait_for_timeout(5000)
                            else:
                                break
                                
                        await handle_consent(page, config)
                        content = await page.content()
                        is_error = any(x in content for x in ["Player Not Found", "We could not find the player", "404 - Not Found", "Network Error", "Server Error"])
                        
                        if is_error and platform_tracker in ["xbl", "psn"]:
                            # Discovery search
                            search_url = f"{domain}/r6siege/search/{platform_tracker}/{username}"
                            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                            await page.wait_for_timeout(6000)
                            await handle_consent(page, config)
                            
                            if "profile" in page.url and not any(x in await page.content() for x in ["Player Not Found", "We could not find the player"]):
                                url = page.url
                            else:
                                # Parse search result
                                links = page.locator("a[href*='/profile/']")
                                found_href = None
                                count = await links.count()
                                for i in range(count):
                                    href = await links.nth(i).get_attribute("href")
                                    if href and "/profile/" in href and (platform_tracker in href or platform_label in href):
                                        found_href = href
                                        break
                                if found_href:
                                    url = f"{domain}{found_href}" if found_href.startswith("/") else found_href
                                    await page.goto(url, wait_until="domcontentloaded")
                                    await page.wait_for_timeout(6000)
                                else:
                                    continue
                        elif is_error:
                            continue
                            
                        stats_dict = {}
                        async def extract_stat(label):
                            patterns = [
                                f"div.trn-defstat:has(div.trn-defstat__name:has-text('{label}')) div.trn-defstat__value",
                                f"div.stat:has(div.name:has-text('{label}')) div.value",
                                f"div.stat-item:has(div.stat-label:has-text('{label}')) div.stat-value",
                                f".stat:has(.name:has-text('{label}')) .value",
                                f".stat-row:has(.label:has-text('{label}')) .value",
                                f"div:has-text('{label}') + div"
                            ]
                            for pattern in patterns:
                                try:
                                    locator = page.locator(pattern).first
                                    if await locator.count() > 0:
                                        val = (await locator.inner_text(timeout=1000)).strip()
                                        if val and val != "0" and val != "--":
                                            return val
                                except:
                                    pass
                            return "0"

                        for label in ["K/D", "Kills", "Deaths", "Matches", "Wins", "Losses", "HS %", "Headshot %"]:
                            stats_dict[label] = await extract_stat(label)

                        try:
                            view_all_btn = page.locator("button:has-text('View All Stats')")
                            if await view_all_btn.count() > 0:
                                await view_all_btn.first.click(timeout=3000)
                                await page.wait_for_timeout(3000)
                                for label in ["Time Played", "Rank", "Matches Played"]:
                                    stats_dict[label] = await extract_stat(label)
                        except:
                            pass
                        
                        kd, kills = stats_dict.get("K/D", "0"), stats_dict.get("Kills", "0")
                        matches = stats_dict.get("Matches Played") or stats_dict.get("Matches", "0")
                        hs_pct = stats_dict.get("HS %") or stats_dict.get("Headshot %", "N/A")

                        if all(v in ["0", "N/A"] for v in [kd, kills, matches]):
                            if config and config.verbose:
                                await page.screenshot(path=f"verify_{platform_tracker}_{username}.png")
                            continue
                        
                        if config and hasattr(config, 'console'):
                            config.console.print(rf"  ✔️  \[[cyan1]R6 Siege ({platform_label.upper()})[/cyan1]] [bright_white]{url}[/bright_white]")
                            config.console.print(f"      ➡️  K/D: {kd} | Kills: {kills} | Matches: {matches}")
                        
                        results.append({
                            "name": f"R6 Siege ({platform_label.upper()})",
                            "status": "FOUND", "url": url, "category": "Gaming",
                            "metadata": [
                                {"name": "Platform", "value": platform_label.upper()},
                                {"name": "K/D", "value": kd},
                                {"name": "Headshot %", "value": hs_pct},
                                {"name": "Kills", "value": kills},
                                {"name": "Deaths", "value": stats_dict.get("Deaths", "0")},
                                {"name": "Matches Played", "value": matches},
                                {"name": "Wins", "value": stats_dict.get("Wins", "0")},
                                {"name": "Losses", "value": stats_dict.get("Losses", "0")},
                                {"name": "Playtime", "value": stats_dict.get("Time Played", "N/A")},
                            ],
                        })
                        found_for_platform = True
                        
                    except Exception as inner_e:
                        if config and config.verbose:
                            logError(inner_e, f"[R6 Siege] Error fetching on {domain}", config)
                        continue
                
                # Search Engine Fallback (Google) if direct domains failed
                if not found_for_platform:
                    try:
                        if config and config.verbose:
                            config.console.print(f"    [dim]Direct access failed for {platform_label}. Trying search engine fallback (Yahoo/AOL)...[/dim]")
                        
                        search_query = f'"{username}" site:r6.tracker.network {platform_label}'
                        # Yahoo search often bypasses some bot detection that Google/DDG have
                        yahoo_url = f"https://search.yahoo.com/search?p={search_query.replace(' ', '+')}"
                        
                        await page.goto(yahoo_url, wait_until="domcontentloaded", timeout=30000)
                        await handle_consent(page, config)
                        await page.wait_for_timeout(5000)
                        
                        if config and config.verbose:
                            await page.screenshot(path=f"search_fallback_{username}_{platform_label}.png")
                        
                        # Look for snippets in Yahoo results
                        snippets = page.locator("div.compText, .algo-snippet, .st")
                        count = await snippets.count()
                        
                        # If Yahoo fails, try AOL (often a mirror of Bing but different thresholds)
                        if count == 0:
                            if config and config.verbose:
                                config.console.print(f"    [dim]Yahoo failed, trying AOL...[/dim]")
                            aol_url = f"https://search.aol.com/aol/search?q={search_query.replace(' ', '+')}"
                            await page.goto(aol_url, wait_until="domcontentloaded", timeout=30000)
                            await handle_consent(page, config)
                            await page.wait_for_timeout(5000)
                            snippets = page.locator("p.lh-20, .algo-snippet")
                            count = await snippets.count()

                        for i in range(count):
                            text = await snippets.nth(i).inner_text()
                            if "K/D" in text:
                                import re
                                # Flexibly match K/D and other stats with various delimiters (. , : ·)
                                kd_match = re.search(r"K/D[:\s\·\.]*([\d\.,]+)", text)
                                kills_match = re.search(r"Kills[:\s\·\.]*([\d\.,]+)", text)
                                matches_match = re.search(r"Matches Played[:\s\·\.]*([\d\.,]+)", text) or re.search(r"Matches[:\s\·\.]*([\d\.,]+)", text)
                                
                                if kd_match:
                                    kd = kd_match.group(1).replace(",", ".")
                                    kills = kills_match.group(1) if kills_match else "N/A"
                                    matches = matches_match.group(1) if matches_match else "N/A"
                                    
                                    if config and hasattr(config, 'console'):
                                        config.console.print(rf"  [R6 Siege ({platform_label.upper()})] [yellow](Snippet Result)[/yellow]")
                                        config.console.print(f"      -> K/D: {kd} | Kills: {kills} | Matches: {matches}")
                                    
                                    results.append({
                                        "name": f"R6 Siege ({platform_label.upper()})",
                                        "status": "FOUND", "url": "Search Fragment", "category": "Gaming",
                                        "metadata": [
                                            {"name": "Platform", "value": platform_label.upper()},
                                            {"name": "K/D", "value": kd},
                                            {"name": "Kills", "value": kills},
                                            {"name": "Matches Played", "value": matches},
                                            {"name": "Source", "value": "Search Engine Snapshot"},
                                        ],
                                    })
                                    found_for_platform = True
                                    break
                    except Exception as e:
                        if config and config.verbose:
                            logError(e, f"[R6 Siege] Search engine fallback failed for {username}", config)

            await browser.close()
    except Exception as e:
        if config and config.verbose:
            logError(e, "[R6 Siege] Playwright execution failed", config)

    return results
