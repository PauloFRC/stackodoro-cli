from .enums import SessionType

import random

def get_pomodoro_session_message(session_type: str) -> str:
    match session_type:
        case SessionType.WORK:
            info_text = random.choice([
                "Focus time",
                "Work starts now",
                "Build momentum",
                "Progress over perfection",
                "Focus with intention",
            ])
        case SessionType.BREAK:
            info_text = random.choice([
                "Break time",
                "Relax and recharge",
                "Take a breather",
                "Enjoy your break",
                "Time to unwind",
            ])
        case SessionType.BIG_BREAK:
            info_text = random.choice([
                "Big break time!",
                "Well deserved rest",
            ])
        case _:
            raise ValueError(f"Unknown session type: {session_type}")
        
    return info_text
        