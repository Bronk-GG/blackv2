def refactor():
    with open('blackbird.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_interactive = -1
    start_execution = -1
    
    for i, line in enumerate(lines):
        if line.strip() == 'if (' and lines[i+1].strip() == 'not config.username':
            start_interactive = i
        if line.strip() == 'if not config.username and (config.permute or config.permuteall):':
            start_execution = i
            break

    if start_interactive == -1 or start_execution == -1:
        print("Could not find blocks")
        return

    header = "".join(lines[:start_interactive])
    execution_block_lines = lines[start_execution:]

    new_interactive_block = """    is_interactive = (
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

            config.console.print("\\n[cyan1]select an option:[/cyan1]")
            config.console.print("[white]1.[/white] Search Username")
            config.console.print("[white]2.[/white] Search Email")
            config.console.print("[white]3.[/white] Track IP")
            config.console.print("[white]4.[/white] Exit")
            
            choice = input("\\n > ").strip()
            
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
"""

    new_execution_block = ""
    for line in execution_block_lines:
        if line.strip() != "":
            # Indent execution stuff by 4 additional spaces
            new_execution_block += "    " + line
        else:
            new_execution_block += "\n"

    new_execution_block += """
        if not is_interactive:
            break
"""

    with open('blackbird.py', 'w', encoding='utf-8') as f:
        f.write(header + new_interactive_block + "\n" + new_execution_block)

    print("Successfully refactored blackbird.py")

refactor()
