import requests
import sys
import os
import chardet
import aiohttp
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from modules.utils.log import logError

requests.packages.urllib3.disable_warnings()


# Perform a Sync Request and return response details
def do_sync_request(method, url, config, data=None, customHeaders=None, cookies=None):
    headers = {"User-Agent": config.userAgent}
    if customHeaders:
        headers.update(customHeaders)
    # Only set proxies parameter if actually needed to avoid performance overhead
    request_kwargs = {
        "method": method,
        "url": url,
        "timeout": config.timeout,
        "verify": False,
        "headers": headers,
        "data": data,
        "cookies": cookies,
    }
    
    # Only add proxies parameter if a proxy is actually configured
    if config.proxy:
        request_kwargs["proxies"] = {"http": config.proxy, "https": config.proxy}
    try:
        response = requests.request(**request_kwargs)
        if config.verbose:
            config.console.print(
                f"  🆗 Sync HTTP Request completed [{method} - {response.status_code}] {url}"
            )
        return response
    except Exception as e:
        if config.verbose:
            config.console.print(f"  ❌ Error in Sync HTTP Request [{method}] {url}")
        logError(e, f"Error in Sync HTTP Request [{method}] {url}", config)
        return None


# Perform an Async Request and return response details
async def do_async_request(method, url, session, config, data=None, customHeaders=None):
    headers = {"User-Agent": config.userAgent}
    if customHeaders:
        headers.update(customHeaders)
    proxy = config.proxy if config.proxy else None
    try:
        # aiohttp.ClientTimeout required in aiohttp >= 3.x (plain int is not accepted)
        timeout = aiohttp.ClientTimeout(total=config.timeout)

        request_kwargs = dict(
            method=method,
            url=url,
            proxy=proxy,
            timeout=timeout,
            allow_redirects=True,
            ssl=False,
            data=data,
            headers=headers,
        )
        # max_redirects was added in aiohttp 3.10.11 — skip on older installs
        try:
            import aiohttp as _aio
            _ver = tuple(int(x) for x in _aio.__version__.split('.')[:3])
            if _ver >= (3, 10, 11):
                request_kwargs['max_redirects'] = 10
        except Exception:
            pass

        response = await session.request(**request_kwargs)

        json = None
        try:
            content = await response.text()
        except:
            binaryContent = await response.read()
            encode = chardet.detect(binaryContent)["encoding"]
            content = binaryContent.decode(encode)

        if "Content-Type" in response.headers:
            if "application/json" in response.headers["Content-Type"]:
                json = await response.json()

        responseData = {
            "url": url,
            "status_code": response.status,
            "headers": response.headers,
            "content": content,
            "json": json,
        }

        if config.verbose:
            config.console.print(
                f"  🆗 Async HTTP Request completed [{method} - {response.status}] {url}"
            )
        return responseData
    except Exception as e:
        if config.verbose:
            config.console.print(f"  ❌ Error in Async HTTP Request [{method}] {url}")
        logError(
            e,
            f"Error in Async HTTP Request [{method}] {url} | {type(e).__name__}: {e}",
            config,
        )
        return None
