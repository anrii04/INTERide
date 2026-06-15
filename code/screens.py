"""
screens.py
INTERide — All six application screens.

  SplashScreen      — animated logo + start button
  NameScreen        — passenger name entry
  VehicleScreen     — vehicle picker cards
  BookingScreen     — map + side panel (pickup, drop-off, fare, book)
  AllBookingsScreen — full treeview table of past bookings
  AboutScreen       — group info, project docs, features
"""

from typing import Dict, List, Optional, Tuple
import os
import threading

import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk
from config      import C, F, HAS_MAP, HAS_DOCX
from models      import VEHICLES, V_MAP
from geo         import geocode, get_road_route
from persistence import save_all, make_receipt
from widgets     import Screen, draw_gradient
from riders import assign_rider
if HAS_MAP:
    import tkintermapview as mapview  # type: ignore


# ══════════════════════════════════════════════════════════════════════════
#  SCREEN 1 — Splash
# ══════════════════════════════════════════════════════════════════════════
class SplashScreen(Screen):
    def __init__(self, app: object) -> None:
        super().__init__(app)
        self._anim_id: Optional[int ] = None
        self._build()
        self._anim_id = self.after(100, self._start_logo_anim)
        threading.Thread(target=self._fetch_loc, daemon=True).start()

    def _fetch_loc(self) -> None:
        from geo import ip_location
        self.app.my_lat, self.app.my_lon, self.app.my_city = ip_location()


    def _redraw_bg(self) -> None:
        self.update_idletasks()
        w = self.winfo_toplevel().winfo_width()
        h = self.winfo_toplevel().winfo_height()
        if w > 1 and h > 1:
            img = self._bg_img_raw.resize((w, h), Image.LANCZOS)
            self._bg_photo = ImageTk.PhotoImage(img)
            self.canvas.delete("bg")
            self.canvas.create_image(0, 0, anchor="nw", image=self._bg_photo, tags="bg")
            self.canvas.lower("bg")
            self._show_btn()  # ← call directly instead of after()

    def _show_btn(self) -> None:
        w = self.app.root.winfo_width()
        h = self.app.root.winfo_height()
        self.canvas.delete("start_btn_window")
        self.canvas.create_window(
            w // 2,
            int(h * 0.92),
            window=self.start_btn,
            tags="start_btn_window"
    )
    

    def on_show(self) -> None:
        try:
            if self._anim_id:
                self.after_cancel(self._anim_id)
        except:
            pass
        self._redraw_bg()
        # reset and replay the bar animation
        self.bar_width = 0
        self.bar.config(width=0)
        self._bar_anim()

    def _build(self) -> None:
        # Set up canvas
        self.canvas: tk.Canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Load background image
        bg_path = os.path.join(os.path.dirname(__file__), "Splash_BG.jpg")
        self._bg_img_raw = Image.open(bg_path)

        def _resize_bg(event):
            img = self._bg_img_raw.resize((event.width, event.height), Image.LANCZOS)
            self._bg_photo = ImageTk.PhotoImage(img)
            self.canvas.delete("bg")
            self.canvas.create_image(0, 0, anchor="nw", image=self._bg_photo, tags="bg")
            self.canvas.tag_lower("bg")

        self.canvas.bind("<Configure>", _resize_bg)

        centre: tk.Frame = tk.Frame(self, bg="#C8D8EC")
        centre.place(relx=0.5, rely=0.95, anchor="center")


        bar_bg: tk.Frame = tk.Frame(self, bg="#D8E8F0", width=240, height=3)
        bar_bg.place(relx=0.5, rely=0.88, anchor="center")
        bar_bg.pack_propagate(False)
        self.bar: tk.Frame = tk.Frame(bar_bg, bg=C["white"], width=0, height=3)
        self.bar.place(x=0, y=0)
        self.bar_width: int = 0
        self._bar_anim()

        self.start_btn: tk.Button = self.btn(
            self, "Start Booking a Ride",
            command=self._go_name,
            bg="#D8E8F0", fg=C["primary"],
            font_size=10, pady=8, padx=24,
        )
        self.start_btn.config(highlightthickness=0, relief="flat", borderwidth=0)
        self.start_btn.place(relx=0.5, rely=0.93, anchor="center")
        self.start_btn.place_forget()

    # ── logo grow ─────────────────────────────────────────────────────────
    def _start_logo_anim(self) -> None:
        if not hasattr(self, 'logo_lbl'):  
            return
        self._logo_size: int = 10
        self._grow_logo()

    def _grow_logo(self) -> None:
        if not hasattr(self, 'logo_lbl'):
            return
        if self._logo_size < 54:
            self._logo_size += 4
            self.logo_lbl.config(font=(F, self._logo_size, "bold"))
            self.after(18, self._grow_logo)
        else:
            self._fade_tag(0)

    def _fade_tag(self, step: int) -> None:
        blues: List[str] = [
            "#1E40AF", "#1D4ED8", "#2563EB", "#3B82F6",
            "#60A5FA", "#93C5FD", "#BFDBFE",
        ]
        if step < len(blues):
            self.tag_lbl.config(fg=blues[step])
            self.after(60, lambda: self._fade_tag(step + 1))

    # ── progress bar ──────────────────────────────────────────────────────
    def _bar_anim(self) -> None:
        if self.bar_width < 240:
            self.bar_width += 3
            self.bar.config(width=self.bar_width)
            self.after(20, self._bar_anim)
        else:
            self.after(300, self._show_btn_first)

    def _show_btn_first(self) -> None:
        self.canvas.delete("start_btn_window")
        self.canvas.create_window(
            self.winfo_width() // 2,
            int(self.winfo_height() * 0.92),
            window=self.start_btn,
            tags="start_btn_window"
        )
        self.app.root.bind("<Return>", lambda e: self._go_name())
        self.app.root.bind("<space>",  lambda e: self._go_name())

    def _go_name(self) -> None:
        self.app.root.unbind("<Return>")
        self.app.root.unbind("<space>")
        self.app.slides.push(self.app.login_screen)

# ══════════════════════════════════════════════════════════════════════════
#  SCREEN 2 — Login
# ══════════════════════════════════════════════════════════════════════════
class LoginScreen(Screen):
    def __init__(self, app: object) -> None:
        super().__init__(app)
        self._build()

    def _build(self) -> None:
        top_c: tk.Canvas = tk.Canvas(self, height=220, highlightthickness=0)
        top_c.pack(fill="x")
        top_c.bind(
            "<Configure>",
            lambda e: draw_gradient(top_c, e.width, e.height, C["grad_top"], C["accent"]),
        )

        tk.Label(top_c, text="INTERide",
                 bg=C["grad_top"], fg=C["white"],
                 font=(F, 22, "bold")).place(relx=0.5, y=60, anchor="center")

        tk.Label(top_c, text="Welcome back! Please log in.",
                 bg=C["grad_top"], fg="#BFDBFE",
                 font=(F, 12)).place(relx=0.5, y=100, anchor="center")

        card: tk.Frame = tk.Frame(
            self, bg=C["surface"],
            highlightbackground=C["border"], highlightthickness=1,
        )
        card.pack(padx=60, pady=30, fill="x")

        tk.Label(card, text="Login to your account",
                 bg=C["surface"], fg=C["text"],
                 font=(F, 18, "bold")).pack(pady=(36, 6))

        tk.Label(card, text="Enter your username and password to continue.",
                 bg=C["surface"], fg=C["muted"],
                 font=(F, 10)).pack()

        ef: tk.Frame = tk.Frame(card, bg=C["surface"])
        ef.pack(pady=(20, 0), padx=40, fill="x")

        # username
        tk.Label(ef, text="Username", bg=C["surface"], fg=C["text"],
                 font=(F, 10, "bold"), anchor="w").pack(fill="x")
        self.username_var: tk.StringVar = tk.StringVar()
        self.username_e: tk.Entry = self.entry(
            ef, self.username_var,
            placeholder="Enter your username",
            font_size=13,
        )
        self.username_e.pack(fill="x", ipady=10, pady=(2, 12))

        # password
        tk.Label(ef, text="Password", bg=C["surface"], fg=C["text"],
                 font=(F, 10, "bold"), anchor="w").pack(fill="x")
        self.password_var: tk.StringVar = tk.StringVar()
        self.password_e: tk.Entry = tk.Entry(
            ef, textvariable=self.password_var,
            bg=C["bg"], fg=C["text"],
            font=(F, 13), relief="flat", show="*",
            highlightbackground=C["border"],
            highlightthickness=2,
            insertbackground=C["primary"],
        )
        self.password_e.pack(fill="x", ipady=10, pady=(2, 0))
        self.password_e.bind("<Return>", lambda e: self._login())

        btn_f: tk.Frame = tk.Frame(card, bg=C["surface"])
        btn_f.pack(pady=(20, 0), padx=40, fill="x")

        self.btn(btn_f, "Login  →", self._login,
                 font_size=12, pady=13).pack(fill="x")

        # sign up link
        link_f: tk.Frame = tk.Frame(card, bg=C["surface"])
        link_f.pack(pady=(12, 36))

        tk.Label(link_f, text="Don't have an account?",
                 bg=C["surface"], fg=C["muted"],
                 font=(F, 10)).pack(side="left")

        tk.Button(link_f, text="Sign Up",
                  bg=C["surface"], fg=C["primary"],
                  font=(F, 10, "bold"), relief="flat", cursor="hand2",
                  command=self._go_signup).pack(side="left", padx=(6, 0))

        tk.Button(self, text="← Back",
                  bg=C["bg"], fg=C["muted"],
                  font=(F, 9), relief="flat", cursor="hand2",
                  command=self.app.slides.pop).pack(pady=(0, 10))

    def _login(self) -> None:
        from accounts import find_account
        username: str = self.username_var.get().strip()
        password: str = self.password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("INTERide", "Please fill in all fields.")
            return

        acc = find_account(username, password)
        if not acc:
            messagebox.showerror("INTERide", "Invalid username or password.")
            return

        # store the logged-in user's full name
        self.app.passenger_name.set(acc["full_name"])
        self.password_var.set("")
        self.app.vehicle_screen.on_show()
        self.app.slides.push(
            self.app.vehicle_screen,
            on_done=self.app.vehicle_screen.on_ready,
        )

    def _go_signup(self) -> None:
        self.app.slides.push(self.app.signup_screen)

# ══════════════════════════════════════════════════════════════════════════
#  SCREEN 3 — Sign Up
# ══════════════════════════════════════════════════════════════════════════
class SignUpScreen(Screen):
    def __init__(self, app: object) -> None:
        super().__init__(app)
        self._build()

    def _build(self) -> None:
        top_c: tk.Canvas = tk.Canvas(self, height=160, highlightthickness=0)
        top_c.pack(fill="x")
        top_c.bind(
            "<Configure>",
            lambda e: draw_gradient(top_c, e.width, e.height, C["grad_top"], C["accent"]),
        )

        tk.Label(top_c, text="INTERide",
                 bg=C["grad_top"], fg=C["white"],
                 font=(F, 22, "bold")).place(relx=0.5, y=50, anchor="center")

        tk.Label(top_c, text="Create your account",
                 bg=C["grad_top"], fg="#BFDBFE",
                 font=(F, 12)).place(relx=0.5, y=88, anchor="center")

        # scrollable body
        body_c: tk.Canvas = tk.Canvas(self, bg=C["surface"], highlightthickness=0)
        sb: ttk.Scrollbar = ttk.Scrollbar(self, orient="vertical", command=body_c.yview)
        body_c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        body_c.pack(fill="both", expand=True)

        inner: tk.Frame = tk.Frame(body_c, bg=C["surface"])
        win = body_c.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: body_c.configure(scrollregion=body_c.bbox("all")))
        body_c.bind("<Configure>",
                    lambda e: body_c.itemconfig(win, width=e.width))
        body_c.bind("<MouseWheel>",
                    lambda e: body_c.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._build_form(inner)

    def _build_form(self, f: tk.Frame) -> None:
        card: tk.Frame = tk.Frame(
            f, bg=C["surface"],
            highlightbackground=C["border"], highlightthickness=1,
        )
        card.pack(padx=60, pady=20, fill="x")

        tk.Label(card, text="Fill in your details",
                 bg=C["surface"], fg=C["text"],
                 font=(F, 16, "bold")).pack(pady=(28, 4))
        tk.Label(card, text="All fields are required.",
                 bg=C["surface"], fg=C["muted"],
                 font=(F, 10)).pack()

        ef: tk.Frame = tk.Frame(card, bg=C["surface"])
        ef.pack(pady=(16, 0), padx=40, fill="x")

        # full name
        tk.Label(ef, text="Full Name", bg=C["surface"], fg=C["text"],
                 font=(F, 10, "bold"), anchor="w").pack(fill="x")
        self.fullname_var: tk.StringVar = tk.StringVar()
        self.entry(ef, self.fullname_var,
                   placeholder="Enter your full name",
                   font_size=13).pack(fill="x", ipady=10, pady=(2, 12))

        # email
        tk.Label(ef, text="Email Address", bg=C["surface"], fg=C["text"],
                 font=(F, 10, "bold"), anchor="w").pack(fill="x")
        self.email_var: tk.StringVar = tk.StringVar()
        self.entry(ef, self.email_var,
                   placeholder="Enter your email",
                   font_size=13).pack(fill="x", ipady=10, pady=(2, 12))

        # phone
        tk.Label(ef, text="Phone Number", bg=C["surface"], fg=C["text"],
                 font=(F, 10, "bold"), anchor="w").pack(fill="x")
        self.phone_var: tk.StringVar = tk.StringVar()
        self.entry(ef, self.phone_var,
                   placeholder="Enter your phone number",
                   font_size=13).pack(fill="x", ipady=10, pady=(2, 12))

        # username
        tk.Label(ef, text="Username", bg=C["surface"], fg=C["text"],
                 font=(F, 10, "bold"), anchor="w").pack(fill="x")
        self.new_username_var: tk.StringVar = tk.StringVar()
        self.entry(ef, self.new_username_var,
                   placeholder="Choose a username",
                   font_size=13).pack(fill="x", ipady=10, pady=(2, 12))

        # password
        tk.Label(ef, text="Password", bg=C["surface"], fg=C["text"],
                 font=(F, 10, "bold"), anchor="w").pack(fill="x")
        self.new_password_var: tk.StringVar = tk.StringVar()
        tk.Entry(
            ef, textvariable=self.new_password_var,
            bg=C["bg"], fg=C["text"],
            font=(F, 13), relief="flat", show="*",
            highlightbackground=C["border"],
            highlightthickness=2,
            insertbackground=C["primary"],
        ).pack(fill="x", ipady=10, pady=(2, 12))

        # confirm password
        tk.Label(ef, text="Confirm Password", bg=C["surface"], fg=C["text"],
                 font=(F, 10, "bold"), anchor="w").pack(fill="x")
        self.confirm_password_var: tk.StringVar = tk.StringVar()
        tk.Entry(
            ef, textvariable=self.confirm_password_var,
            bg=C["bg"], fg=C["text"],
            font=(F, 13), relief="flat", show="*",
            highlightbackground=C["border"],
            highlightthickness=2,
            insertbackground=C["primary"],
        ).pack(fill="x", ipady=10, pady=(2, 0))

        btn_f: tk.Frame = tk.Frame(card, bg=C["surface"])
        btn_f.pack(pady=(20, 0), padx=40, fill="x")
        self.btn(btn_f, "Create Account", self._signup,
                 font_size=12, pady=13).pack(fill="x")

        tk.Button(card, text="← Back to Login",
                  bg=C["surface"], fg=C["muted"],
                  font=(F, 9), relief="flat", cursor="hand2",
                  command=self.app.slides.pop).pack(pady=(10, 28))

    def _signup(self) -> None:
        from accounts import save_accounts, load_accounts, username_exists

        full_name: str = self.fullname_var.get().strip()
        email:     str = self.email_var.get().strip()
        phone:     str = self.phone_var.get().strip()
        username:  str = self.new_username_var.get().strip()
        password:  str = self.new_password_var.get().strip()
        confirm:   str = self.confirm_password_var.get().strip()

        # validation
        placeholders = [
            "Enter your full name", "Enter your email",
            "Enter your phone number", "Choose a username",
        ]
        if not all([full_name, email, phone, username, password, confirm]) \
                or full_name in placeholders or email in placeholders \
                or phone in placeholders or username in placeholders:
            messagebox.showwarning("INTERide", "Please fill in all fields.")
            return

        if password != confirm:
            messagebox.showerror("INTERide", "Passwords do not match.")
            return

        if username_exists(username):
            messagebox.showerror("INTERide", "Username is already taken.")
            return

        # save new account
        accounts = load_accounts()
        accounts.append({
            "full_name": full_name,
            "email":     email,
            "phone":     phone,
            "username":  username,
            "password":  password,
        })
        save_accounts(accounts)

        # clear fields
        for var in [self.fullname_var, self.email_var, self.phone_var,
                    self.new_username_var, self.new_password_var,
                    self.confirm_password_var]:
            var.set("")

        messagebox.showinfo("INTERide", "Account created! Please log in.")
        self.app.slides.pop()

# ══════════════════════════════════════════════════════════════════════════
#  SCREEN 4 — Vehicle Picker
# ══════════════════════════════════════════════════════════════════════════
class VehicleScreen(Screen):
    def __init__(self, app: object) -> None:
        super().__init__(app)
        self._build()

    def _build(self) -> None:
        hdr_c: tk.Canvas = tk.Canvas(self, height=140, highlightthickness=0)
        hdr_c.pack(fill="x")
        hdr_c.bind(
            "<Configure>",
            lambda e: draw_gradient(hdr_c, e.width, e.height, C["grad_top"], C["accent"]),
        )

        self.greet: tk.Label = tk.Label(
            hdr_c, text="", bg=C["grad_top"], fg=C["white"], font=(F, 19, "bold")
        )
        self.greet.place(relx=0.5, y=55, anchor="center")
        tk.Label(hdr_c, text="Choose your ride",
                 bg=C["grad_top"], fg="#BFDBFE",
                 font=(F, 11)).place(relx=0.5, y=90, anchor="center")

        cards_frame: tk.Frame = tk.Frame(self, bg=C["bg"])
        cards_frame.pack(padx=40, pady=24, fill="both", expand=True)

        self._selected_v: tk.StringVar          = tk.StringVar(value="Car")
        self._v_frames:   Dict[str, tuple]      = {}

        for v in VEHICLES:
            card: tk.Frame = tk.Frame(
                cards_frame, bg=C["surface"],
                highlightbackground=C["border"],
                highlightthickness=2, cursor="hand2",
            )
            card.pack(fill="x", pady=8)

            inner: tk.Frame = tk.Frame(card, bg=C["surface"])
            inner.pack(fill="x", padx=20, pady=16)

            left: tk.Frame = tk.Frame(inner, bg=C["surface"])
            left.pack(side="left")
            tk.Label(left, text=v.emoji, bg=C["surface"],
                     font=(F, 30)).pack(side="left", padx=(0, 16))

            info: tk.Frame = tk.Frame(left, bg=C["surface"])
            info.pack(side="left")
            nl: tk.Label = tk.Label(info, text=v.vtype, bg=C["surface"],
                                    fg=C["text"], font=(F, 14, "bold"))
            nl.pack(anchor="w")
            tl: tk.Label = tk.Label(info, text=v.tagline, bg=C["surface"],
                                    fg=C["muted"], font=(F, 9))
            tl.pack(anchor="w")

            right: tk.Frame = tk.Frame(inner, bg=C["surface"])
            right.pack(side="right")
            rl: tk.Label = tk.Label(right, text=v.rate_desc(), bg=C["surface"],
                                    fg=C["primary"], font=(F, 13, "bold"))
            rl.pack(anchor="e")
            tk.Label(right, text="per km", bg=C["surface"],
                     fg=C["muted"], font=(F, 8)).pack(anchor="e")

            self._v_frames[v.vtype] = (card, inner, nl, tl, rl, right)
            for w in [card, inner, left, info, right, nl, tl, rl]:
                w.bind("<Button-1>", lambda e, vt=v.vtype: self._select(vt))

        btn_f: tk.Frame = tk.Frame(self, bg=C["bg"])
        btn_f.pack(pady=10, padx=40, fill="x")
        self.btn(btn_f, "Next  →", self._next,
                 font_size=12, pady=13).pack(fill="x")

        tk.Button(self, text="← Back",
                  bg=C["bg"], fg=C["muted"],
                  font=(F, 9), relief="flat", cursor="hand2",
                  command=self.app.slides.pop).pack(pady=(0, 10))

        self._select("Car")
        self._v_order: List[str] = [v.vtype for v in VEHICLES]

    def on_show(self) -> None:
        name: str = self.app.passenger_name.get()
        self.greet.config(text=f"Hello, {name}! 👋")
        self.app.root.bind("<Down>", self._key_down)
        self.app.root.bind("<Up>",   self._key_up)

    def on_ready(self) -> None:
        self.app.root.bind("<Return>", lambda e: self._next())

    def _key_down(self, event: tk.Event) -> None:
        idx: int = self._v_order.index(self._selected_v.get())
        self._select(self._v_order[(idx + 1) % len(self._v_order)])

    def _key_up(self, event: tk.Event) -> None:
        idx: int = self._v_order.index(self._selected_v.get())
        self._select(self._v_order[(idx - 1) % len(self._v_order)])

    def _select(self, vtype: str) -> None:
        self._selected_v.set(vtype)
        for vt, (card, inner, nl, tl, rl, right) in self._v_frames.items():
            if vt == vtype:
                card.config(highlightbackground=C["primary"], highlightthickness=2)
                for w in [card, inner, nl, tl, rl, right]:
                    w.config(bg=C["primary_lt"])
                nl.config(fg=C["primary"])
            else:
                card.config(highlightbackground=C["border"], highlightthickness=1)
                for w in [card, inner, nl, tl, rl, right]:
                    w.config(bg=C["surface"])
                nl.config(fg=C["text"])
        self.app.selected_vehicle.set(vtype)

    def _next(self) -> None:
        self.app.root.unbind("<Down>")
        self.app.root.unbind("<Up>")
        self.app.root.unbind("<Return>")
        self.app.slides.push(self.app.booking_screen)
        self.app.booking_screen.on_show()


# ══════════════════════════════════════════════════════════════════════════
#  SCREEN 5 — Booking (map + side panel)
# ══════════════════════════════════════════════════════════════════════════
class BookingScreen(Screen):
    def __init__(self, app: object) -> None:
        super().__init__(app)
        self._pc:      Optional[tuple ] = None
        self._dc:      Optional[tuple ] = None
        self._km:      float        = 0.0
        self._route:   object       = None
        self._mk_pick: object       = None
        self._mk_drop: object       = None
        self._build()

    def _build(self) -> None:
        # ── top bar ──
        top: tk.Frame = tk.Frame(self, bg=C["dark"], height=54)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Button(top, text="←", bg=C["dark"], fg=C["white"],
                  font=(F, 14), relief="flat", cursor="hand2",
                  command=self.app.slides.pop).pack(side="left", padx=12, pady=10)

        self.lbl_title: tk.Label = tk.Label(
            top, text="Where to?",
            bg=C["dark"], fg=C["white"], font=(F, 14, "bold"),
        )
        self.lbl_title.pack(side="left", pady=10)

        tk.Button(top, text="About",
                  bg=C["dark"], fg=C["muted"],
                  font=(F, 9), relief="flat", cursor="hand2", padx=10,
                  command=lambda: self.app.slides.push(self.app.about_screen),
                  ).pack(side="right", padx=(0, 8), pady=14)

        tk.Button(top, text="All Bookings",
                  bg=C["primary"], fg=C["white"],
                  font=(F, 9, "bold"), relief="flat", cursor="hand2", padx=10,
                  command=self._go_all_bookings,
                  ).pack(side="right", padx=(0, 4), pady=14)

        # ── main layout ──
        body: tk.Frame = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=0)
        body.rowconfigure(0, weight=1)

        map_f: tk.Frame = tk.Frame(body, bg=C["dark"])
        map_f.grid(row=0, column=0, sticky="nsew")
        if HAS_MAP:
            self.map_w = mapview.TkinterMapView(map_f, corner_radius=0)
            self.map_w.pack(fill="both", expand=True)
            self.map_w.set_position(14.5995, 120.9842)
            self.map_w.set_zoom(13)
        else:
            tk.Label(map_f,
                     text="Map unavailable\npip install tkintermapview",
                     bg="#1A1A2E", fg="#555",
                     font=(F, 12)).pack(expand=True)

        panel: tk.Frame = tk.Frame(body, bg=C["surface"], width=320)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.pack_propagate(False)

        inner_c: tk.Canvas = tk.Canvas(panel, bg=C["surface"], highlightthickness=0)
        sb: ttk.Scrollbar  = ttk.Scrollbar(panel, orient="vertical", command=inner_c.yview)
        inner_c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        inner_c.pack(side="left", fill="both", expand=True)

        scroll_f: tk.Frame = tk.Frame(inner_c, bg=C["surface"])
        win = inner_c.create_window((0, 0), window=scroll_f, anchor="nw")

        scroll_f.bind(
            "<Configure>",
            lambda e: inner_c.configure(scrollregion=inner_c.bbox("all")),
        )
        inner_c.bind("<Configure>",
                     lambda e: inner_c.itemconfig(win, width=e.width))
        inner_c.bind(
            "<MouseWheel>",
            lambda e: inner_c.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )
        inner_c.bind("<Button-4>", lambda e: inner_c.yview_scroll(-1, "units"))
        inner_c.bind("<Button-5>", lambda e: inner_c.yview_scroll(1,  "units"))
        scroll_f.bind(
            "<MouseWheel>",
            lambda e: inner_c.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        self._panel_canvas: tk.Canvas = inner_c
        self._build_panel(scroll_f)

    def _bind_scroll(self, widget: tk.Widget) -> None:
        widget.bind(
            "<MouseWheel>",
            lambda e: self._panel_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )
        widget.bind("<Button-4>",
                    lambda e: self._panel_canvas.yview_scroll(-1, "units"))
        widget.bind("<Button-5>",
                    lambda e: self._panel_canvas.yview_scroll(1,  "units"))
        for child in widget.winfo_children():
            self._bind_scroll(child)

    def _build_panel(self, f: tk.Frame) -> None:
        pad: dict = dict(padx=18)

        self.greet_lbl: tk.Label = tk.Label(
            f, text="", bg=C["surface"], fg=C["text"],
            font=(F, 14, "bold"), wraplength=270, justify="left",
        )
        self.greet_lbl.pack(fill="x", **pad, pady=(20, 4))

        self.v_badge: tk.Label = tk.Label(
            f, text="", bg=C["primary_lt"], fg=C["primary"], font=(F, 10, "bold")
        )
        self.v_badge.pack(anchor="w", **pad, pady=(0, 14))

        # pickup
        self._sec(f, "PICKUP LOCATION")
        pf: tk.Frame = tk.Frame(f, bg=C["surface"])
        pf.pack(fill="x", **pad, pady=(0, 6))
        self.pick_e: tk.Entry = tk.Entry(
            pf, textvariable=self.app.pickup_var,
            bg=C["bg"], fg=C["text"], font=(F, 10), relief="flat",
            highlightbackground=C["border"], highlightthickness=1,
            insertbackground=C["primary"],
        )
        self.pick_e.pack(side="left", fill="x", expand=True, ipady=9)
        self.pick_e.insert(0, "Search pickup...")
        self.pick_e.config(fg=C["muted"])
        self._ph(self.pick_e, "Search pickup...", self.app.pickup_var)
        tk.Button(pf, text="Pin", bg=C["primary"], fg=C["white"],
                  font=(F, 9, "bold"), relief="flat", cursor="hand2",
                  padx=10, pady=9,
                  command=self._pin_pickup).pack(side="left", padx=(4, 0))

        # drop-off
        self._sec(f, "DROP-OFF LOCATION")
        df: tk.Frame = tk.Frame(f, bg=C["surface"])
        df.pack(fill="x", **pad, pady=(0, 6))
        self.drop_e: tk.Entry = tk.Entry(
            df, textvariable=self.app.dropoff_var,
            bg=C["bg"], fg=C["text"], font=(F, 10), relief="flat",
            highlightbackground=C["border"], highlightthickness=1,
            insertbackground=C["primary"],
        )
        self.drop_e.pack(side="left", fill="x", expand=True, ipady=9)
        self._ph(self.drop_e, "Search drop-off...", self.app.dropoff_var)
        tk.Button(df, text="Pin", bg=C["danger"], fg=C["white"],
                  font=(F, 9, "bold"), relief="flat", cursor="hand2",
                  padx=10, pady=9,
                  command=self._pin_dropoff).pack(side="left", padx=(4, 0))

        self.lbl_dist: tk.Label = tk.Label(
            f, text="", bg=C["surface"], fg=C["muted"], font=(F, 9)
        )
        self.lbl_dist.pack(fill="x", **pad, pady=(4, 0))

        # fare card
        cost_card: tk.Frame = tk.Frame(
            f, bg=C["primary_lt"],
            highlightbackground=C["primary"], highlightthickness=1,
        )
        cost_card.pack(fill="x", **pad, pady=14)
        tk.Label(cost_card, text="Estimated Fare",
                 bg=C["primary_lt"], fg=C["primary"],
                 font=(F, 9, "bold")).pack(anchor="w", padx=14, pady=(12, 0))
        self.lbl_cost: tk.Label = tk.Label(
            cost_card, text="₱ —",
            bg=C["primary_lt"], fg=C["primary"], font=(F, 22, "bold"),
        )
        self.lbl_cost.pack(anchor="w", padx=14)
        self.lbl_cost_sub: tk.Label = tk.Label(
            cost_card, text="",
            bg=C["primary_lt"], fg=C["muted"], font=(F, 8),
        )
        self.lbl_cost_sub.pack(anchor="w", padx=14, pady=(0, 12))

        tk.Frame(f, bg=C["border"], height=1).pack(fill="x", **pad, pady=10)

        self.btn_book: tk.Button = tk.Button(
            f, text="Confirm Booking",
            bg=C["primary"], fg=C["white"],
            font=(F, 12, "bold"), relief="flat", cursor="hand2", pady=13,
            activebackground=C["primary2"],
            command=self._book,
        )
        self.btn_book.pack(fill="x", **pad)

        self.lbl_status: tk.Label = tk.Label(
            f, text="", bg=C["surface"], font=(F, 9), wraplength=270
        )
        self.lbl_status.pack(**pad, pady=6)

        self._sec(f, "MY BOOKINGS")
        self.list_f: tk.Frame = tk.Frame(f, bg=C["surface"])
        self.list_f.pack(fill="x", padx=12, pady=(0, 24))

        self.after(100, lambda: self._bind_scroll(f))

    # ── helpers ───────────────────────────────────────────────────────────
    def _sec(self, parent: tk.Frame, title: str) -> None:
        tk.Label(parent, text=title, bg=C["surface"],
                 fg=C["muted"], font=(F, 8, "bold"),
                 anchor="w").pack(fill="x", padx=18, pady=(14, 4))

    def _ph(self, entry: tk.Entry, ph: str, var: tk.StringVar) -> None:
        def fi(ev: tk.Event) -> None:
            if entry.get() == ph:
                entry.delete(0, "end")
                entry.config(fg=C["text"])
        def fo(ev: tk.Event) -> None:
            if not entry.get():
                entry.insert(0, ph)
                entry.config(fg=C["muted"])
        entry.bind("<FocusIn>",  fi)
        entry.bind("<FocusOut>", fo)

    def on_show(self) -> None:
        name:  str = self.app.passenger_name.get()
        vtype: str = self.app.selected_vehicle.get()
        v = V_MAP[vtype]
        self.greet_lbl.config(text=f"Hello {name},\nwhere are we going? 🗺️")
        self.v_badge.config(text=f"  {v.emoji}  {vtype}  ·  {v.rate_desc()}  ")
        if HAS_MAP and hasattr(self, "map_w"):
            self.map_w.set_position(self.app.my_lat, self.app.my_lon)
            self.map_w.set_zoom(13)
            if not self._pc:
                self._pc = (self.app.my_lat, self.app.my_lon)
                self.app.pickup_var.set(self.app.my_city)
                self.pick_e.delete(0, "end")
                self.pick_e.insert(0, self.app.my_city)
                self.pick_e.config(fg=C["text"])
                if self._mk_pick:
                    self._mk_pick.delete()
                self._mk_pick = self.map_w.set_marker(
                    self._pc[0], self._pc[1], text="You",
                    marker_color_circle=C["primary"],
                    marker_color_outside=C["primary2"],
                )
        self._refresh_list()

    # ── geo pins ──────────────────────────────────────────────────────────
    def _pin_pickup(self) -> None:
        addr: str = self.app.pickup_var.get().strip()
        if not addr or addr == "Search pickup...":
            messagebox.showwarning("INTERide", "Enter a pickup address.")
            return
        self.lbl_status.config(text="Searching...", fg=C["muted"])
        self.update()
        coords = geocode(addr)
        if not coords:
            messagebox.showerror("INTERide", f"Can't find '{addr}'.")
            self.lbl_status.config(text="")
            return
        self._pc = coords
        if HAS_MAP and hasattr(self, "map_w"):
            if self._mk_pick:
                self._mk_pick.delete()
            self._mk_pick = self.map_w.set_marker(
                *coords, text="Pickup",
                marker_color_circle=C["primary"],
                marker_color_outside=C["primary2"],
            )
            self.map_w.set_position(*coords)
        if self._dc:
            self._draw_route()
        self.lbl_status.config(text="Pickup pinned!", fg=C["success"])
        self.after(2000, lambda: self.lbl_status.config(text=""))

    def _pin_dropoff(self) -> None:
        addr: str = self.app.dropoff_var.get().strip()
        if not addr or addr == "Search drop-off...":
            messagebox.showwarning("INTERide", "Enter a drop-off address.")
            return
        self.lbl_status.config(text="Searching...", fg=C["muted"])
        self.update()
        coords = geocode(addr)
        if not coords:
            messagebox.showerror("INTERide", f"Can't find '{addr}'.")
            self.lbl_status.config(text="")
            return
        self._dc = coords
        if HAS_MAP and hasattr(self, "map_w"):
            if self._mk_drop:
                self._mk_drop.delete()
            self._mk_drop = self.map_w.set_marker(
                *coords, text="Drop-off",
                marker_color_circle=C["danger"],
                marker_color_outside="#B91C1C",
            )
            self.map_w.set_position(*coords)
        if self._pc:
            self._draw_route()
        self.lbl_status.config(text="Drop-off pinned!", fg=C["success"])
        self.after(2000, lambda: self.lbl_status.config(text=""))

    def _draw_route(self) -> None:
        if self._route and HAS_MAP and hasattr(self, "map_w"):
            try:
                self._route.delete()
            except Exception:
                pass
            self._route = None
        self.lbl_dist.config(text="🔄 Calculating road route...", fg=C["muted"])
        self.lbl_cost.config(text="₱ —")
        self.update()

        def fetch() -> None:
            coords, dist_km, dur_min = get_road_route(self._pc, self._dc)
            self.after(0, lambda: self._apply_route(coords, dist_km, dur_min))

        threading.Thread(target=fetch, daemon=True).start()

    def _apply_route(
        self,
        coords:  list,
        dist_km: float,
        dur_min: Optional[float ],
    ) -> None:
        self._km = dist_km
        if dur_min is not None:
            h:   int = int(dur_min // 60)
            m:   int = int(dur_min % 60)
            eta: str = f"{h}h {m}m" if h > 0 else f"{m} min"
            self.lbl_dist.config(
                text=f"📏 {dist_km:.1f} km  ·  🕐 ~{eta} estimated",
                fg=C["text"],
            )
        else:
            self.lbl_dist.config(
                text=f"📏 ~{dist_km:.1f} km (estimated)", fg=C["muted"]
            )
        if HAS_MAP and hasattr(self, "map_w"):
            self._route = self.map_w.set_path(coords, color=C["primary"], width=5)
            mid = (
                (self._pc[0] + self._dc[0]) / 2,
                (self._pc[1] + self._dc[1]) / 2,
            )
            self.map_w.set_position(*mid)
            self.map_w.set_zoom(12)
        self._update_cost()

    def _update_cost(self) -> None:
        if self._km <= 0:
            self.lbl_cost.config(text="₱ —")
            self.lbl_cost_sub.config(text="")
            return
        v    = V_MAP[self.app.selected_vehicle.get()]
        cost = v.calculate_cost(self._km)
        self.lbl_cost.config(text=f"₱{cost:,.2f}")
        self.lbl_cost_sub.config(
            text=f"{v.vtype} · {self._km} km · {v.rate_desc()}"
        )

    # ── booking actions ───────────────────────────────────────────────────
    def _book(self) -> None:
        from models import Booking
        user:  str = self.app.passenger_name.get().strip()
        pick:  str = self.app.pickup_var.get().strip()
        drop:  str = self.app.dropoff_var.get().strip()
        vtype: str = self.app.selected_vehicle.get()

        if not self._pc:
            messagebox.showwarning("INTERide", "Pin your pickup location.")
            return
        if not self._dc:
            messagebox.showwarning("INTERide", "Pin your drop-off location.")
            return
        if not pick or pick in ("Search pickup...",):
            messagebox.showwarning("INTERide", "Enter pickup location.")
            return
        if not drop or drop in ("Search drop-off...",):
            messagebox.showwarning("INTERide", "Enter drop-off location.")
            return

        b = Booking(user, vtype, pick, drop, self._pc, self._dc, self._km)
        self.app.bookings.append(b)
        save_all(self.app.bookings)
        self._refresh_list()
        self.lbl_status.config(
            text=f"✓ Booked! #{b.bid}  ₱{b.cost:,.2f}", fg=C["success"]
        )

        self.app.current_rider = assign_rider()          # ← assign a random rider
        self.app.rider_screen.on_show()
        self.app.slides.push(self.app.rider_screen)      # ← slide to RiderScreen
        # reset drop-off
        self._dc = None
        self._km = 0.0
        if self._route and HAS_MAP and hasattr(self, "map_w"):
            try:
                self._route.delete()
            except Exception:
                pass
            self._route = None
        if self._mk_drop and HAS_MAP and hasattr(self, "map_w"):
            try:
                self._mk_drop.delete()
            except Exception:
                pass
            self._mk_drop = None
        self.app.dropoff_var.set("")
        self.drop_e.delete(0, "end")
        self.drop_e.insert(0, "Search drop-off...")
        self.drop_e.config(fg=C["muted"])
        self.lbl_dist.config(text="")
        self.lbl_cost.config(text="₱ —")
        self.lbl_cost_sub.config(text="")

    # ── booking list ──────────────────────────────────────────────────────
    def _refresh_list(self) -> None:
        for w in self.list_f.winfo_children():
            w.destroy()
        if not self.app.bookings:
            tk.Label(self.list_f, text="No bookings yet.",
                     bg=C["surface"], fg=C["muted"],
                     font=(F, 9)).pack(pady=8)
            return
        for b in reversed(self.app.bookings):
            self._booking_card(b)
        self.after(50, lambda: self._bind_scroll(self.list_f))

    def _booking_card(self, b) -> None:
        card: tk.Frame = tk.Frame(
            self.list_f, bg=C["card"],
            highlightbackground=C["border"], highlightthickness=1,
        )
        card.pack(fill="x", pady=4)

        top: tk.Frame = tk.Frame(card, bg=C["card"])
        top.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(top, text=f"{b.emoji} {b.vtype}  #{b.bid}",
                 bg=C["card"], fg=C["text"],
                 font=(F, 9, "bold")).pack(side="left")
        tk.Label(top, text=f"₱{b.cost:,.2f}",
                 bg=C["card"], fg=C["primary"],
                 font=(F, 9, "bold")).pack(side="right")

        tk.Label(card, text=f"{b.pick} → {b.drop}",
                 bg=C["card"], fg=C["muted"], font=(F, 8),
                 wraplength=250, anchor="w").pack(fill="x", padx=10)
        tk.Label(card, text=f"{b.km} km · {b.ts}",
                 bg=C["card"], fg=C["muted"], font=(F, 7),
                 anchor="w").pack(fill="x", padx=10)

        act: tk.Frame = tk.Frame(card, bg=C["card"])
        act.pack(fill="x", padx=10, pady=(4, 8))
        tk.Button(act, text="📄 Receipt",
                  bg=C["primary_lt"], fg=C["primary"],
                  font=(F, 8), relief="flat", cursor="hand2",
                  padx=6, pady=3,
                  command=lambda bk=b: self._receipt(bk)).pack(side="left", padx=(0, 4))
        tk.Button(act, text="✕ Cancel",
                  bg="#FEE2E2", fg=C["danger"],
                  font=(F, 8), relief="flat", cursor="hand2",
                  padx=6, pady=3,
                  command=lambda bk=b: self._cancel(bk)).pack(side="left")

    def _go_all_bookings(self) -> None:
        self.app.all_bookings_screen.on_show()
        self.app.slides.push(self.app.all_bookings_screen)

    def _receipt(self, b) -> None:
        if not HAS_DOCX:
            messagebox.showerror("INTERide", "Install python-docx first.")
            return
        path: str = f"INTERide_Receipt_{b.bid}.docx"
        make_receipt(b, path)
        messagebox.showinfo("Receipt Saved", f"Saved as:\n{os.path.abspath(path)}")

    def _cancel(self, b) -> None:
        if messagebox.askyesno(
            "Cancel", f"Cancel #{b.bid} for {b.user}?\n{b.vtype} · ₱{b.cost:,.2f}"
        ):
            self.app.bookings.remove(b)
            save_all(self.app.bookings)
            self._refresh_list()


# ══════════════════════════════════════════════════════════════════════════
#  SCREEN 6 — All Bookings
# ══════════════════════════════════════════════════════════════════════════
class AllBookingsScreen(Screen):
    """Full treeview table of all bookings with receipt & cancel actions."""

    def __init__(self, app: object) -> None:
        super().__init__(app)
        self._build()

    def _build(self) -> None:
        # top bar
        top: tk.Frame = tk.Frame(self, bg=C["dark"], height=54)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Button(top, text="←", bg=C["dark"], fg=C["white"],
                  font=(F, 14), relief="flat", cursor="hand2",
                  command=self.app.slides.pop).pack(side="left", padx=12, pady=10)
        tk.Label(top, text="All Bookings",
                 bg=C["dark"], fg=C["white"],
                 font=(F, 14, "bold")).pack(side="left", pady=10)

        self.lbl_count: tk.Label = tk.Label(
            top, text="", bg=C["primary"], fg=C["white"], font=(F, 9, "bold")
        )
        self.lbl_count.pack(side="right", padx=16, pady=16)

        # gradient strip
        strip: tk.Canvas = tk.Canvas(self, height=6, highlightthickness=0)
        strip.pack(fill="x")
        strip.bind(
            "<Configure>",
            lambda e: draw_gradient(
                strip, e.width, e.height, C["grad_top"], C["accent"], horizontal=True
            ),
        )

        # summary bar
        self.summary_f: tk.Frame = tk.Frame(self, bg=C["primary_lt"])
        self.summary_f.pack(fill="x")
        self.lbl_summary: tk.Label = tk.Label(
            self.summary_f, text="",
            bg=C["primary_lt"], fg=C["primary"],
            font=(F, 9, "bold"), anchor="w",
        )
        self.lbl_summary.pack(fill="x", padx=20, pady=8)

        # treeview
        tree_frame: tk.Frame = tk.Frame(self, bg=C["bg"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=12)

        style: ttk.Style = ttk.Style()
        style.theme_use("clam")
        style.configure("INTERide.Treeview",
                        background=C["surface"], foreground=C["text"],
                        rowheight=34, fieldbackground=C["surface"],
                        font=(F, 9), borderwidth=0)
        style.configure("INTERide.Treeview.Heading",
                        background=C["primary"], foreground=C["white"],
                        font=(F, 9, "bold"), relief="flat")
        style.map("INTERide.Treeview",
                  background=[("selected", C["primary_lt"])],
                  foreground=[("selected", C["primary"])])

        cols: tuple = ("ID", "Passenger", "Vehicle", "Pickup",
                       "Drop-off", "Distance", "Fare", "Date & Time")
        self.tree: ttk.Treeview = ttk.Treeview(
            tree_frame, columns=cols,
            show="headings", style="INTERide.Treeview", selectmode="browse",
        )

        widths:  List[int] = [80, 120, 70, 160, 160, 80, 90, 130]
        anchors: tuple     = ("center", "w", "center", "w", "w", "center", "center", "center")
        for col, w, anc in zip(cols, widths, anchors):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anc, stretch=False)

        vsb: ttk.Scrollbar = ttk.Scrollbar(tree_frame, orient="vertical",   command=self.tree.yview)
        hsb: ttk.Scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal",  command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        def _tree_scroll(event: tk.Event) -> None:
            self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.tree.bind("<MouseWheel>", _tree_scroll)
        self.tree.bind("<Button-4>", lambda e: self.tree.yview_scroll(-1, "units"))
        self.tree.bind("<Button-5>", lambda e: self.tree.yview_scroll(1,  "units"))

        self.tree.tag_configure("odd",       background=C["surface"])
        self.tree.tag_configure("even",      background=C["bg"])
        self.tree.tag_configure("cancelled", background="#FEE2E2", foreground="#991B1B")

        # action bar
        act_bar: tk.Frame = tk.Frame(self, bg=C["bg"])
        act_bar.pack(fill="x", padx=20, pady=(0, 14))

        self.btn_receipt: tk.Button = self.btn(
            act_bar, "📄 Save Receipt (.docx)",
            self._receipt_selected, bg=C["primary"], pady=9, font_size=9,
        )
        self.btn_receipt.pack(side="left", padx=(0, 8))

        self.btn_cancel: tk.Button = self.btn(
            act_bar, "✕ Cancel Selected",
            self._cancel_selected, bg=C["danger"], pady=9, font_size=9,
        )
        self.btn_cancel.pack(side="left")

        tk.Label(act_bar, text="← select a row first",
                 bg=C["bg"], fg=C["muted"],
                 font=(F, 8)).pack(side="left", padx=10)

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        bookings   = self.app.bookings
        total_cost: float = sum(b.cost for b in bookings)
        n: int = len(bookings)
        self.lbl_count.config(text=f"  {n} ride(s)  ")
        self.lbl_summary.config(
            text=f"Total bookings: {n}   ·   Total revenue: ₱{total_cost:,.2f}"
        )

        if not bookings:
            self.tree.insert("", "end",
                             values=("—", "No bookings yet", "—", "—", "—", "—", "—", "—"),
                             tags=("odd",))
            return

        for i, b in enumerate(reversed(bookings)):
            is_cancelled = getattr(b, "status", "confirmed") == "cancelled"
            if is_cancelled:
                tag = "cancelled"
            else:
                tag = "even" if i % 2 == 0 else "odd"
            fare_display = f"₱{b.cost:,.2f}" + (" [CANCELLED]" if is_cancelled else "")
            self.tree.insert("", "end", iid=b.bid, tags=(tag,),
                             values=(b.bid, b.user, f"{b.emoji} {b.vtype}",
                                     b.pick, b.drop,
                                     f"{b.km} km", fare_display, b.ts))

    def _selected_booking(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("INTERide", "Please select a booking first.")
            return None
        bid: str = sel[0]
        return next((b for b in self.app.bookings if b.bid == bid), None)

    def _receipt_selected(self) -> None:
        b = self._selected_booking()
        if not b:
            return
        if not HAS_DOCX:
            messagebox.showerror("INTERide", "Install python-docx first.")
            return
        path: str = f"INTERide_Receipt_{b.bid}.docx"
        make_receipt(b, path)
        messagebox.showinfo("Receipt Saved", f"Saved as:\n{os.path.abspath(path)}")

    def _cancel_selected(self) -> None:
        b = self._selected_booking()
        if not b:
            return
        if getattr(b, "status", "confirmed") == "cancelled":
            messagebox.showinfo("INTERide", "This booking is already cancelled.")
            return
        if messagebox.askyesno(
            "Cancel Booking",
            f"Cancel #{b.bid} for {b.user}?\n{b.vtype} · ₱{b.cost:,.2f}",
        ):
            b.cancel()
            save_all(self.app.bookings)
            self.app.booking_screen._refresh_list()
            self._refresh()


# ══════════════════════════════════════════════════════════════════════════
#  SCREEN 7 — About
# ══════════════════════════════════════════════════════════════════════════
class AboutScreen(Screen):
    """Group portfolio and documentation page."""

    def __init__(self, app: object) -> None:
        super().__init__(app)
        self._build()

    def _build(self) -> None:
        # top bar
        top: tk.Frame = tk.Frame(self, bg=C["dark"], height=54)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Button(top, text="←", bg=C["dark"], fg=C["white"],
                  font=(F, 14), relief="flat", cursor="hand2",
                  command=self.app.slides.pop).pack(side="left", padx=12, pady=10)
        tk.Label(top, text="About",
                 bg=C["dark"], fg=C["white"],
                 font=(F, 14, "bold")).pack(side="left", pady=10)

        # gradient header
        hdr_c: tk.Canvas = tk.Canvas(self, height=160, highlightthickness=0)
        hdr_c.pack(fill="x")
        hdr_c.bind(
            "<Configure>",
            lambda e: draw_gradient(hdr_c, e.width, e.height, C["grad_top"], C["accent"]),
        )
        tk.Label(hdr_c, text="INTERide",
                 bg=C["grad_top"], fg=C["white"],
                 font=(F, 28, "bold")).place(relx=0.5, y=60, anchor="center")
        tk.Label(hdr_c, text="Ride Booking System  ·  Group Project 1",
                 bg=C["grad_top"], fg="#BFDBFE",
                 font=(F, 10)).place(relx=0.5, y=100, anchor="center")

        # scrollable body
        body_c: tk.Canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0)
        sb: ttk.Scrollbar = ttk.Scrollbar(self, orient="vertical", command=body_c.yview)
        body_c.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        body_c.pack(fill="both", expand=True)

        inner: tk.Frame = tk.Frame(body_c, bg=C["bg"])
        win = body_c.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: body_c.configure(scrollregion=body_c.bbox("all")))
        body_c.bind("<Configure>",
                    lambda e: body_c.itemconfig(win, width=e.width))
        body_c.bind_all(
            "<MouseWheel>",
            lambda e: body_c.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        self._build_body(inner)

    def _build_body(self, f: tk.Frame) -> None:
        pad: dict = dict(padx=40)

        def section(title: str) -> None:
            tk.Label(f, text=title, bg=C["bg"], fg=C["primary"],
                     font=(F, 11, "bold"), anchor="w").pack(
                fill="x", **pad, pady=(28, 6))
            tk.Frame(f, bg=C["primary"], height=2).pack(fill="x", **pad)

        def card(parent=None) -> tk.Frame:
            p  = parent or f
            c: tk.Frame = tk.Frame(
                p, bg=C["surface"],
                highlightbackground=C["border"], highlightthickness=1,
            )
            c.pack(fill="x", **pad, pady=(10, 0))
            return c

        # ── group members ──
        section("👥  Group Members")

        import os
        from PIL import Image, ImageTk

        # Member data: (display_name, role, student_no, birthday, contact, email, photo_filename)
        members: List[Tuple[str, str, str, str, str, str]] = [
            ("Dorothy Ane C. Tapado",       "Code, Group Portfolio",  "10/16/2007", "9942454453", "tapadodorothyane@gmail.com",      "Dorothy_Ane_C__Tapado.png"),
            ("Manchor Jr. D. Lemindog",     "Code",                   "05/04/2007", "9503613168", "lemindog25@gmail.com",             "Manchor_JR_D__Lemindog.png"),
            ("Mandy Nicole B. Aragoncillo", "Code, File Operations",  "03/10/2007", "9300872976", "mandyaragoncillo10@gmail.com",     "Mandy_Nicole_B__Aragoncillo.png"),
            ("Princess Venice N. Maico",    "Code, File Operations",  "03/23/2007", "9911503809", "princessvenicemaico@gmail.com",    "Princess_Venice_N__Maico.png"),
            ("Gabriel Carl S. Calasang",    "Code",                   "09/09/2007", "9351156394", "gabrielcarlcalasang@gmail.com",    "Gabriel_Carl_S__Calasang.png"),
            ("Samantha Shan A. Laguine",    "Paper",                  "02/21/2007", "9352538287", "samshan.laguine@gmail.com",        "Samantha_Shan_A__Laguine.png"),
            ("Rudylyn S. Caspillan",        "Paper",                  "12/04/2006", "9942802268", "rudylyncaspillan06@gmail.com",     "Rudylyn_S__Caspillan.png"),
            ("Marian Andrea L. Murillo",    "Paper",                  "10/04/2007", "9952968312", "murillomarian.mm@gmail.com",       "Marian_Andrea_L__Murillo.png"),
            ("Gian Gabriel A. Racanday",    "Paper",                  "09/10/2006", "9915248168", "acederagian455@gmail.com",         "Gian_Gabriel_A__Racanday.png"),
        ]

        # Keep photo references alive to prevent garbage collection
        if not hasattr(self, "_photo_refs"):
            self._photo_refs: list = []

        PHOTO_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pictures")
        PHOTO_SIZE: int = 90

        for (full_name, role, bday, contact, email, photo_file) in members:
            mc: tk.Frame = card()
            row: tk.Frame = tk.Frame(mc, bg=C["surface"])
            row.pack(fill="x", padx=16, pady=14)

            # ── photo ──
            photo_path: str = os.path.join(PHOTO_DIR, photo_file)
            photo_lbl: tk.Label = tk.Label(row, bg=C["surface"])
            photo_lbl.pack(side="left", padx=(0, 16))
            try:
                img = Image.open(photo_path).resize((PHOTO_SIZE, PHOTO_SIZE), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self._photo_refs.append(tk_img)
                photo_lbl.config(image=tk_img, width=PHOTO_SIZE, height=PHOTO_SIZE)
            except Exception:
                photo_lbl.config(text="👤", font=(F, 32), width=4)

            # ── info ──
            info: tk.Frame = tk.Frame(row, bg=C["surface"])
            info.pack(side="left", fill="x", expand=True)

            tk.Label(info, text=full_name, bg=C["surface"], fg=C["text"],
                     font=(F, 12, "bold"), anchor="w").pack(anchor="w")
            tk.Label(info, text=f"Contribution: {role}", bg=C["surface"], fg=C["primary"],
                     font=(F, 9, "bold"), anchor="w").pack(anchor="w", pady=(2, 0))

            details_f: tk.Frame = tk.Frame(info, bg=C["surface"])
            details_f.pack(anchor="w", pady=(4, 0))

            for icon, val in [("🎂", bday), ("📞", contact), ("✉️", email)]:
                row_d: tk.Frame = tk.Frame(details_f, bg=C["surface"])
                row_d.pack(anchor="w")
                tk.Label(row_d, text=icon, bg=C["surface"],
                         font=(F, 9)).pack(side="left")
                tk.Label(row_d, text=f"  {val}", bg=C["surface"], fg=C["muted"],
                         font=(F, 9), anchor="w").pack(side="left")

        # ── project info ──
        section("📋  Project Information")
        info_items: List[Tuple[str, str]] = [
            ("Project",  "Ride Booking System"),
            ("Course",   "Object-Oriented Programming"),
            ("Deadline", "June 15, 2026"),
            ("Language", "Python 3.x"),
            ("GUI",      "Tkinter"),
            ("Map",      "OpenStreetMap + OSRM Routing"),
        ]
        ic: tk.Frame = card()
        for label, val in info_items:
            row2: tk.Frame = tk.Frame(ic, bg=C["surface"])
            row2.pack(fill="x", padx=16, pady=4)
            tk.Label(row2, text=label, bg=C["surface"], fg=C["muted"],
                     font=(F, 9), width=12, anchor="w").pack(side="left")
            tk.Label(row2, text=val, bg=C["surface"], fg=C["text"],
                     font=(F, 9, "bold"), anchor="w").pack(side="left")
        tk.Frame(ic, bg=C["surface"], height=8).pack()

        # ── features ──
        section("✨  Key Features")
        features: List[Tuple[str, str]] = [
            ("🚗  Vehicle Management",
             "Car, Van, and Bike — each with unique cost calculations via polymorphism."),
            ("📍  Real Map Routing",
             "OpenStreetMap with OSRM road-following routes and live distance/ETA."),
            ("📋  Booking System",
             "Book, view, and cancel rides. All data saved automatically to JSON."),
            ("📄  Receipt Export",
             "Generate a professional .docx receipt for any booking."),
            ("💾  Data Persistence",
             "Bookings are saved to file and restored on next launch."),
        ]
        for title, desc in features:
            fc: tk.Frame = card()
            tk.Label(fc, text=title, bg=C["surface"], fg=C["primary"],
                     font=(F, 10, "bold"), anchor="w").pack(
                fill="x", padx=16, pady=(12, 2))
            tk.Label(fc, text=desc, bg=C["surface"], fg=C["muted"],
                     font=(F, 9), anchor="w", wraplength=700).pack(
                fill="x", padx=16, pady=(0, 12))

        tk.Frame(f, bg=C["bg"], height=40).pack()

# ══════════════════════════════════════════════════════════════════════════
#  SCREEN  8 — Rider Info
# ══════════════════════════════════════════════════════════════════════════
class RiderScreen(Screen):
    def __init__(self, app: object) -> None:
        super().__init__(app)
        self._photo_ref = None   # keep reference so image isn't garbage collected
        self._build()

    def _build(self) -> None:
        # ── top bar ──
        top: tk.Frame = tk.Frame(self, bg=C["dark"], height=54)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="Your Rider is on the way! 🛵",
                 bg=C["dark"], fg=C["white"],
                 font=(F, 14, "bold")).pack(side="left", padx=16, pady=14)

        # ── main card ──
        outer: tk.Frame = tk.Frame(self, bg=C["bg"])
        outer.pack(fill="both", expand=True)

        card: tk.Frame = tk.Frame(
            outer, bg=C["surface"],
            highlightbackground=C["border"], highlightthickness=1,
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=380)

        # ── rider photo ──
        self.photo_lbl: tk.Label = tk.Label(card, bg=C["surface"])
        self.photo_lbl.pack(pady=(32, 12))

        # ── rider name ──
        self.name_lbl: tk.Label = tk.Label(
            card, text="",
            bg=C["surface"], fg=C["text"],
            font=(F, 22, "bold"),
        )
        self.name_lbl.pack()

        # ── rating ──
        self.rating_lbl: tk.Label = tk.Label(
            card, text="",
            bg=C["surface"], fg=C["muted"],
            font=(F, 11),
        )
        self.rating_lbl.pack(pady=(2, 0))

        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", padx=24, pady=16)

        # ── info rows ──
        info_f: tk.Frame = tk.Frame(card, bg=C["surface"])
        info_f.pack(fill="x", padx=32, pady=(0, 8))

        self.phone_lbl: tk.Label = tk.Label(
            info_f, text="",
            bg=C["surface"], fg=C["text"],
            font=(F, 11),
        )
        self.phone_lbl.pack(anchor="w", pady=2)

        self.vehicle_lbl: tk.Label = tk.Label(
            info_f, text="",
            bg=C["surface"], fg=C["text"],
            font=(F, 11),
        )
        self.vehicle_lbl.pack(anchor="w", pady=2)

        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", padx=24, pady=16)

        # ── done button ──
        self.btn(
            card, "Done  ✓",
            command=self._done,
            bg=C["success"], font_size=12, pady=13,
        ).pack(fill="x", padx=24, pady=(0, 8))

        # ── cancel booking button ──
        self.btn(
            card, "✕  Cancel Booking",
            command=self._cancel,
            bg=C["danger"], font_size=12, pady=13,
        ).pack(fill="x", padx=24, pady=(0, 28))

    def on_show(self) -> None:
        """Called every time this screen slides in — refreshes rider info."""
        rider: dict = self.app.current_rider
        vtype: str  = self.app.selected_vehicle.get()
        v           = V_MAP[vtype]

        # ── update labels ──
        self.name_lbl.config(text=rider["name"])
        self.rating_lbl.config(text=rider["rating"])
        self.phone_lbl.config(text=f"📞  {rider['phone']}")
        self.vehicle_lbl.config(text=f"{v.emoji}  {vtype}")

        # ── load photo ──
        photo_path: str = os.path.join(
            os.path.dirname(__file__), "pictures", rider["photo"]
        )
        try:
            img = Image.open(photo_path).resize((120, 120), Image.LANCZOS)
            self._photo_ref = ImageTk.PhotoImage(img)
            self.photo_lbl.config(image=self._photo_ref)
        except Exception:
            self.photo_lbl.config(image="", text="No Photo", font=(F, 12))

    def _done(self) -> None:
        """Return to booking screen and reset the drop-off state."""
        self.app.slides.pop()

    def _cancel(self) -> None:
        """Mark the latest booking as cancelled and return to booking screen."""
        if not self.app.bookings:
            self.app.slides.pop()
            return
        if messagebox.askyesno(
            "Cancel Booking",
            "Are you sure you want to cancel this booking?\nIt will be marked as cancelled in your history.",
        ):
            b = self.app.bookings[-1]
            b.cancel()
            save_all(self.app.bookings)
            self.app.slides.pop()
