from release_updates import check_release

def latest(current):
    version=check_release('Skrivi-TTS',current)
    return (version or current, version is not None)
