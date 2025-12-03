# Utility helpers for ParkFlow

def hanya_alnum(char):
    """Return True if `char` is alphanumeric.

    This is used as a Tkinter validation callback (validatecommand receives
    each typed character) so the function expects a single-character string.
    """
    return char.isalnum()
