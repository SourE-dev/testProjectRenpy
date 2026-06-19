label start:
    $ wm.start()
    $ wm.center(mode="teleport", snap=True)
    
    "--- Testing Time & Speed Parameters ---"
    $ wm.move(100, 100, mode="teleport", time=0.5)
    "1. Teleport delay: 0.5s"
    $ wm.user_movable = False
    $ wm.move(500, 300, mode="glide", time=0.2, snap=True)
    "2. Fast Glide: 0.2s duration"
    
    $ wm.move(-100, -100, mode="glide", time=3.0, snap=True)
    "3. Slow Glide: 3.0s duration"
    
    $ wm.move(400, 400, mode="linear", speed=5.0, snap=True, interpolate=False)
    "4. Precise Linear Speed: 5px per tick"
    $ wm.user_movable = True
    $ wm.move(0, 0, mode="linear", speed=50.0, snap=True)
    "5. Blazing Linear Speed: 50px per tick"
    
    "Tests Complete."
    return