"""Two generic visuals for environment verification and style adaptation."""
from manim import *
from talk_style import TalkSlide, heading, math, text, lattice, PRIMARY, SECONDARY, VIOLATION, NOTE


class Translation(TalkSlide):
    def construct(self):
        self.add(heading("A pattern and its translation"))
        grid, pos = lattice(range(5), range(4), origin=LEFT * 4.6 + DOWN * 1.3)
        self.add(grid)
        points = [(0, 0), (1, 0), (0, 1)]
        names = [r"1", r"x", r"y"]
        terms = math(r"P =", "1", "+", "x", "+", "y").move_to(RIGHT * 2.4 + UP * 0.75)
        self.play(Write(terms[0]))
        objects = VGroup()
        for index, (point, name) in enumerate(zip(points, names)):
            dot = Dot(pos(*point), radius=0.09, color=PRIMARY)
            label = math(name, size=28).next_to(dot, DOWN, buff=0.13)
            objects.add(dot, label)
            self.play(FadeIn(dot), Write(label), run_time=0.6)
            self.play(TransformFromCopy(label, terms[1 + index * 2]), run_time=0.6)
            if index:
                self.add(terms[index * 2])
        self.next_slide()

        target = math(r"xP =", "x", "+", r"x^2", "+", "xy").move_to(terms)
        cue = Arrow(pos(0, 2), pos(1, 2), color=SECONDARY)
        explanation = text(r"translation by one site along $x$", size=28).next_to(target, DOWN, buff=0.5)
        self.play(GrowArrow(cue), FadeIn(explanation), run_time=0.6)
        shifted_names = [r"x", r"x^2", r"xy"]
        movement = []
        for index, name in enumerate(shifted_names):
            movement.append(objects[index * 2].animate.shift(RIGHT * 0.65))
            movement.append(Transform(objects[index * 2 + 1], math(name, size=28).move_to(objects[index * 2 + 1].get_center() + RIGHT * 0.65)))
        self.play(*movement, Transform(terms, target), run_time=1.0)
        self.wait(0.3)


class Cancellation(TalkSlide):
    def construct(self):
        self.add(heading(r"Overlap parity in $\mathbb F_2$"))
        grid, pos = lattice(range(5), range(3), origin=LEFT * 4.2 + DOWN)
        self.add(grid)
        first = VGroup(Dot(pos(0, 1), radius=0.10, color=PRIMARY),
                       Dot(pos(1, 1), radius=0.10, color=PRIMARY))
        second = VGroup(Square(side_length=0.24, color=SECONDARY).move_to(pos(1, 1)),
                        Square(side_length=0.24, color=SECONDARY).move_to(pos(2, 1)))
        equation = math(r"(1+x)+(x+x^2)").move_to(RIGHT * 2.3 + UP * 0.6)
        self.play(FadeIn(first), Write(equation), run_time=0.8)
        self.play(FadeIn(second), run_time=0.7)
        self.next_slide()

        caption = text(r"the overlapping site is counted twice", size=27).next_to(equation, DOWN, buff=0.55)
        self.play(Indicate(first[1], color=VIOLATION), Indicate(second[0], color=VIOLATION), FadeIn(caption))
        self.play(FadeOut(first[1]), FadeOut(second[0]),
                  Transform(equation, math(r"1+x^2").move_to(equation)), run_time=0.8)
        self.play(Transform(second[1], Dot(pos(2, 1), radius=0.10, color=PRIMARY)))
        self.wait(0.3)
