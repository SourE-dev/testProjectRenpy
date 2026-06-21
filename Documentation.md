# Ren'Py-to-PyQt Companion System Documentation

This documentation outlines the architecture and methods for your **Ren'Py-to-PyQt Companion System**.

This system uses a file-based event synchronization bridge to allow Ren'Py to spawn and control persistent or transient UI elements in an external PyQt6 application.

---

# 1. Architectural Overview

The system operates as a decoupled **Producer-Consumer** model:

## Producer (Ren'Py)

Manages the game state and writes updates to a shared `game_events.json` file.

## Consumer (PyQt6)

A background watcher monitors the JSON file. When it detects a change, it updates the UI by spawning, moving, or closing windows accordingly.

---

# 2. Ren'Py Methods (`events.rpy`)

These functions are used within your game script to control companion windows.

| Method                                        | Purpose                                                                                                                         |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `update_companion_state(...)`                 | The primary entry point. Spawns or updates a window. If a `logical_id` is provided, the window is persistent and rollback-safe. |
| `remove_companion_state_by_logic(logical_id)` | Removes a specific persistent window by its logical name.                                                                       |
| `clear_companion_states()`                    | Wipes all active windows from the screen immediately.                                                                           |

## Key Parameters for `update_companion_state`

| Parameter    | Description                                                                     |
| ------------ | ------------------------------------------------------------------------------- |
| `msg`        | The string text to display.                                                     |
| `effect`     | Selects the visual style (`EFFECT_FIREBALL`, `EFFECT_SYSTEM`, etc.).            |
| `cleanup`    | Defines lifecycle (`CLEANUP_MANUAL` vs `CLEANUP_IMMEDIATE`).                    |
| `logical_id` | A unique string key for persistent windows. Omit for one-off transient windows. |
| `kwargs`     | Passes extra settings (e.g., `pos=(100, 100)`, `scale_w=256`).                  |

---

# 3. Automatic Cleanup Logic

The system uses a **Generation-Based** approach to handle `CLEANUP_IMMEDIATE` windows, ensuring they vanish when the player progresses without deleting themselves instantly.

## `cleanup_immediate(name=None)`

This function is hooked into:

```python
config.interact_callbacks
```

It compares the current game statement line:

```python
renpy.get_filename_line()
```

with:

```python
last_processed_statement
```

### The Rule

A window is only deleted if the game has moved to a new statement line.

This prevents the window from vanishing during the same frame in which it was created.

---

# 4. PyQt6 Methods (`companion.py`)

The Companion engine handles rendering and OS-level window management.

## Main Classes

### `Companion`

The main controller.

Uses `watchdog` to monitor `game_events.json` for file-system changes and triggers `process_events()` whenever modifications are detected.

### `MessageWindow`

A custom `QWidget` representing an individual companion UI element.

Applies window flags for:

* Always On Top
* Frameless Window Styling

### `AnimatedEffect`

Handles sprite-sheet loading and frame-by-frame animation via `QThreadPool` for non-blocking UI performance.

---

## The Sync Pipeline

### 1. Ren'Py Writes State

```text
game_events.json
```

### 2. Watchdog Detects Change

The file modification event is captured by the watcher.

### 3. Process Events

```python
process_events()
```

reads the JSON state and executes:

```python
sync_windows()
```

### 4. Window Synchronization

#### Garbage Collection

Closes any windows whose `id` is no longer present in the JSON state.

#### Spawning

Instantiates new `MessageWindow` objects for any new IDs found in the JSON.

---

# 5. Best Practices

## Rollback Safety

Always provide a `logical_id` for windows you want to persist across rollbacks.

Without a `logical_id`, the system treats the window as a new instance each time the player rolls backward and forward through game history.

## Resource Management

For animations, always use the `AnimatedEffect` class.

It offloads image processing to background threads, preventing UI stuttering during animation initialization.

## Cleanup Strategy

### Use `CLEANUP_MANUAL`

For:

* Major character dialogue windows
* Persistent HUD elements
* UI components you intend to manage explicitly

### Use `CLEANUP_IMMEDIATE`

For:

* Temporary notifications
* Status popups
* One-shot visual effects

---

# Summary

The Ren'Py-to-PyQt Companion System provides a robust bridge between game logic and external desktop UI components using a file-based synchronization model.

Key benefits include:

* Rollback-safe persistent windows
* Decoupled Ren'Py and PyQt architectures
* Automatic lifecycle management
* Threaded animation rendering
* Real-time JSON-based synchronization

This design allows complex desktop companion interfaces to coexist with Ren'Py gameplay while remaining responsive, maintainable, and rollback-friendly.
