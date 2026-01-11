from datetime import datetime

def get_session_start_message() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"chore: session start – {timestamp}"

def get_session_end_message() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"chore: session end – {timestamp}"

def get_autocommit_message(file_count: int) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"wip: auto-saving {file_count} files – {timestamp}"
