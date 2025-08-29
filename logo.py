def get_logo(bot_name: str = "Bot") -> str:
    """Generate logo with dynamic bot name"""
    return f'''░█▀▄░█▀█░▀█▀░█░░░▀█▀░░░█▀▀░▀█▀░▀█▀░█░█░█░█░█▀▄░░
░█▀▄░█░█░░█░░█░░░░█░░░░█░█░░█░░░█░░█▀█░█░█░█▀▄░░
░▀▀░░▀▀▀░░▀░░▀▀▀░▀▀▀░░░▀▀▀░▀▀▀░░▀░░▀░▀░▀▀▀░▀▀░░░

Let's play {bot_name}'''

LOGO = get_logo()