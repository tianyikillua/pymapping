import numpy as np
import pytest

import pygmsh
import pymapping


def mesh_TUB(h, recombine=False):
    geom = pygmsh.built_in.Geometry()
    polygon = geom.add_polygon([[1 / 3, 1 / 3, 0], [1, 0, 0], [0.5, 0.5, 0]], lcar=h)
    if recombine:
        geom.add_raw_code("Recombine Surface {%s};" % polygon.surface.id)
    mesh = pygmsh.generate_mesh(geom, dim=2, verbose=False, prune_z_0=True)
    for celltype in ["vertex", "line"]:
        mesh.cells.pop(celltype, None)
        mesh.cell_data.pop(celltype, None)
    return mesh


mesh_source = mesh_TUB(0.01, recombine=True)
f = 2 * mesh_source.points[:, 0] + mesh_source.points[:, 1]
mesh_source.point_data = {"f(x)": f}
for celltype in mesh_source.cells:
    array = np.zeros(len(mesh_source.cells[celltype]))
    for i, cell in enumerate(mesh_source.cells[celltype]):
        centroid = np.mean(mesh_source.points[cell], axis=0)
        f = 2 * centroid[0] + centroid[1]
        array[i] = f
    mesh_source.cell_data[celltype] = {"f(x)": array}

mesh_target = mesh_TUB(0.02, recombine=True)
remap = pymapping.Remapper(verbose=False)


@pytest.mark.parametrize(
    "method", ["P1P1", "P1P0", "P0P1", "P0P0"])
def test_TUB_triangle(method):
    remap.prepare(mesh_source, mesh_target, method=method, intersection_type="Triangulation")
    res = remap.transfer("f(x)")

    integral_source = remap.field_source.integral(0, True)
    integral_target = res.field_target.integral(0, True)
    assert np.isclose(integral_source, integral_target, rtol=1e-4)


def test_cli():
    import tempfile
    import meshio

    mesh_source_file = tempfile.NamedTemporaryFile(suffix=".vtu").name
    mesh_target_file = tempfile.NamedTemporaryFile(suffix=".vtu").name
    meshio.write(mesh_source_file, mesh_source)
    meshio.write(mesh_target_file, mesh_target)

    outfile = tempfile.NamedTemporaryFile(suffix=".npy").name
    pymapping.cli.main(
        [
            mesh_source_file,
            mesh_target_file,
            "f(x)",
            outfile,
            "--method",
            "P1P0",
            "--intersection_type",
            "Triangulation",
        ]
    )
