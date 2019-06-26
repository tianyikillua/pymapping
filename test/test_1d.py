import meshio
import pymapping
import pytest
import numpy as np


def mesh_unit_interval(N):
    points = np.linspace(0, 1, N)
    cells_line = np.array([(i, i + 1) for i in range(len(points) - 1)], dtype=int)
    cells = {"line": cells_line}
    return meshio.Mesh(points, cells)


mesh_source = mesh_unit_interval(100)
y = np.sin(2 * np.pi * mesh_source.points) + 0.5 * np.sin(6 * np.pi * mesh_source.points)
mesh_source.point_data = {"y": y}
mesh_target = mesh_unit_interval(10)
remap = pymapping.Remapper(verbose=False)


@pytest.mark.parametrize(
    "intersection_type", ["Triangulation", "PointLocator"])
def test_P1P1(intersection_type):
    remap.prepare(mesh_source, mesh_target, method="P1P1", intersection_type=intersection_type)
    res = remap.transfer("y")

    if intersection_type == "PointLocator":
        x_target = res.discretization_points()
        y_target_from_source = np.interp(x_target, mesh_source.points, y)
        assert np.allclose(y_target_from_source, res.array())


def test_P1P0():
    remap.prepare(mesh_source, mesh_target, method="P1P0", intersection_type="Triangulation")
    remap.transfer("y")
