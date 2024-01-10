import argparse
import os
import sys
import subprocess
from datetime import datetime
import pytz


def recover_files(evidence_file):
    """
    Recovers files from a disk image using the 'foremost' tool.

    :param evidence_file: Path to the disk image file from which to recover files.
    :type evidence_file: str
    :returns: None
    :raises subprocess.CalledProcessError: If an error occurs during the file recovery process.

    This function attempts to recover files from a specified disk image file using the 'foremost' tool.
    It creates an output directory named after the disk image and the current date and time, where
    it stores the recovered files. The process is run as a subprocess. If the subprocess fails,
    the function raises an error and exits.
    """
    timezone = pytz.timezone("Europe/Warsaw")
    current_datetime = datetime.now(timezone).strftime("%Y_%m_%d_%H_%M_%S")

    image_name = evidence_file.split("/")[1]

    output_directory = (
        "~/infa/Disk-Project/RecoveredDiskImages/"
        + image_name.split(".")[0]
        + "_"
        + current_datetime
    )

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    command = f"sudo foremost {evidence_file} -o {output_directory}"

    try:
        subprocess.run(command, shell=True, check=True)
        print(
            f"[+] Recovery process completed. Check {output_directory} for recovered files."
        )
    except subprocess.CalledProcessError as e:
        print(f"[-] Error during recovery process: {e}")
        sys.exit(1)


def main(evidence_file):
    """
    Main function to initiate the file recovery process from a disk image.

    :param evidence_file: Path to the disk image file from which to recover files.
    :type evidence_file: str
    :returns: None

    This function serves as the main entry point for the file recovery process. It calls
    the `recover_files` function with the provided disk image file path. It is used to start
    the process of recovering files from a given disk image.
    """
    recover_files(evidence_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Utility to recover files from disk image using foremost"
    )
    parser.add_argument("EVIDENCE_FILE", help="Evidence file path")
    args = parser.parse_args()
    if os.path.exists(args.EVIDENCE_FILE) and os.path.isfile(args.EVIDENCE_FILE):
        main(args.EVIDENCE_FILE)
    else:
        print(
            f"[-] Supplied input file {args.EVIDENCE_FILE} does not exist or is not a file"
        )
        sys.exit(1)
