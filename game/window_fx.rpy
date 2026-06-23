# init -10 python:
#     import ctypes
#     import ctypes.wintypes
#     import sys
#     import time

#     class WindowManager(object):
#         """
#         Manages the application window position on Windows using ctypes.
#         Supports scripted movement, interpolation logic, and user-drag restriction.
#         """
#         def __init__(self):
#             self.WIN = (renpy.windows or sys.platform.startswith('win'))
#             self._win_user32 = ctypes.windll.user32 if self.WIN else None
#             self._native_hwnd = None
            
#             self.current_x, self.current_y = 0.0, 0.0
#             self.target_x, self.target_y = 0.0, 0.0
#             self.start_x, self.start_y = 0.0, 0.0
#             self.active = False
            
#             self.move_mode = None
#             self.move_params = {"speed": 10.0, "time": 1.0}
#             self.move_start_time = 0.0
            
#             self.locked = False # Prevents script-based movement
#             self.user_movable = True # Prevents user-based dragging

#         def _get_window_dims(self):
#             """Calculates current window width and height."""
#             if not self._native_hwnd or not self.WIN: return 0, 0
#             rect = ctypes.wintypes.RECT()
#             self._win_user32.GetWindowRect(self._native_hwnd, ctypes.byref(rect))
#             return (rect.right - rect.left), (rect.bottom - rect.top)

#         def _get_work_area(self):
#             """Retrieves the desktop work area dimensions to constrain window movement."""
#             if not self.WIN: return 0, 0, 1920, 1080
#             work_area = ctypes.wintypes.RECT()
#             ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work_area), 0)
#             return work_area.left, work_area.top, work_area.right, work_area.bottom

#         def _get_actual_win_pos(self):
#             """Queries the OS directly for the current window screen coordinates."""
#             if not self._native_hwnd: return 0, 0
#             rect = ctypes.wintypes.RECT()
#             self._win_user32.GetWindowRect(self._native_hwnd, ctypes.byref(rect))
#             return float(rect.left), float(rect.top)

#         def _apply_snap(self, x, y):
#             """Clamps coordinates to ensure the window stays within the desktop work area."""
#             if not self.WIN: return x, y
#             wa_left, wa_top, wa_right, wa_bottom = self._get_work_area()
#             w, h = self._get_window_dims()
#             return float(max(wa_left, min(x, wa_right - w))), float(max(wa_top, min(y, wa_bottom - h)))

#         def start(self):
#             """Initializes the window handle and starts the background ticker."""
#             if self.WIN: self._native_hwnd = self._win_user32.GetActiveWindow()
#             rect = ctypes.wintypes.RECT()
#             if self._native_hwnd:
#                 self._win_user32.GetWindowRect(self._native_hwnd, ctypes.byref(rect))
#                 self.current_x, self.current_y = float(rect.left), float(rect.top)
#             self.target_x, self.target_y = self.current_x, self.current_y
#             self.active = True
#             renpy.show_screen("_window_manager_ticker")

#         def move(self, x, y, mode="glide", snap=False, interpolate=False, **kwargs):
#             """
#             Commands the window to move to a target coordinate.
            
#             :param interpolate: If False, snaps internal state to target before moving.
#             """
#             if self.locked: return
#             if "speed" in kwargs and "time" in kwargs:
#                 raise ValueError("WindowManager: Specify either 'speed' or 'time', not both.")
            
#             if snap: x, y = self._apply_snap(x, y)
            
#             self.move_mode = mode
#             self.move_params["speed"] = kwargs.get("speed", 10.0)
#             self.move_params["time"] = kwargs.get("time", 1.0)
            
#             # If interpolate is disabled, reset start/current pos to last known state
#             if not interpolate:
#                 self.current_x, self.current_y = self.target_x, self.target_y
#                 self.start_x, self.start_y = self.target_x, self.target_y
#             else:
#                 self.start_x, self.start_y = self.current_x, self.current_y
                
#             self.target_x, self.target_y = float(x), float(y)
#             self.move_start_time = time.time()
#             self.active = True

#         def center(self, mode="glide", snap=False, interpolate=True, **kwargs):
#             """Calculates and executes a move command to the center of the screen."""
#             if self.locked or not self.WIN: return
#             wa_left, wa_top, wa_right, wa_bottom = self._get_work_area()
#             w, h = self._get_window_dims()
#             tx = wa_left + ((wa_right - wa_left) // 2) - (w // 2)
#             ty = wa_top + ((wa_bottom - wa_top) // 2) - (h // 2)
#             self.move(tx, ty, mode=mode, snap=snap, interpolate=interpolate, **kwargs)

#         def _commit(self, x, y):
#             """Applies coordinates to the OS window."""
#             if not self._native_hwnd: return
#             self._win_user32.SetWindowPos(self._native_hwnd, 0, int(x), int(y), 0, 0, 0x0001 | 0x0004 | 0x0010)

#         def _tick(self):
#             """Background process for movement interpolation and drag-enforcement."""
#             # Enforcement logic: check if user dragged the window while movement is idle
#             if not self.active or self.move_mode is None:
#                 if not self.user_movable and self._native_hwnd:
#                     actual_x, actual_y = self._get_actual_win_pos()
#                     if abs(actual_x - self.current_x) > 2 or abs(actual_y - self.current_y) > 2:
#                         self._commit(self.current_x, self.current_y)
#                 return
            
#             elapsed = time.time() - self.move_start_time
#             duration = self.move_params["time"]

#             if self.move_mode == "teleport":
#                 if elapsed >= duration:
#                     self.current_x, self.current_y = self.target_x, self.target_y
#                     self._commit(self.current_x, self.current_y)
#                     self.move_mode = None
#             elif self.move_mode == "glide":
#                 progress = min(elapsed / duration, 1.0)
#                 self.current_x = self.start_x + (self.target_x - self.start_x) * progress
#                 self.current_y = self.start_y + (self.target_y - self.start_y) * progress
#                 self._commit(self.current_x, self.current_y)
#                 if progress >= 1.0: self.move_mode = None
#             elif self.move_mode == "linear":
#                 dx = self.target_x - self.current_x
#                 dy = self.target_y - self.current_y
#                 dist = (dx**2 + dy**2)**0.5
#                 step = self.move_params["speed"]
#                 if step >= dist:
#                     self.current_x, self.current_y = self.target_x, self.target_y
#                     self.move_mode = None
#                 else:
#                     ratio = step / dist
#                     self.current_x += dx * ratio
#                     self.current_y += dy * ratio
#                 self._commit(self.current_x, self.current_y)

#     wm = WindowManager()

# screen _window_manager_ticker():
#     # Forces updates every 10ms
#     timer 0.01 repeat True action [Function(wm._tick), Function(renpy.restart_interaction)]