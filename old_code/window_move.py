import win32gui
import win32con

def on_window_move():
    print("Window moved")

def window_proc(hwnd, msg, wparam, lparam):
    if msg == win32con.WM_MOVE:
        # This code is executed every time the window moves
        on_window_move()

    # Call the original window procedure for any other messages
    return win32gui.CallWindowProc(old_proc, hwnd, msg, wparam, lparam)

if __name__ == '__main__':
    # Replace 'Window Title' with the actual title of the window you want to track
    hwnd = win32gui.FindWindow(None, 'hyuntamansei')
    print(hwnd)

    # Subclass the window procedure for the specified window handle
    old_proc = win32gui.SetWindowLong(hwnd, win32con.GWL_WNDPROC, window_proc)

    # Enter the message loop to process messages
    win32gui.PumpMessages()