import os
import sys
import timeit
import logging
import argparse

import sublib
import chardet


def parser() -> argparse.Namespace:
    """
    Parse CLI arguments.

    Parameters
    ----------
    None

    Returns
    ----------
    Arguments values.
    """
    arg_parser = argparse.ArgumentParser(
        usage=f"{os.path.basename(__file__)} "
              f"[--help] {{convert, detect}} ...",
        description="CLI implementation of Sublib package.",
        epilog="Supported formats: mpl, srt, sub, tmp"
    )
    subparsers = arg_parser.add_subparsers(
        dest="command"
    )
    base_parser = argparse.ArgumentParser(
        add_help=False
    )
    base_parser.add_argument(
        "-l", "--log",
        type=str,
        nargs="?",
        const=f"{os.path.splitext(__file__)[0]}.log",
        metavar="file",
        help="Enable logging"
    )
    convert_parser = subparsers.add_parser(
        "convert",
        usage=f"{os.path.basename(__file__)} "
              f"[--help] [--log [file]] convert path form",
        description="Convert subtitles to given format",
        help="Convert subtitles to given format",
        parents=[base_parser],
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog,
            max_help_position=52
        )
    )
    convert_parser.add_argument(
        "path",
        type=str,
        metavar="path",
        help="Directory or file to convert"
    )
    convert_parser.add_argument(
        "form",
        type=str,
        choices=["mpl", "srt", "sub", "tmp"],
        metavar="form",
        help="Desired format"
    )
    detect_parser = subparsers.add_parser(
        "detect",
        usage=f"{os.path.basename(__file__)} "
              f"[--help] [--log [file]] detect path",
        description="Detect subtitle format of file",
        help="Detect subtitle format of file",
        parents=[base_parser],
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog,
            max_help_position=52
        )
    )
    detect_parser.add_argument(
        "path",
        type=str,
        metavar="path",
        help="Directory or file to be analyzed"
    )
    arguments = arg_parser.parse_args()
    return arguments


def set_logger(file: str, level: int) -> logging.Logger:
    """
    Configure logging system.

    Parameters
    ----------
    file
        Path to a log file.
    level
        Representation of logging level.

    Returns
    ----------
    Logger object.
    """
    file = os.path.normpath(file)
    file = os.path.abspath(file)
    logging.basicConfig(
        filename=file,
        filemode="at",
        encoding="utf-8",
        format="%(asctime)s,%(levelname)s,"
               "%(module)s.%(funcName)s,%(message)s",
        level=level
    )
    logger = logging.getLogger(__name__)
    return logger


def find_files(path: str) -> list:
    """
    Search for files in a path.

    Parameters
    ----------
    path
        Path to dir or subtitle file.

    Returns
    ----------
    Found files.
    """
    if os.path.isfile(path):
        files = [path]
    if os.path.isdir(path):
        files = list(os.walk(path))
        files = [
            file.replace(file, path + "\\" + file)
            for file in files[0][2]
        ]
    return files


def detect_encoding(file: str) -> str:
    """
    Detect file encoding.

    Parameters
    ----------
    file
        Path to a file.

    Returns
    ----------
    Detected encoding.
    """
    with open(file, "rb") as f:
        file_content = f.read()
    result = chardet.detect(file_content)
    result = result["encoding"]
    return result


def get_subtitle(subtitle: dict) -> sublib.Subtitle:
    """
    Create Subtitle class instance.

    Parameters
    ----------
    subtitle
        Subtitle details.

    Returns
    ----------
    Specific subtitle object.
    """
    form = subtitle["format"]
    path = subtitle["path"]
    encd = subtitle["encoding"]
    if form == "mpl":
        subtitle = sublib.MPlayer2(path, encd)
    elif form == "srt":
        subtitle = sublib.SubRip(path, encd)
    elif form == "sub":
        subtitle = sublib.MicroDVD(path, encd)
    elif form == "tmp":
        subtitle = sublib.TMPlayer(path, encd)
    return subtitle


def get_new_path(file: dict, form: str) -> str:
    """
    Create path to desired subtitle file.

    Parameters
    ----------
    file
        Subtitle details.
    form
        Desired subtitle format.

    Returns
    ----------
    New subtitle file path.
    """
    path = file["path"]
    path = path[:path.rfind(".")]
    if form in ("mpl", "tmp"):
        path = f"{path}.txt"
    elif form in ("srt", "sub"):
        path = f"{path}.{form}"
    return path


def write_file(subtitle: sublib.Subtitle, file: dict,
               form: str, logger: logging.Logger):
    """
    Write converted subtitle to new file.

    Parameters
    ----------
    subtitle
        Specific subtitle class.
    file
        Subtitle details.
    form
        Desired subtitle format.
    logger
        Logger object.

    Returns
    ----------
    None
    """
    new = get_subtitle({
        "format": form,
        "path": "",
        "encoding": ""
    })
    lines = subtitle.get_general_format()
    new.set_from_general_format(lines)
    logger.info(f"Converted: {os.path.basename(subtitle.path)}")
    with open(file["path"], "wt", encoding=file["encoding"]) as f:
        f.writelines(f"{line}\n" for line in new.content)
    logger.info(f"Saved: {os.path.basename(file['path'])}")


def end(logger: logging.Logger, logfile: str, start: float):
    """
    End executing of script.

    Parameters
    ----------
    logger
        Logger object.
    logfile
        Path to log file.
    start
        Script start time.

    Returns
    ----------
    None
    """
    stop = timeit.default_timer()
    logger.info(f"Execution time: {stop-start}s")
    logger.info("END")
    logging.shutdown()
    if not os.path.getsize(logfile):
        os.remove(logfile)


def main(arguments: argparse.Namespace):

    command = arguments.command
    path = arguments.path
    logfile = arguments.log

    start = timeit.default_timer()

    path = os.path.normpath(path)
    path = os.path.abspath(path)

    if logfile:
        logger = set_logger(logfile, logging.INFO)
    else:
        logfile = f"{os.path.splitext(__file__)[0]}.log"
        logger = set_logger(logfile, logging.CRITICAL)

    logger.info("START")

    if os.path.exists(path):
        logger.info(f"Path: {path}")
    else:
        logger.critical(f"Path does not exists: {path}")
        end(logger, logfile, start)
        sys.exit(f"Path does not exists: {path}")

    if command == "convert":

        form = arguments.form

        input_files = []
        for file in find_files(path):
            input_files.append({
                "path": file,
                "encoding": detect_encoding(file),
                "format": sublib.detect(file, detect_encoding(file))
            })

        logger.info(
            f"Input files: "
            f"{[os.path.basename(file['path']) for file in input_files]}"
        )

        output_files = []
        for file in input_files:
            output_files.append({
                "path": get_new_path(file, form),
                "encoding": file["encoding"]
            })

        logger.info(
            f"Output files: "
            f"{[os.path.basename(file['path']) for file in output_files]}"
        )

        input_subtitles = [get_subtitle(file) for file in input_files]

        for subtitle, file in zip(input_subtitles, output_files):
            write_file(subtitle, file, form, logger)

    elif command == "detect":

        for file in find_files(path):

            encoding = detect_encoding(file)
            form = sublib.detect(file, encoding)

            forms = {
                "mpl": "MPlayer2",
                "srt": "SubRip",
                "sub": "MicroDVD",
                "tmp": "TMPlayer",
                "undefined": "Unknown"
            }

            message = f"{os.path.basename(file)} is in {forms[form]} format"
            logger.info(message)
            print(message)

    end(logger, logfile, start)


if __name__ == "__main__":

    try:
        main(parser())
    except Exception:
        print("An unknown error has occurred:")
        print(sys.exc_info())
