"""
app.py
INTERide — Application controller: wires all screens and shared state.
"""

import tkinter as tk

from config      import C
from persistence import load_bookings
from widgets     import SlideManager
from screens     import (
    SplashScreen,
    LoginScreen,
    SignUpScreen,
    VehicleScreen,
    BookingScreen,
    AllBookingsScreen,
    AboutScreen,
    RiderScreen,
)


class INTERideApp:
    """
    Top-level application object.
    Creates the Tk root, shared StringVars, the SlideManager,
    and all six screens, then starts on the splash screen.
    """

    def __init__(self) -> None:
        self.root: tk.Tk = tk.Tk()
        self.root.title("INTERide")
        self._setup_window()
        self.root.configure(bg=C["bg"])

        # ── shared state ──────────────────────────────────────────────────
        self.passenger_name:   tk.StringVar = tk.StringVar()
        self.selected_vehicle: tk.StringVar = tk.StringVar(value="Car")
        self.pickup_var:       tk.StringVar = tk.StringVar()
        self.dropoff_var:      tk.StringVar = tk.StringVar()
        self.bookings:         list         = load_bookings()
        self.current_rider:    dict         = {}

        # ── IP location (default: Manila) ─────────────────────────────────
        self.my_lat:  float = 14.5995
        self.my_lon:  float = 120.9842
        self.my_city: str   = "Manila"

        # ── slide manager ─────────────────────────────────────────────────
        self.slides: SlideManager = SlideManager(self.root)

        # ── build all screens ─────────────────────────────────────────────
        self.splash_screen:       SplashScreen       = SplashScreen(self)
        self.login_screen:        LoginScreen        = LoginScreen(self)
        self.signup_screen :       SignUpScreen       = SignUpScreen(self)
        self.vehicle_screen:      VehicleScreen      = VehicleScreen(self)
        self.booking_screen:      BookingScreen      = BookingScreen(self)
        self.all_bookings_screen: AllBookingsScreen  = AllBookingsScreen(self)
        self.about_screen:        AboutScreen        = AboutScreen(self)
        self.rider_screen:        RiderScreen        = RiderScreen(self)

        # ── start on splash ───────────────────────────────────────────────
        self.splash_screen.place(x=0, y=0, relwidth=1, relheight=1)
        self.slides.stack.append(self.splash_screen)

    def _setup_window(self) -> None:
        sw: int = self.root.winfo_screenwidth()
        sh: int = self.root.winfo_screenheight()
        if sw <= 1366:
            w, h = 960, 640
        elif sw <= 1920:
            w, h = 1100, 700
        else:
            w, h = 1280, 800
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.root.resizable(True, True)
        self.root.minsize(820, 560)

    def run(self) -> None:
        """Enter the Tk main loop."""
        self.root.mainloop()
