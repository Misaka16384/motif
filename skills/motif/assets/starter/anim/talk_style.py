"""Generic visual helpers; adapt semantic roles to the research topic."""
import os
from manim import (
    Animation, Dot, MathTex, Tex, VGroup, Wait, config, BLUE, TEAL, RED,
    GREEN, YELLOW, GREY_B, GREY_D, UP, LEFT,
)
from manim.animation.animation import prepare_animation
from manim_slides import Slide

PRIMARY = "#58C4DD"
SECONDARY = "#5CD0B3"
VIOLATION = "#FC6255"
ALLOWED = "#83C167"
HIGHLIGHT = "#FFFF00"
NOTE = GREY_B
PACE = float(os.environ.get("MOTIF_PACE", "0.7"))
config.background_color = os.environ.get("MOTIF_BACKGROUND", "#000000")
FOREGROUND = os.environ.get("MOTIF_FOREGROUND", "#FFFFFF")


class TalkSlide(Slide):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("random_seed", int(os.environ.get("MOTIF_SEED", "0")))
        super().__init__(*args, **kwargs)

    def play(self, *animations, **kwargs):
        # Scene.wait calls play(Wait(...)), so waits are scaled here exactly once.
        if "run_time" in kwargs:
            kwargs["run_time"] *= PACE
            return super().play(*animations, **kwargs)
        else:
            prepared = [prepare_animation(a) for a in animations]
            original = [a.run_time for a in prepared]
            try:
                for animation, duration in zip(prepared, original):
                    animation.run_time = duration * PACE
                return super().play(*prepared, **kwargs)
            finally:
                for animation, duration in zip(prepared, original):
                    animation.run_time = duration

    def next_slide(self, *args, **kwargs):
        # Bypass our pacing override to record the completed state before pausing.
        super().play(Wait(0.1))
        self._layout_snapshot()
        return super().next_slide(*args, **kwargs)

    def tear_down(self):
        self._layout_snapshot()
        return super().tear_down()

    def _layout_snapshot(self):
        if os.environ.get("MOTIF_QA_FILE"):
            from layout_probe import snapshot
            snapshot(self)


def heading(text, size=38):
    return Tex(text, font_size=size, color=FOREGROUND).to_corner(UP + LEFT, buff=0.42)


def math(*strings, size=38, **kwargs):
    return MathTex(*strings, font_size=size, color=FOREGROUND, **kwargs)


def text(string, size=30, color=None):
    return Tex(string, font_size=size, color=color or FOREGROUND)


def lattice(x_range, y_range, spacing=0.65, origin=LEFT * 3):
    def position(x, y):
        return origin + spacing * (x * __import__('numpy').array([1, 0, 0]) + y * UP)
    dots = VGroup(*(Dot(position(x, y), radius=0.026, color=GREY_D)
                    for x in x_range for y in y_range))
    return dots, position
