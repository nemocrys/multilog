"""Execute this to start multilog!"""

from argparse import ArgumentParser

from multilog.main import main
from multilog import __version__


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="multilog",
        description="Measurement data recording and visualization using various devices.",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="multilog configuration file [optional, default='./config.yml']",
        default="./config.yml",
    )
    parser.add_argument(
        "-o",
        "--out_dir",
        help="directory where to put the output [optional, default='.']",
        default=".",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{parser.prog} version {__version__}",
    )
    args = parser.parse_args()
    main(args.config, args.out_dir)
