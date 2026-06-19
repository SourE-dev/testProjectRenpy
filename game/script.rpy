init python:
    import math
    import time
    import sys

    # ==========================================
    # 1. CROSS-PLATFORM HARDWARE INITIALIZATION
    # ==========================================
    # REMOVED 'import renpy' -> Use the native global 'renpy' namespace instead
    PLATFORM_WIN = (renpy.windows or sys.platform.startswith('win'))
    PLATFORM_LINUX = (renpy.linux or sys.platform.startswith('linux'))

    # Pointers and handles populated dynamically at runtime
    _win_user32 = None
    _linux_x11 = None
    _native_hwnd = None
    _x11_display = None

    if PLATFORM_WIN:
        try:
            import ctypes
            _win_user32 = ctypes.windll.user32
            # NOSIZE (0x0001) | NOZORDER (0x0004) | NOACTIVATE (0x0010)
            SWP_MOVE_FLAGS = 0x0001 | 0x0004 | 0x0010
        except Exception:
            PLATFORM_WIN = False

    elif PLATFORM_LINUX:
        try:
            import ctypes
            _linux_x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
            _linux_x11.XOpenDisplay.restype = ctypes.c_void_p
            _linux_x11.XDefaultRootWindow.restype = ctypes.c_ulong
        except Exception:
            PLATFORM_LINUX = False


    # ==========================================
    # 2. INTERNAL UTILITY DETECTORS
    # ==========================================
    def _find_native_window():
        """Locates and saves the engine's OS window handles."""
        global _native_hwnd, _x11_display
        
        if PLATFORM_WIN and _win_user32:
            _native_hwnd = _win_user32.GetActiveWindow()
            
        elif PLATFORM_LINUX and _linux_x11:
            # 0 or None defaults to the local active display pipeline
            _x11_display = _linux_x11.XOpenDisplay(None)
            if _x11_display:
                # In Ren'Py on X11, the active foreground window can be referenced
                # via InputFocus or searching the clients list. For instant execution,
                # we query the window currently receiving user focus inputs.
                focus_win = ctypes.c_ulong()
                revert_to = ctypes.c_int()
                _linux_x11.XGetInputFocus(_x11_display, ctypes.byref(focus_win), ctypes.byref(revert_to))
                _native_hwnd = focus_win.value

    def get_system_screen_dimensions():
        """Returns the screen resolution width and height dynamically."""
        if PLATFORM_WIN and _win_user32:
            return _win_user32.GetSystemMetrics(0), _win_user32.GetSystemMetrics(1)
            
        elif PLATFORM_LINUX and _linux_x11 and _x11_display:
            # Safely request display dimensions from X11 Server context
            w = _linux_x11.XDisplayWidth(_x11_display, 0)
            h = _linux_x11.XDisplayHeight(_x11_display, 0)
            if w > 0 and h > 0:
                return w, h
                
        # Safe fallback standard for unexpected environments or headless builds
        return 1920, 1080


    # ==========================================
    # 3. PUBLIC API CONTROL METHODS
    # ==========================================
    window_angle = 0.0
    window_effect_enabled = False

    def start_window_effect():
        global window_effect_enabled
        _find_native_window()
        
        if _native_hwnd:
            if PLATFORM_WIN and _win_user32:
                _win_user32.ShowWindow(_native_hwnd, 1) # Break maximization
            window_effect_enabled = True

    def stop_window_effect():
        global window_effect_enabled, _x11_display
        window_effect_enabled = False
        
        # Clean up open X11 displays to avoid memory leaks
        if PLATFORM_LINUX and _linux_x11 and _x11_display:
            _linux_x11.XCloseDisplay(_x11_display)
            _x11_display = None

    def update_hardware_window_position(x, y):
        """Directly forces raw coordinate updates bypassing engine loops."""
        if not window_effect_enabled or not _native_hwnd:
            return

        if PLATFORM_WIN and _win_user32:
            _win_user32.SetWindowPos(_native_hwnd, 0, int(x), int(y), 0, 0, SWP_MOVE_FLAGS)
            
        elif PLATFORM_LINUX and _linux_x11 and _x11_display:
            # Native C signature: XMoveWindow(Display*, Window, int x, int y)
            _linux_x11.XMoveWindow(_x11_display, _native_hwnd, int(x), int(y))
            # X11 buffers output requests; Flush forces immediate hardware rendering execution
            _linux_x11.XFlush(_x11_display)


    # ==========================================
    # 4. MATH LOOPS
    # ==========================================
    fps_last_time = time.time()
    fps_current = 60.0

    def calculate_raw_fps():
        global fps_last_time, fps_current
        now = time.time()
        delta = now - fps_last_time
        if delta > 0:
            fps_current = 0.9 * fps_current + 0.1 * (1.0 / delta)
        fps_last_time = now
        return f"FPS: {int(fps_current)} | OS: {'Windows' if PLATFORM_WIN else 'Linux' if PLATFORM_LINUX else 'Unsupported'}"

    def high_perf_window_tick():
        global window_angle
        if not window_effect_enabled:
            return

        window_angle += 0.05
        scr_w, scr_h = get_system_screen_dimensions()

        # Calculate coordinates dynamically relative to the desktop display size
        center_x = (scr_w // 2) - 400
        center_y = (scr_h // 2) - 300

        new_x = center_x + (math.cos(window_angle) * 250)
        new_y = center_y + (math.sin(window_angle) * 120)

        update_hardware_window_position(new_x, new_y)


# ==========================================
# 5. RENDER PIPELINE UI SYNC
# ==========================================
screen hardware_window_pumper():
    zorder 100
    if window_effect_enabled:
        timer 0.016 repeat True action [Function(high_perf_window_tick), Function(renpy.restart_interaction)]
    else:
        timer 0.016 repeat True action Function(renpy.restart_interaction)

    text calculate_raw_fps():
        xalign 0.02 yalign 0.02 color "#ffffff" size 22


# ==========================================
# 6. RUNTIME TEST SCENARIO
# ==========================================
label start:
    scene black
    show screen hardware_window_pumper
    
    "System diagnostics initialized. Checking engine hooks..."
    
    $ start_window_effect()
    
    "The engine loop is running. If you are on Windows or Linux, your window should be moving fluidly at 60 FPS."
    "The window bounds scale smoothly across screen setups without impacting standard thread operations."

    $ stop_window_effect()
    "Hardware tracking closed successfully."
    return