# ── Early log setup ─────────────────────────────────────────────────────────
# Uses stdlib ONLY so failures in third-party imports are still captured.
import os
import sys
import traceback
from datetime import datetime

def _get_exe_dir():
    """Return the directory that contains the exe (frozen) or this script (dev)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

_LOG_PATH = os.path.join(_get_exe_dir(), "blackbird_log.txt")

def _log(msg: str):
    """Append a timestamped message to blackbird_log.txt."""
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as _f:
            _f.write(msg + "\n")
    except Exception:
        pass  # never crash trying to log

def _excepthook(exc_type, exc_value, exc_tb):
    """Catch any otherwise-unhandled exception and write it to the log."""
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    _log(f"\n[UNHANDLED EXCEPTION]\n{msg}")
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _excepthook

# Write a startup marker every time the exe launches
_log(f"\n{'='*60}")
_log(f"  Blackbird started  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
_log(f"{'='*60}")

# ── Platform / encoding ──────────────────────────────────────────────────────
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# ── Path setup ───────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    basedir = sys._MEIPASS
    src_dir = os.path.join(basedir, 'src')
    sys.path.insert(0, basedir)
    sys.path.insert(0, src_dir)
else:
    basedir = os.path.dirname(__file__)
    src_dir = os.path.join(basedir, "src")
    sys.path.insert(0, src_dir)

_log(f"[PATH] basedir={basedir}")
_log(f"[PATH] src_dir={src_dir}")

# ── Third-party / project imports ────────────────────────────────────────────
try:
    import argparse
    import logging
    import random
    import time

    from rich.console import Console
    from rich.live import Live
    from rich.text import Text

    import config
    from modules.whatsmyname.list_operations import checkUpdates
    from modules.core.username import verifyUsername
    from modules.core.email import verifyEmail
    from modules.core.ip import verifyIP
    from modules.utils.userAgent import getRandomUserAgent
    from modules.export.file_operations import createSaveDirectory
    from modules.export.csv import saveToCsv
    from modules.export.pdf import saveToPdf
    from modules.export.json import saveToJson
    from modules.utils.file_operations import isFile, getLinesFromFile
    from modules.utils.permute import Permute
    from dotenv import load_dotenv

    load_dotenv()
    _log("[OK] All imports succeeded")

except Exception as _import_err:
    _log(f"\n[IMPORT ERROR]\n{traceback.format_exc()}")
    print(f"\n[STARTUP ERROR] A module failed to load. See blackbird_log.txt for details.\n{_import_err}")
    input("\nPress Enter to exit...")
    sys.exit(1)


def initiate():
    if not os.path.exists("logs/"):
        os.makedirs("logs/")
    logging.basicConfig(
        filename=config.LOG_PATH,
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        prog="blackbird",
        description="An OSINT tool to search for accounts by username in social networks.",
    )
    parser.add_argument(
        "-u",
        "--username",
        nargs="*",
        type=str,
        help="One or more usernames to search.",
    )
    parser.add_argument(
        "-uf",
        "--username-file",
        help="The list of usernames to be searched.",
    )
    parser.add_argument(
        "--ip",
        nargs="*",
        type=str,
        help="One or more IP addresses to track.",
    )
    parser.add_argument(
        "--ip-file",
        help="The list of IP addresses to track.",
    )
    parser.add_argument(
        "--permute",
        action="store_true",
        help="Permute usernames, ignoring single elements.",
    )
    parser.add_argument(
        "--permuteall", action="store_true", help="Permute usernames, all elements."
    )
    parser.add_argument(
        "-e",
        "--email",
        nargs="*",
        type=str,
        help="One or more email to search.",
    )
    parser.add_argument(
        "-ef",
        "--email-file",
        help="The list of emails to be searched.",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Generate a CSV with the results."
    )

    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Generate a PDF with the results."
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Generate a JSON with the results."
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output."
    )

    parser.add_argument(
        "-ai", "--ai",
        action="store_true",
        help="Use AI features."
    )
    parser.add_argument("--setup-ai", action="store_true", help="Configure the API key required for AI features.")
    parser.add_argument(
        "--filter",
        help='Filter sites to be searched by list property value.E.g --filter "cat=social"',
    )
    parser.add_argument(
        "--no-nsfw", action="store_true", help="Removes NSFW sites from the search."
    )
    parser.add_argument(
        "--dump", action="store_true", help="Dump HTML content for found accounts."
    )
    parser.add_argument("--proxy", help="Proxy to send HTTP requests though.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for each HTTP request (Default is 30).",
    )
    parser.add_argument(
        "--max-concurrent-requests",
        type=int,
        default=30,
        help="Specify the maximum number of concurrent requests allowed. Default is 30.",
    )
    parser.add_argument(
        "--no-update", action="store_true", help="Don't update sites lists."
    )
    parser.add_argument(
        "--about", action="store_true", help="Show about information and exit."
    )
    args = parser.parse_args()

    # Store the necessary arguments to config Object
    config.username = args.username
    config.username_file = args.username_file
    config.permute = args.permute
    config.permuteall = args.permuteall
    config.csv = args.csv
    config.pdf = args.pdf
    config.json = args.json
    config.filter = args.filter
    config.no_nsfw = args.no_nsfw
    config.dump = args.dump
    config.proxy = args.proxy
    config.verbose = args.verbose
    config.ai = args.ai
    config.setup_ai = args.setup_ai
    config.timeout = args.timeout
    config.max_concurrent_requests = args.max_concurrent_requests
    config.email = args.email
    config.email_file = args.email_file
    config.ip = args.ip
    config.ip_file = args.ip_file
    config.no_update = args.no_update
    config.about = args.about
    config.instagram_session_id = os.getenv("INSTAGRAM_SESSION_ID")
    config.api_url = os.getenv("API_URL")

    config.console = Console()

    config.dateRaw = datetime.now().strftime("%m_%d_%Y")
    config.datePretty = datetime.now().strftime("%B %d, %Y")

    config.userAgent = getRandomUserAgent(config)

    config.usernameFoundAccounts = None
    config.emailFoundAccounts = None

    config.currentUser = None
    config.currentEmail = None

    splash_path = os.path.join(basedir, "assets", "text", "splash.txt")
    lines = getLinesFromFile(splash_path)
    config.splash_line = random.choice(lines) if lines else ""


if __name__ == "__main__":
    try:
        initiate()
    except Exception as e:
        import traceback
        print("\n[STARTUP ERROR] The application failed to start:")
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
    config.console.print(
        """[red]
    ▄▄▄▄    ██▓    ▄▄▄       ▄████▄   ██ ▄█▀ ▄▄▄▄    ██▓ ██▀███  ▓█████▄ 
    ▓█████▄ ▓██▒   ▒████▄    ▒██▀ ▀█   ██▄█▒ ▓█████▄ ▓██▒▓██ ▒ ██▒▒██▀ ██▌
    ▒██▒ ▄██▒██░   ▒██  ▀█▄  ▒▓█    ▄ ▓███▄░ ▒██▒ ▄██▒██▒▓██ ░▄█ ▒░██   █▌
    ▒██░█▀  ▒██░   ░██▄▄▄▄██ ▒▓▓▄ ▄██▒▓██ █▄ ▒██░█▀  ░██░▒██▀▀█▄  ░▓█▄   ▌
    ░▓█  ▀█▓░██████▒▓█   ▓██▒▒ ▓███▀ ░▒██▒ █▄░▓█  ▀█▓░██░░██▓ ▒██▒░▒████▓ 
    ░▒▓███▀▒░ ▒░▓  ░▒▒   ▓▒█░░ ░▒ ▒  ░▒ ▒▒ ▓▒░▒▓███▀▒░▓  ░ ▒▓ ░▒▓░ ▒▒▓  ▒ 
    ▒░▒   ░ ░ ░ ▒  ░ ▒   ▒▒ ░  ░  ▒   ░ ░▒ ▒░▒░▒   ░  ▒ ░  ░▒ ░ ▒░ ░ ▒  ▒ 
    ░    ░   ░ ░    ░   ▒   ░        ░ ░░ ░  ░    ░  ▒ ░  ░░   ░  ░ ░  ░ 
    ░          ░  ░     ░  ░░ ░      ░  ░    ░       ░     ░        ░    
        ░                  ░                     ░               ░      

    [/red]"""
    )
    config.console.print(
        f"             [white]{config.splash_line}[/white] | by [red]IlIonlygangsIlI[/red]"
    )

    if config.about:
        config.console.print(
            """
        Author: Lucas Antoniaci (p1ngul1n0)
        Description: Blackbird is an OSINT tool that perform reverse search in username and emails.
        About WhatsMyName Project: This tool search for accounts using data from the WhatsMyName project, which is an open-source tool developed by WebBreacher. WhatsMyName License: The WhatsMyName project is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0). More details (https://github.com/WebBreacher/WhatsMyName)
        """
        )
        sys.exit()

    is_interactive = (
        not config.username
        and not config.email
        and not config.ip
        and not config.username_file
        and not config.email_file
        and not config.ip_file
        and not config.setup_ai
    )

    while True:
        if is_interactive:
            config.username = None
            config.email = None
            config.ip = None

            config.console.print("\n[cyan1]Please select an option:[/cyan1]")
            config.console.print("[white]1.[/white] Search Username")
            config.console.print("[white]2.[/white] Search Email")
            config.console.print("[white]3.[/white] Track IP")
            config.console.print("[white]4.[/white] Exit")
            
            choice = input("\n > ").strip()
            
            if choice == "1":
                target = input("Enter username: ").strip()
                if target:
                    config.username = [target]
                else:
                    continue
            elif choice == "2":
                target = input("Enter email: ").strip()
                if target:
                    config.email = [target]
                else:
                    continue
            elif choice == "3":
                target = input("Enter IP Address: ").strip()
                if target:
                    config.ip = [target]
                else:
                    continue
            elif choice == "4":
                sys.exit()
            else:
                config.console.print("[red]Invalid selection, please try again.[/red]")
                continue

        if not config.username and (config.permute or config.permuteall):
            config.console.print("Permutations requires --username")
            sys.exit()

        if config.no_update:
            config.console.print(":next_track_button:  Skipping update...")
        else:
            checkUpdates(config)

        if config.ai:
            config.console.print("[yellow1]:exclamation: By proceeding, you consent to share the found site names with Blackbird AI for analysis.[/yellow1] [Y/n]", end="")
            confirm = input(" > ").strip().lower()

            if confirm not in ["", "y"]:
                config.console.print(":stop_sign:  Cancelled by user.")
                sys.exit()

            from modules.ai.key_manager import load_api_key_from_file
            apikey = load_api_key_from_file(config)
            if not apikey:
                config.console.print(
                    ":x: No API Key found. Please run with --setup-ai to configure the API Key."
                )
                sys.exit()

        if config.setup_ai:
            config.console.print("[yellow1]:exclamation: By continuing, you acknowledge that your IP is registered for API key management and abuse prevention.[/yellow1] [Y/n]", end="")
            confirm = input(" > ").strip().lower()

            if confirm not in ["", "y"]:
                config.console.print(":stop_sign:  Cancelled by user.")
                sys.exit()

            from modules.ai.key_manager import fetch_api_key_from_server
            result = fetch_api_key_from_server(config)
            if not result:
                config.console.print(
                    ":x: Failed to fetch API Key. Please check your internet connection or try again later."
                )
            sys.exit()

        if config.username_file:
            if isFile(config.username_file):
                config.username = getLinesFromFile(config.username_file)
                config.console.print(
                    f':glasses: Successfully loaded {len(config.username)} usernames from "{config.username_file}"'
                )
            else:
                config.console.print(f'❌ Could not read file "{config.username_file}"')
                sys.exit()

        if config.username:
            if (config.permute or config.permuteall) and len(config.username) > 1:
                elements = " ".join(config.username)
                way = "all" if config.permuteall else "strict"
                permute = Permute(config.username)
                config.username = permute.gather(way)
                config.console.print(
                    f":glasses: Successfully loaded {len(config.username)} usernames from permuting {elements}"
                )
            for user in config.username:
                config.currentUser = user
                if config.dump or config.csv or config.pdf or config.json:
                    createSaveDirectory(config)
                verifyUsername(config.currentUser, config)
                if config.ai:
                    if len(config.usernameFoundAccounts) > 2:
                        from modules.ai.client import send_prompt
                        site_names = [account.get("name", "") for account in config.usernameFoundAccounts]
                        if (site_names):
                            prompt = ", ".join(site_names)

                            data = send_prompt(prompt, config)

                            if (data):
                                config.ai_analysis = data
                    else:
                        config.console.print(
                            ":warning: Not enough accounts found for AI analysis. Skipping AI features."
                        )

                if config.csv and config.usernameFoundAccounts:
                    saveToCsv(config.usernameFoundAccounts, config)
                if config.pdf and config.usernameFoundAccounts:
                    saveToPdf(config.usernameFoundAccounts, "username", config)
                if config.json and config.usernameFoundAccounts:
                    saveToJson(config.usernameFoundAccounts, config)

                config.currentUser = None
                config.usernameFoundAccounts = None

        if config.email_file:
            if isFile(config.email_file):
                config.email = getLinesFromFile(config.email_file)
                config.console.print(
                    f':glasses: Successfully loaded {len(config.email)} emails from "{config.email_file}"'
                )
            else:
                config.console.print(f'❌ Could not read file "{config.email_file}"')
                sys.exit()

        if config.email:
            for email in config.email:
                config.currentEmail = email
                if config.dump or config.csv or config.pdf or config.json:
                    createSaveDirectory(config)
                verifyEmail(email, config)
                if config.ai:
                    if len(config.emailFoundAccounts) > 2:
                        from modules.ai.client import send_prompt
                        site_names = [account.get("name", "") for account in config.emailFoundAccounts]
                        if (site_names):
                            prompt = ", ".join(site_names)

                            data = send_prompt(prompt, config)

                            if (data):
                                config.ai_analysis = data
                    else:
                        config.console.print(
                            ":warning: Not enough accounts found for AI analysis. Skipping AI features."
                        )

                if config.csv and config.emailFoundAccounts:
                    saveToCsv(config.emailFoundAccounts, config)
                if config.pdf and config.emailFoundAccounts:
                    saveToPdf(config.emailFoundAccounts, "email", config)
                if config.json and config.emailFoundAccounts:
                    saveToJson(config.emailFoundAccounts, config)
                config.currentEmail = None
                config.emailFoundAccounts = None

        if config.ip_file:
            if isFile(config.ip_file):
                config.ip = getLinesFromFile(config.ip_file)
                config.console.print(
                    f':glasses: Successfully loaded {len(config.ip)} IPs from "{config.ip_file}"'
                )
            else:
                config.console.print(f'❌ Could not read file "{config.ip_file}"')
                sys.exit()

        if config.ip:
            for ip in config.ip:
                verifyIP(ip, config)

        if not is_interactive:
            break
