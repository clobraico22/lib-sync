from rekordbox_library import RekordboxLibrary


def generate_rekordbox_library_report(rekordbox_library: RekordboxLibrary) -> None:
    """print some useful lists/stats based on flags from user

    Args:
        rekordbox_library (RekordboxLibrary): user's library to analyze
    """
    print("analyze")
    print(rekordbox_library)
    print("analyzed")
