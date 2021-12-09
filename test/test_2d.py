import numpy as np
import pygmsh
import pytest

import pymapping


def mesh_TUB(h, recombine=False):
    with pygmsh.geo.Geometry() as geom:
        polygon = geom.add_polygon(
            [[1 / 3, 1 / 3, 0], [1, 0, 0], [0.5, 0.5, 0]], mesh_size=h
        )
        if recombine:
            geom.set_recombined_surfaces([polygon])
        mesh = geom.generate_mesh(dim=2, verbose=False)
    mesh.points = mesh.points[:, :2]
    pymapping.cleanup_mesh_meshio(mesh)
    return mesh


mesh_source = mesh_TUB(0.01, recombine=True)
f = 2 * mesh_source.points[:, 0] + mesh_source.points[:, 1]
mesh_source.point_data = {"f(x)": f}
mesh_source.cell_data["f(x)"] = []
for cells in mesh_source.cells:
    array = np.zeros(len(cells.data))
    for i, cell in enumerate(cells.data):
        centroid = np.mean(mesh_source.points[cell], axis=0)
        array[i] = 2 * centroid[0] + centroid[1]
    mesh_source.cell_data["f(x)"].append(array)

mesh_target = mesh_TUB(0.02, recombine=True)
mapper = pymapping.Mapper(verbose=False)


@pytest.mark.parametrize("method", ["P1P1", "P1P0", "P0P1", "P0P0"])
def test_TUB_triangle(method):
    mapper.prepare(
        mesh_source, mesh_target, method=method, intersection_type="Triangulation"
    )
    res = mapper.transfer("f(x)")

    integral_source = mapper.field_source.integral(0, True)
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
