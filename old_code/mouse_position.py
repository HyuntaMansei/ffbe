import time
import pyautogui
import win32gui
import sys

hwnd = win32gui.FindWindow(None, sys.argv[1])

client_xy0 = win32gui.ClientToScreen(hwnd, (0,0))
(x0, y0) = client_xy0

while True:
    # Get the current mouse position
    x, y = pyautogui.position()

    # Print the coordinates
    print(f'Mouse position: x,y={x,y}', end='  ')
    print(f'client x,y ={x-x0, y-y0} (x0,y0)={x0,y0}')
    time.sleep(2.5)