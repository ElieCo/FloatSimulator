import numpy as np
from copy import deepcopy
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from typing import Optional
import time

class Point:
    _lines_ordered: bool = True
    def __init__(self, x: float, y: float, z: float):
        self.coords = np.array([x, y, z], dtype=float)
        self.lines = []
        self.surfaces = []

    def __str__(self):
        return str(self.coords)

    def __add__(self, other: "Point"):
        coords = self.coords + other.coords
        return Point(coords[0], coords[1], coords[2])

    def __truediv__(self, other: float):
        coords = self.coords / other
        return Point(coords[0], coords[1], coords[2])

    def __mul__(self, other: float):
        coords = self.coords * other
        return Point(coords[0], coords[1], coords[2])

    def __rmul__(self, other):
        return self.__mul__(other)

    def add_line(self, line: "Line"):
        self.lines.append(line)
        self._lines_ordered = False

    def add_surface(self, surface: "Surface"):
        self.surfaces.append(surface)

    def in_same_surface_than(self, p0: "Point", p1: Optional["Point"]):
        # print(p0, p1)
        # print(self)
        for s in self.surfaces:
            # for p in s.points:
            #     print(p)
            # print("---")
            if p0 in s.points and (p1 is None or p1 in s.points):
                return True
        return False

    def order_lines(self):
        if self._lines_ordered:
            return

        # print(f"self {self}")
        # for l in self.lines:
        #     print(f"one of my lines: {l.get_other_point(self)}")
        l = self.lines[0]
        ordered_lines = [l]
        # print(f"First line is {self} to {l.get_other_point(self)}")
        while len(ordered_lines) != len(self.lines):
            # print("==================")
            # print(len(self.lines))
            next_line = None
            for line in self.lines:
                # print("plop")
                if line not in ordered_lines:
                    # print(f"Test line: {self} to {line.get_other_point(self)}")
                    if self.in_same_surface_than(l.get_other_point(self), line.get_other_point(self)):
                        next_line = line
                        break
            if next_line is None:
                raise Exception("Nul.")
            else:
                l = next_line
                ordered_lines.append(l)
                # print(f"Choosen next line is {self} to {l.get_other_point(self)}")


        self._lines_ordered = True
        self.lines = ordered_lines


class Line:
    def __init__(self, p1: Point, p2: Point):
        self.points = [p1, p2]

    def get_other_point(self, p: Point):
        if p == self.points[0]:
            return self.points[1]
        else:
            return self.points[0]


class Surface:
    def __init__(self, points: list[Point]):
        self.points = points

    def __str__(self):
        s = "Surface defined by points:\n"
        for p in self.points:
            s += f"\t{p}"
        return s


class Volume:
    def __init__(self):
        self.points = []
        self.lines = []
        self.surfaces = []

        self.volume = 0
        self.vol_center = Point(0, 0, 0)

    def add_point(self, p: Point):
        if not self._contains_point(p):
            self.points.append(p)

    def add_line(self, p1: Point, p2: Point):
        if self._contains_line(p1, p2):
            return

        line = Line(p1, p2)
        p1.add_line(line)
        p2.add_line(line)
        self.lines.append(line)

    def add_surface(self, points: list[Point]):
        if self._contains_surface(points):
            return

        s = Surface(points)
        for i in range(len(points)):
            p = points[i]
            self.add_point(p)
            self.add_line(p, points[i-1])
            p.add_surface(s)
        self.surfaces.append(s)

    def display_on(self, ax, color="cyan"):
        s_points = []
        for s in self.surfaces:
            X = np.array([p.coords[0] for p in s.points])
            Y = np.array([p.coords[1] for p in s.points])
            Z = np.array([p.coords[2] for p in s.points])
            ax.scatter3D(X, Y, Z, color=color)
            s_points.append([p.coords for p in s.points])
        for line in self.lines:
            X = [p.coords[0] for p in line.points]
            Y = [p.coords[1] for p in line.points]
            Z = [p.coords[2] for p in line.points]
            ax.plot(X, Y, Z, color=color)
        return ax.add_collection3d(Poly3DCollection(s_points, facecolors=color, alpha=.25))

    def display(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.set_aspect('equal')

        self.display_on(ax)

        plt.show()

    def get_tetrahedrons(self) -> list["Tetrahedron"]:

        vol = deepcopy(self)

        pyramides: list["Tetrahedron"] = []

        while len(vol.points) >= 4:
            # vol.display()

            # Get a point
            p0 = vol.points[0]

            # Ordonate the lines
            p0.order_lines()

            # Create all the pyramides
            if len(p0.lines) >= 3:
                for i in range(len(p0.lines) - 2):

                    p1 = p0.lines[0].get_other_point(p0)
                    p2 = p0.lines[i+1].get_other_point(p0)
                    p3 = p0.lines[i+2].get_other_point(p0)
                    if not vol._contains_line(p1, p2):
                        vol.add_line(p1, p2)
                    if not vol._contains_line(p3, p2):
                        vol.add_line(p3, p2)
                    if not vol._contains_line(p1, p3):
                        vol.add_line(p1, p3)
                    if not vol._contains_surface([p1, p2, p3]):
                        vol.add_surface([p1, p2, p3])

                    p = Tetrahedron(p0, p1, p2, p3)
                    pyramides.append(p)

            else:
                break

            # Remove this point
            vol.remove_point(p0)

            # If a point have now less than 3 lines, remove it to
            for p in vol.points:
                if len(p.lines) < 3:
                    vol.remove_point(p)

        # pyramides.append(vol)
        return pyramides

    def remove_point(self, p):
        # Remove all this lines from the volume and the other points
        for line in p.lines:
            self.lines.remove(line)
            line.get_other_point(p).lines.remove(line)

        # Remove this point
        self.points.remove(p)

    def _contains_point(self, p):
        return p in self.points

    def _contains_line(self, p1, p2):
        for line in self.lines:
            if p1 in line.points and p2 in line.points:
                return True

        return False

    def _contains_surface(self, points):
        for s in self.surfaces:
            all_in = True
            for p in points:
                if p not in s.points:
                    all_in = False
                    break
            if all_in:
                return True

        return False

    def get_volume_n_center(self):
        self._calculate_volume()
        return self.volume, self.vol_center

    def _calculate_volume(self):
        tetrahedrons = self.get_tetrahedrons()
        volumes = []
        vol_centers = []
        for tetra in tetrahedrons:
            volumes.append(tetra.get_volume())
            vol_centers.append(tetra.get_center())
        self.volume = 0
        self.vol_center = Point(0, 0, 0)
        for i in range(len(volumes)):
            self.volume += volumes[i]
            if volumes[i] > 0:
                self.vol_center += vol_centers[i] * volumes[i]
        self.vol_center /= self.volume


class Tetrahedron(Volume):
    def __init__(self, _p0, _p1, _p2, _p3):
        Volume.__init__(self)
        p0 = Point(*_p0.coords)
        p1 = Point(*_p1.coords)
        p2 = Point(*_p2.coords)
        p3 = Point(*_p3.coords)
        self._points = [p0, p1, p2, p3]

        self.add_surface(deepcopy([p0, p1, p2]))
        self.add_surface(deepcopy([p0, p1, p3]))
        self.add_surface(deepcopy([p0, p2, p3]))
        self.add_surface(deepcopy([p1, p2, p3]))

        self._vol_center = self._calculate_center()
        self._volume = self._calculate_volume()

    def get_center(self) -> Point:
        return self._vol_center

    def get_volume(self) -> float:
        return self._volume

    def _calculate_center(self) -> Point:
        x = y = z = 0
        for p in self._points:
            x += p.coords[0] / 4
            y += p.coords[1] / 4
            z += p.coords[2] / 4
        return Point(x, y, z)

    def _determinant_3x3(self, m):
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) -
                m[1][0] * (m[0][1] * m[2][2] - m[0][2] * m[2][1]) +
                m[2][0] * (m[0][1] * m[1][2] - m[0][2] * m[1][1]))


    def _subtract(self, a, b):
        return (a[0] - b[0],
                a[1] - b[1],
                a[2] - b[2])

    def _calculate_volume(self):
        a = self._points[0].coords
        b = self._points[1].coords
        c = self._points[2].coords
        d = self._points[3].coords
        return (abs(self._determinant_3x3((self._subtract(a, b),
                                           self._subtract(b, c),
                                           self._subtract(c, d),
                                           ))) / 6.0)


class RectangularCuboid(Volume):
    def __init__(self, len_x: float, len_y: float, len_z: float):
        Volume.__init__(self)

        self._size = [len_x, len_y, len_z]

        p0 = Point(0, 0, 0)
        p1 = Point(0, 0, len_z)
        p2 = Point(0, len_y, len_z)
        p3 = Point(0, len_y, 0)
        p4 = Point(len_x, 0, 0)
        p5 = Point(len_x, 0, len_z)
        p6 = Point(len_x, len_y, len_z)
        p7 = Point(len_x, len_y, 0)
        self.add_surface([p0, p1, p2, p3])
        self.add_surface([p4, p5, p6, p7])
        self.add_surface([p0, p1, p5, p4])
        self.add_surface([p1, p2, p6, p5])
        self.add_surface([p2, p3, p7, p6])
        self.add_surface([p3, p0, p4, p7])

    # def get_volume(self):
    #     return abs(self.size[0] * self.size[0] * self.size[0])


def main():
    # cube = RectangularCuboid(1/2, 0.5/2, 2/2)
    cube = RectangularCuboid(1, 1, 0.5)
    vol, center = cube.get_volume_n_center()
    print(vol, str(center))

    # cube.display()

    tetrahedrons = cube.get_tetrahedrons()

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.set_aspect('equal')

    vol_total = 0

    polygons = []
    for tetrahedron in tetrahedrons:
        vol_total += tetrahedron.get_volume()

        polygon = tetrahedron.display_on(ax, [np.random.randint(0, 100)/100, np.random.randint(0, 100)/100, np.random.randint(0, 100)/100])
        polygons.append(polygon)

    print("Volume total:", vol_total)

    plt.show()

if __name__ == "__main__":
    main()
