import numpy as np
import medcoupling as mc

celltype_mc = {
    "line": mc.NORM_SEG2,
    "triangle": mc.NORM_TRI3,
    "quad": mc.NORM_QUAD4,
    "tetra": mc.NORM_TETRA4,
    "pyramid": mc.NORM_PYRA5,
    "hexahedron": mc.NORM_HEXA8
}

celltype_3d = ["tetra", "pyramid", "hexahedron"]
celltype_2d = ["triangle", "quad"]


def mesh_mc_from_meshio(mesh, check=False):
    """
    Convert a ``meshio`` mesh to a ``medcoupling`` mesh
    """
    # Determine mesh dimension
    celltypes = list(mesh.cells.keys())
    if len(set(celltype_3d).intersection(celltypes)) > 0:
        meshdim = 3
    elif len(set(celltype_2d).intersection(celltypes)) > 0:
        meshdim = 2
    else:
        meshdim = 1
    mesh_mc = mc.MEDCouplingUMesh("mesh", meshdim)

    # Point coordinates
    coords = mc.DataArrayDouble(mesh.points.copy())
    mesh_mc.setCoords(coords)

    # Cells
    conn = np.array([], dtype=np.int32)
    conn_index = np.array([], dtype=np.int32)
    ncells_cumsum = np.hstack([[0], np.cumsum([len(cells) for cells in mesh.cells.values()])])
    for i_celltype, celltype in enumerate(mesh.cells):
        celltype_ = celltype_mc[celltype]
        ncells_celltype, npoints_celltype = mesh.cells[celltype].shape
        col_celltype = celltype_ * np.ones((ncells_celltype, 1), dtype=np.int32)
        conn_celltype = np.hstack([col_celltype, mesh.cells[celltype]]).flatten()
        conn = np.hstack([conn, conn_celltype])
        conn_index_celltype = ncells_cumsum[i_celltype] + (1 + npoints_celltype) * np.arange(ncells_celltype, dtype=np.int32)
        conn_index = np.hstack([conn_index, conn_index_celltype])
    conn_index = np.hstack([conn_index, [len(conn)]]).astype(np.int32)
    conn = mc.DataArrayInt(conn.astype(np.int32))
    conn_index = mc.DataArrayInt(conn_index)
    mesh_mc.setConnectivity(conn, conn_index)

    if check:
        mesh_mc.checkConsistency()
    return mesh_mc


def field_mc_from_meshio(mesh, field_name, on="points", mesh_mc=None):
    """
    Todo:
        Currently the field must be defined on points (nodal field)
    """
    assert on in ["points", "cells"]
    if on == "points":
        field = mc.MEDCouplingFieldDouble(mc.ON_NODES, mc.NO_TIME)
    else:
        field = mc.MEDCouplingFieldDouble(mc.ON_CELLS, mc.NO_TIME)
    field.setName(field_name)
    if mesh_mc is None:
        mesh_mc = mesh_mc_from_meshio(mesh)
    field.setMesh(mesh_mc)
    field.setArray(mc.DataArrayDouble(mesh.point_data[field_name].copy()))
    field.setNature(mc.IntensiveMaximum)
    return field


class MappingResult:
    """
    Container class for mapped field on the target mesh
    """
    def __init__(self, field_target, mesh_target=None):
        self.field_target = field_target
        self.dis = self.field_target.getDiscretization()

        self.mesh_target = mesh_target

    def array(self):
        """
        Return the ``numpy`` array of the mapped field
        """
        return self.field_target.getArray().toNumPyArray()

    def discretization_points(self):
        """
        Return the location of discretization points on which
        the field array is defined
        """
        return self.dis.getLocalizationOfDiscValues(self.field_target.getMesh()).toNumPyArray()

    def export_vtk(self, vtkfile):
        """
        Export the mapped field to a VTK file
        """
        self.field_target.writeVTK(vtkfile)

    def mesh_meshio(self):
        """
        Return the ``meshio`` mesh object containing the
        mapped field
        """
        assert self.mesh_target is not None
        from copy import deepcopy
        mesh_target = deepcopy(self.mesh_target)
        name = self.field_target.getName()
        if self.dis.getRepr() == "P1":
            mesh_target.point_data[name] = self.array()
        else:
            raise NotImplementedError("P0 field not yet implemented")
        return mesh_target


class Remapper:
    """
    Class for Mapping finite element data between meshes

    Args:
        verbose (bool): Whehter print out progress information
    """
    def __init__(self, verbose=True):
        self.remap = mc.MEDCouplingRemapper()
        self.verbose = verbose

        self.mesh_source = None
        self.mesh_source_mc = None
        self.mesh_target = None
        self.mesh_target_mc = None
        self.field_source = None
        self.field_target = None

    def prepare(self, mesh_source, mesh_target, method="P1P0", intersection_type=None):
        """
        Prepare field mapping between meshes, must be run before
        :py:meth:`~.Remapper.transfer`. The source mesh must contain
        the field that you want to transfer to the target mesh.

        Args:
            mesh_source (meshio mesh): Source mesh
            mesh_target (meshio mesh): Target mesh
            method (str): Must be ``P1P0``, ``P1P1``, ``P0P0`` or ``P0P1``
            intersection_type (str): Intersection type depending on meshes and the method
        """
        # Select intersection type
        assert method in ["P1P0", "P1P1", "P0P0", "P0P1"]
        if intersection_type is not None:
            self.remap.setIntersectionType(eval("mc." + intersection_type))
        elif method[:2] == "P1":
            self.remap.setIntersectionType(mc.PointLocator)

        self._print("Loading source mesh...")
        self.mesh_source = mesh_source
        self.mesh_source_mc = mesh_mc_from_meshio(mesh_source)

        self._print("Loading target mesh...")
        self.mesh_target = mesh_target
        self.mesh_target_mc = mesh_mc_from_meshio(mesh_target)

        self._print("Preparing...")
        self.remap.prepare(self.mesh_source_mc, self.mesh_target_mc, method)

    def transfer(self, field_name, on="points"):
        """
        Transfer field from the source mesh to the target mesh, after
        :py:meth:`~.Remapper.prepare`.

        Args:
            field_name (str): The name of the field defined in the source mesh
            on (str): The support of the source field (``points`` or ``cells``)

        Todo:
            Currently the source field must be defined on points (nodal field)
        """
        self._print("Transfering...")
        self.field_source = field_mc_from_meshio(
            self.mesh_source, field_name, on=on, mesh_mc=self.mesh_source_mc)
        self.field_target = self.remap.transferField(self.field_source, dftValue=np.nan)
        self.field_target.setName(field_name)
        return MappingResult(self.field_target, self.mesh_target)

    def _print(self, blabla):
        if self.verbose:
            print(blabla)
