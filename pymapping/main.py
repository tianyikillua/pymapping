from copy import deepcopy

import medcoupling as mc
import numpy as np
from meshio import CellBlock

meshio_to_mc_type = {
    "vertex": mc.NORM_POINT1,
    "line": mc.NORM_SEG2,
    "triangle": mc.NORM_TRI3,
    "quad": mc.NORM_QUAD4,
    "tetra": mc.NORM_TETRA4,
    "pyramid": mc.NORM_PYRA5,
    "hexahedron": mc.NORM_HEXA8,
}
mc_to_meshio_type = {v: k for k, v in meshio_to_mc_type.items()}

celltype_3d = ["tetra", "pyramid", "hexahedron"]
celltype_2d = ["triangle", "quad"]
celltype_1d = ["line"]
celltype_0d = ["vertex"]


def meshdim(mesh):
    """
    Determine the mesh dimension of a meshio mesh

    Returns:
        int: Mesh dimension
    """
    celltypes = list(mesh.cells_dict.keys())
    if len(set(celltype_3d).intersection(celltypes)) > 0:
        meshdim = 3
    elif len(set(celltype_2d).intersection(celltypes)) > 0:
        meshdim = 2
    else:
        meshdim = 1
    return meshdim


def cleanup_mesh_meshio(mesh):
    """
    Drop all cells with a lower dimension from a meshio mesh
    """
    meshdim_ = meshdim(mesh)
    if meshdim_ == 3:
        celltypes = celltype_2d + celltype_1d + celltype_0d
    elif meshdim_ == 2:
        celltypes = celltype_1d + celltype_0d
    else:
        celltypes = celltype_0d

    cells = mesh.cells_dict
    cell_data = mesh.cell_data_dict
    for celltype in celltypes:
        cells.pop(celltype, None)
    for key in cell_data:
        for celltype in celltypes:
            cell_data[key].pop(celltype, None)

    mesh.cells = []
    for celltype, data in cells.items():
        mesh.cells.append(CellBlock(celltype, data))
    for key in mesh.cell_data:
        mesh.cell_data[key] = list(cell_data[key].values())


def mesh_mc_from_meshio(mesh, check=False):
    """
    Convert a meshio mesh to a medcoupling mesh

    Args:
        mesh (meshio mesh): Mesh object
        check (bool): Check if the medcoupling mesh is consist
    """
    # Initialization
    mesh_mc = mc.MEDCouplingUMesh("mesh", meshdim(mesh))

    # Point coordinates
    coords = mc.DataArrayDouble(mesh.points.copy())
    mesh_mc.setCoords(coords)

    # Cells
    cells_dict = mesh.cells_dict
    conn = np.array([], dtype=np.int32)
    conn_index = np.array([], dtype=np.int32)
    for celltype in cells_dict:
        celltype_ = meshio_to_mc_type[celltype]
        ncells_celltype, npoints_celltype = cells_dict[celltype].shape
        col_celltype = celltype_ * np.ones((ncells_celltype, 1), dtype=np.int32)
        conn_celltype = np.hstack([col_celltype, cells_dict[celltype]]).flatten()
        conn_index_celltype = len(conn) + (1 + npoints_celltype) * np.arange(
            ncells_celltype, dtype=np.int32
        )
        conn = np.hstack([conn, conn_celltype])
        conn_index = np.hstack([conn_index, conn_index_celltype])
    conn_index = np.hstack([conn_index, [len(conn)]]).astype(np.int32)
    conn = mc.DataArrayInt(conn.astype(np.int32))
    conn_index = mc.DataArrayInt(conn_index)
    mesh_mc.setConnectivity(conn, conn_index)

    if check:
        mesh_mc.checkConsistency()
    return mesh_mc


def field_mc_from_meshio(
    mesh, field_name, on="points", mesh_mc=None, nature="IntensiveMaximum"
):
    """
    Convert a meshio field to a medcoupling field

    Args:
        mesh (meshio mesh): Mesh object
        field_name (str): Name of the field defined in the ``meshio`` mesh
        on (str): Support of the field (``points`` or ``cells``)
        mesh_mc (medcoupling mesh): MEDCoupling mesh of the current ``meshio`` mesh
        nature (str): Physical nature of the field (``IntensiveMaximum``, ``IntensiveConservation``, ``ExtensiveMaximum`` or ``ExtensiveConservation``)
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

    # Point fields
    if on == "points":
        assert field_name in mesh.point_data
        field.setArray(mc.DataArrayDouble(mesh.point_data[field_name].copy()))
    else:
        # Cell fields
        assert on == "cells"
        assert field_name in mesh.cell_data_dict
        array = None
        celltypes_mc = mesh_mc.getAllGeoTypesSorted()
        for celltype_mc in celltypes_mc:
            celltype = mc_to_meshio_type[celltype_mc]
            assert celltype in mesh.cell_data_dict[field_name]
            values = mesh.cell_data_dict[field_name][celltype]
            if array is None:
                array = values
            else:
                array = np.concatenate([array, values])
        field.setArray(mc.DataArrayDouble(array))

    field.setNature(eval("mc." + nature))
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
        return self.dis.getLocalizationOfDiscValues(
            self.field_target.getMesh()
        ).toNumPyArray()

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
        mesh_target = deepcopy(self.mesh_target)
        name = self.field_target.getName()

        # Point fields
        array = self.array()
        if self.dis.getRepr() == "P1":
            mesh_target.point_data[name] = array
        else:
            # Cell fields
            mesh_mc = self.field_target.getMesh()
            celltypes_mc = mesh_mc.getAllGeoTypesSorted()
            begin = None
            end = None
            cell_data = {}
            for celltype_mc in celltypes_mc:
                celltype = mc_to_meshio_type[celltype_mc]
                len_mesh_celltype = mesh_mc.getNumberOfCellsWithType(celltype_mc)
                if begin is None:
                    begin = 0
                    end = len_mesh_celltype
                else:
                    begin = end
                    end = begin + len_mesh_celltype
                cell_data[celltype] = array[begin:end]

            mesh_target.cell_data[name] = []
            for celltype in mesh_target.cells_dict.keys():
                for key in cell_data:
                    if celltype == key:
                        mesh_target.cell_data[name].append(cell_data[key])
                        break

        return mesh_target


class Mapper:
    """
    Class for mapping finite element data between meshes

    Args:
        verbose (bool): Whehter print out progress information
    """

    def __init__(self, verbose=True):
        self.verbose = verbose

        self.mesh_source = None
        self.mesh_source_mc = None
        self.mesh_target = None
        self.mesh_target_mc = None
        self.field_source = None
        self.field_target = None

        self._mapper = mc.MEDCouplingRemapper()

    def prepare(self, mesh_source, mesh_target, method="P1P0", intersection_type=None):
        """
        Prepare field mapping between meshes, must be run before
        :py:meth:`~.Mapper.transfer`. The source mesh must contain
        the field that you want to transfer to the target mesh.

        Args:
            mesh_source (meshio mesh): Source mesh
            mesh_target (meshio mesh): Target mesh
            method (str): Mapping methods: ``P1P0``, ``P1P1``, ``P0P0`` or ``P0P1``
            intersection_type (str): Intersection algorithm depending on meshes and the method
                                     Most used types: ``Triangulation``, ``PointLocator``
        """
        # Select intersection type
        assert method in ["P1P0", "P1P1", "P0P0", "P0P1"]
        if intersection_type is not None:
            self._mapper.setIntersectionType(eval("mc." + intersection_type))
        elif method[:2] == "P1":
            self._mapper.setIntersectionType(mc.PointLocator)
        self.method = method

        self._print("Loading source mesh...")
        cleanup_mesh_meshio(mesh_source)
        self.mesh_source = mesh_source
        self.mesh_source_mc = mesh_mc_from_meshio(mesh_source)

        self._print("Loading target mesh...")
        cleanup_mesh_meshio(mesh_target)
        self.mesh_target = mesh_target
        self.mesh_target_mc = mesh_mc_from_meshio(mesh_target)

        self._print("Preparing...")
        self._mapper.prepare(self.mesh_source_mc, self.mesh_target_mc, method)

    def transfer(self, field_name, nature="IntensiveMaximum", default_value=np.nan):
        """
        Transfer field from the source mesh to the target mesh, after
        :py:meth:`~.Mapper.prepare`.

        Args:
            field_name (str): Name of the field defined in the source mesh
            nature (str): Physical nature of the field (``IntensiveMaximum``, ``IntensiveConservation``, ``ExtensiveMaximum`` or ``ExtensiveConservation``)
            default_value (float): Default value when mapping is not possible
        """
        self._print("Transfering...")
        if self.method[:2] == "P1":
            on = "points"
        else:
            on = "cells"
        self.field_source = field_mc_from_meshio(
            self.mesh_source,
            field_name,
            on=on,
            mesh_mc=self.mesh_source_mc,
            nature=nature,
        )
        self.field_target = self._mapper.transferField(
            self.field_source, dftValue=default_value
        )
        self.field_target.setName(field_name)
        return MappingResult(self.field_target, self.mesh_target)

    def _print(self, blabla):
        if self.verbose:
            print(blabla)
