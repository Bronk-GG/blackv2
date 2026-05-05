import os
import sys
import time
import asyncio
import aiohttp
from rich.console import Console

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
)

from ..utils.http_client import do_async_request
from ..utils.log import logError

async def checkIP(ip, session, config):
    url = f"http://ip-api.com/json/{ip}"
    
    returnData = {
        "ip": ip,
        "status": "NONE",
        "data": None
    }
    
    try:
        response = await do_async_request("GET", url, session, config)
        if response and response.get("status_code") == 200:
            json_data = response.get("json", {})
            if json_data and json_data.get("status") == "success":
                returnData["status"] = "FOUND"
                returnData["data"] = json_data
                
                # Format output nicely
                config.console.print(f"  ✔️  \\[[cyan1]IP Tracker[/cyan1]] [bright_white]{ip}[/bright_white]")
                config.console.print(f"      [green]Country:[/green] {json_data.get('country')} ({json_data.get('countryCode')})")
                config.console.print(f"      [green]Region:[/green] {json_data.get('regionName')} ({json_data.get('city')})")
                config.console.print(f"      [green]ISP:[/green] {json_data.get('isp')}")
                config.console.print(f"      [green]Organization:[/green] {json_data.get('org')}")
                config.console.print(f"      [green]ASN:[/green] {json_data.get('as')}")
                
            else:
                returnData["status"] = "NOT-FOUND"
                if config.verbose:
                    config.console.print(f"  ❌ [[blue]IP Tracker[/blue]] [bright_white]{ip}[/bright_white] - Invalid IP or reserved range")
        else:
            returnData["status"] = "ERROR"
            
    except Exception as e:
        logError(e, f"Couldn't check IP {ip}", config)
        
    return returnData

async def fetchResults(ips, config):
    async with aiohttp.ClientSession() as session:
        tasks = [checkIP(ip, session, config) for ip in ips]
        results = await asyncio.gather(*tasks)
        return results

def verifyIP(ips, config):
    if isinstance(ips, str):
        ips = [ips]
        
    start_time = time.time()
    config.console.print(f"🛰️  Tracking {len(ips)} IP address(es)...")
    
    results = asyncio.run(fetchResults(ips, config))
    
    end_time = time.time()
    config.console.print(
        f":chequered_flag: Check completed in {round(end_time - start_time, 1)} seconds"
    )
    
    found_ips = [r for r in results if r["status"] == "FOUND"]
    
    if len(found_ips) <= 0:
        config.console.print("⭕ No IP information was found")
        
    return found_ips
