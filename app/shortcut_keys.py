"""Validated Windows shortcut choices, independent of UI and Win32 calls."""

import re


def shortcut_parts(choice):
    if not isinstance(choice, str):
        raise ValueError("Unsupported shortcut.")
    parts = choice.split("+")
    key = parts[-1]
    modifiers = parts[:-1]
    if (
        not modifiers
        or len(set(modifiers)) != len(modifiers)
        or any(x not in ("Ctrl", "Alt", "Shift") for x in modifiers)
    ):
        raise ValueError("Unsupported shortcut.")
    if not any(x in modifiers for x in ("Ctrl", "Alt")):
        raise ValueError("Use Ctrl or Alt with the shortcut.")
    if re.fullmatch("[A-Z]", key):
        vk = ord(key)
    elif key == "Space":
        vk = 0x20
    elif re.fullmatch("F(?:[6-9]|1[0-2])", key):
        vk = 0x70 + int(key[1:]) - 1
    else:
        raise ValueError("Use a letter, Space or F6–F12.")
    return sum({"Ctrl": 2, "Alt": 1, "Shift": 4}[part] for part in modifiers), vk
