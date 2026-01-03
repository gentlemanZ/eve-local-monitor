"""Helper script to find mouse coordinates for Local window region."""

import time
try:
    from PIL import ImageGrab
    import pyautogui
    has_pyautogui = True
except ImportError:
    has_pyautogui = False
    print("Note: Install pyautogui for live mouse tracking: pip install pyautogui")

print("="*60)
print("COORDINATE FINDER")
print("="*60)
print()
print("Move your mouse to the corners of your EVE Local window")
print("and note the coordinates.")
print()

if has_pyautogui:
    print("Press Ctrl+C to stop")
    print()
    try:
        while True:
            x, y = pyautogui.position()
            print(f"\rMouse position: X={x:4d}, Y={y:4d}", end='', flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nStopped.")
else:
    print("Without pyautogui, you'll need to:")
    print("1. Hover over TOP-LEFT corner of Local player list")
    print("2. Note the X,Y position (use Windows Game Bar overlay or estimate)")
    print("3. Hover over BOTTOM-RIGHT corner")
    print("4. Note that X,Y position")
    print()
    print("Example: If Local is on right side of 1920x1080 screen:")
    print("  Top-left: X=1500, Y=200")
    print("  Bottom-right: X=1900, Y=800")

print()
print("="*60)
