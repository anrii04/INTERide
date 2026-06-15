"""
widgets.py
INTERide — Reusable UI primitives:
  • draw_gradient  — paints a gradient on a tk.Canvas
  • SlideManager   — animated screen-stack (push / pop)
  • Screen         — base Frame every screen inherits from
"""

from typing import List, Optional
import tkinter as tk
from tkinter import ttk

from config import C, F


# ══════════════════════════════════════════════════════════════════════════
#  GRADIENT CANVAS helper
# ══════════════════════════════════════════════════════════════════════════
def draw_gradient(
    canvas:     tk.Canvas,
    w:          int,
    h:          int,
    c1:         str = "#1E40AF",
    c2:         str = "#3B82F6",
    horizontal: bool = False,
) -> None:
    """Draw a vertical (or horizontal) gradient on *canvas*."""
    steps: int = 80
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    canvas.delete("grad")
    for i in range(steps):
        t:   float = i / steps
        r:   int   = int(r1 + (r2 - r1) * t)
        g:   int   = int(g1 + (g2 - g1) * t)
        b:   int   = int(b1 + (b2 - b1) * t)
        col: str   = f"#{r:02x}{g:02x}{b:02x}"
        if horizontal:
            x0 = int(w * i / steps);  x1 = int(w * (i + 1) / steps)
            canvas.create_rectangle(x0, 0, x1, h, fill=col, outline=col, tags="grad")
        else:
            y0 = int(h * i / steps);  y1 = int(h * (i + 1) / steps)
            canvas.create_rectangle(0, y0, w, y1, fill=col, outline=col, tags="grad")


# ══════════════════════════════════════════════════════════════════════════
#  SLIDE MANAGER
# ══════════════════════════════════════════════════════════════════════════
class SlideManager:
    """
    Manages a stack of full-window frames and slides between them.
    All frames are stacked at x=0; off-screen frames sit at x=±width.
    """
    SPEED: int = 16   # ms per animation frame
    STEP:  int = 60   # px per animation frame

    def __init__(self, root: tk.Tk) -> None:
        self.root:   tk.Tk          = root
        self.width:  int            = root.winfo_width() or 900
        self.height: int            = root.winfo_height() or 660
        self.stack:  List[tk.Frame] = []
        self.busy:   bool           = False
        root.bind("<Configure>", self._on_resize)

    def _on_resize(self, e: tk.Event) -> None:
        if e.widget is self.root:
            self.width  = e.width
            self.height = e.height

    def _place(self, frame: tk.Frame, x: int) -> None:
        frame.place(x=x, y=0, width=self.width, height=self.height)

    # ── push ──────────────────────────────────────────────────────────────
    def push(
        self,
        frame:     tk.Frame,
        direction: str              = "left",
        on_done:   Optional[callable ]  = None,
    ) -> None:
        """Slide *frame* in from the right (direction='left') or left."""
        if self.busy:
            return
        sign:           int = 1 if direction == "left" else -1
        incoming_start: int = self.width * sign

        self._place(frame, incoming_start)
        frame.lift()

        def _finish_push() -> None:
            self.stack.append(frame)
            if on_done:
                on_done()

        if self.stack:
            current = self.stack[-1]
            self._animate_slide(
                outgoing=(current, 0, -self.width * sign),
                incoming=(frame,  incoming_start, 0),
                on_done=_finish_push,
            )
        else:
            self._animate_slide(
                outgoing=None,
                incoming=(frame, incoming_start, 0),
                on_done=_finish_push,
            )

    # ── pop ───────────────────────────────────────────────────────────────
    def pop(self) -> None:
        if self.busy or len(self.stack) < 2:
            return
        current:  tk.Frame = self.stack[-1]
        previous: tk.Frame = self.stack[-2]

        self._place(previous, -self.width)
        previous.lift()
        current.lift()

        self._animate_slide(
            outgoing=(current,  0,            self.width),
            incoming=(previous, -self.width,  0),
            on_done=lambda: (
                self.stack.pop(),
                self.stack[-1].on_show() if hasattr(self.stack[-1], "on_show") else None
            ),
        )

    # ── internal animation loop ───────────────────────────────────────────
    def _animate_slide(
        self,
        outgoing: Optional[tuple ],
        incoming: tuple,
        on_done:  callable,
    ) -> None:
        self.busy = True
        out_frame = out_x = out_target = None
        if outgoing:
            out_frame, out_x, out_target = outgoing
        in_frame, in_x, in_target = incoming

        def step() -> None:
            nonlocal out_x, in_x
            done: bool = True

            if out_frame:
                diff = out_target - out_x
                move = max(-self.STEP, min(self.STEP, diff))
                if abs(diff) > 2:
                    out_x += move
                    self._place(out_frame, int(out_x))
                    done = False

            diff2 = in_target - in_x
            move2 = max(-self.STEP, min(self.STEP, diff2))
            if abs(diff2) > 2:
                in_x += move2
                self._place(in_frame, int(in_x))
                done = False

            if done:
                if out_frame:
                    self._place(out_frame, int(out_target))
                self._place(in_frame, 0)
                self.busy = False
                on_done()
            else:
                self.root.after(self.SPEED, step)

        self.root.after(self.SPEED, step)


# ══════════════════════════════════════════════════════════════════════════
#  SCREEN BASE
# ══════════════════════════════════════════════════════════════════════════
class Screen(tk.Frame):
    """Base class for every INTERide screen."""

    def __init__(self, app: object) -> None:
        super().__init__(app.root, bg=C["bg"])
        self.app = app

    # ── factory helpers ───────────────────────────────────────────────────
    def btn(
        self,
        parent:    tk.Widget,
        text:      str,
        command:   callable,
        bg:        Optional[str ] = None,
        fg:        Optional[str ] = None,
        font_size: int        = 11,
        bold:      bool       = True,
        pady:      int        = 12,
        padx:      int        = 0,
        width:     int        = 0,
    ) -> tk.Button:
        bg_c:   str = bg or C["primary"]
        fg_c:   str = fg or C["white"]
        weight: str = "bold" if bold else "normal"
        b: tk.Button = tk.Button(
            parent, text=text, command=command,
            bg=bg_c, fg=fg_c, relief="flat", cursor="hand2",
            font=(F, font_size, weight),
            pady=pady, padx=padx or 20,
            activebackground=C["primary2"],
            activeforeground=C["white"],
            bd=0,
        )
        if width:
            b.config(width=width)
        return b

    def entry(
        self,
        parent:       tk.Widget,
        textvariable: tk.StringVar,
        placeholder:  str  = "",
        font_size:    int  = 13,
        center:       bool = False,
    ) -> tk.Entry:
        justify: str = "center" if center else "left"
        e: tk.Entry = tk.Entry(
            parent, textvariable=textvariable,
            bg=C["surface"], fg=C["text"],
            font=(F, font_size), relief="flat",
            justify=justify,
            highlightbackground=C["border"],
            highlightthickness=2,
            insertbackground=C["primary"],
        )
        if placeholder and not textvariable.get():
            e.insert(0, placeholder)
            e.config(fg=C["muted"])

            def fi(ev: tk.Event) -> None:
                if e.get() == placeholder:
                    e.delete(0, "end")
                    e.config(fg=C["text"])

            def fo(ev: tk.Event) -> None:
                if not e.get():
                    e.insert(0, placeholder)
                    e.config(fg=C["muted"])

            e.bind("<FocusIn>",  fi)
            e.bind("<FocusOut>", fo)
        return e
