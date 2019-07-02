# -*- coding: utf-8 -*-
#
import sys

import numpy as np

from .__about__ import __copyright__, __version__
from .main import Remapper


def main(argv=None):
    # Parse command line arguments.
    parser = _get_parser()
    args = parser.parse_args(argv)

    import meshio
    remap = Remapper(verbose=args.verbose)

    mesh_source = meshio.read(args.mesh_source)
    mesh_target = meshio.read(args.mesh_target)
    remap.prepare(mesh_source, mesh_target, args.method, args.intersection_type)
    res = remap.transfer(args.field_name, args.nature)

    if ".txt" in args.outfile:
        np.savetxt(args.outfile, res.array())
    elif ".npy" in args.outfile:
        np.save(args.outfile, res.array())
    elif ".vtu" in args.outfile:
        res.export_vtk(args.outfile)
    else:
        mesh_target = res.mesh_meshio()
        meshio.write(args.outfile, mesh_target)

    return


def _get_parser():
    import argparse

    parser = argparse.ArgumentParser(
        description=("Mapping finite element data between meshes"),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("mesh_source", type=str, help="meshio-compatible source mesh file")

    parser.add_argument("mesh_target", type=str, help="meshio-compatible target mesh file")

    parser.add_argument("field_name", type=str, help="field defined in the source mesh to transfer to the target mesh")

    parser.add_argument("outfile", type=str, help="file to store mapped data: .txt, .npy or meshio-compatible mesh")

    parser.add_argument("--method", type=str, choices=["P1P1", "P1P0", "P0P1", "P0P0"], default="P1P1", help="mapping method")

    parser.add_argument("--intersection_type", type=str, help="intersection algorithm")

    parser.add_argument("--nature", type=str, default="IntensiveMaximum", help="physical nature of the field")

    parser.add_argument("--verbose", action="store_true", default=False, help="increase output verbosity")

    version_text = "\n".join(
        [
            "pymapping {} [Python {}.{}.{}]".format(
                __version__,
                sys.version_info.major,
                sys.version_info.minor,
                sys.version_info.micro,
            ),
            __copyright__,
        ]
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=version_text,
        help="display version information",
    )

    return parser
