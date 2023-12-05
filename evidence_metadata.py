from __future__ import print_function
import argparse
import os
import pytsk3
import pyewf
from tabulate import tabulate
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime


__description__ = (
    "Script to process and extract data from forensic evidence containers."
)


class EWFImgInfo(pytsk3.Img_Info):
    """
    Class to handle EWF (Expert Witness Format) image files using pytsk3 library.

    :param ewf_handle: A handle to an EWF file opened using pyewf.
    :type ewf_handle: pyewf.handle
    """

    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super(EWFImgInfo, self).__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        """
        Closes the EWF handle.
        """
        self._ewf_handle.close()

    def read(self, offset, size):
        """
        Reads data from the EWF image file.

        :param offset: The offset from which to start reading.
        :param size: The amount of data to read.
        :return: The data read from the EWF image.
        """
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        """
        Gets the total size of the EWF image.

        :return: The size of the EWF image.
        """
        return self._ewf_handle.get_media_size()


def main(image, img_type, part_type, password):
    """
    Main function to process the evidence file.

    :param image: Path to the evidence file.
    :param img_type: Type of the evidence file (raw or ewf).
    :param part_type: Type of partition (optional).
    """
    print("[+] Opening {}".format(image))
    if img_type == "ewf":
        try:
            filenames = pyewf.glob(image)
        except IOError as e:
            print("[-] Invalid EWF format:\n {}".format(e))
            return

        ewf_handle = pyewf.handle()
        ewf_handle.open(filenames)
        e01_metadata(ewf_handle)

        img_info = EWFImgInfo(ewf_handle)
    else:
        img_info = pytsk3.Img_Info(image)

    volume = None
    fs = None

    try:
        if part_type:
            attr_id = getattr(pytsk3, "TSK_VS_TYPE_" + part_type)
            volume = pytsk3.Volume_Info(img_info, attr_id)
        else:
            fs = pytsk3.FS_Info(img_info)
    except IOError as e:
        print("[-] Unable to read partition table or file system:\n {}".format(e))
        return

    if volume:
        part_metadata(volume)
    elif fs:
        # Handle file system analysis if needed
        pass
    else:
        print("No partition or file system detected.")

    if volume:
        data = part_metadata(volume)
    elif fs:
        # Handle file system analysis if needed
        pass
    else:
        print("No partition or file system detected.")

    date_str = datetime.now().strftime("%Y%m%d")
    pdf_filename = f"meta_{os.path.splitext(os.path.basename(image))[0]}_{date_str}.pdf"
    create_encrypted_pdf(data, pdf_filename, password)


def create_encrypted_pdf(data, filename, password):
    pdf = SimpleDocTemplate(filename, pagesize=letter)
    elements = []

    t = Table(data)
    # Set table style here
    elements.append(t)
    pdf.build(elements)

    encrypt_pdf(filename, password)


def encrypt_pdf(input_pdf, password):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(password)

    with open(input_pdf, "wb") as output_file:
        writer.write(output_file)


def part_metadata(vol):
    """
    Extracts and prints metadata of partitions.

    :param vol: Volume information from the forensic image.
    """
    if vol is None:
        print("No volume information available.")
        return

    table = [["Index", "Type", "Offset Start (Sectors)", "Length (Sectors)"]]
    for part in vol:
        table.append([part.addr, part.desc.decode("utf-8"), part.start, part.len])
    print("\n Partition Metadata")
    print("-" * 20)
    print(tabulate(table, headers="firstrow"))
    return table


def e01_metadata(e01_image):
    """
    Extracts and prints metadata of EWF (E01) images.

    :param e01_image: EWF image object.
    """
    print("\nEWF Acquisition Metadata")
    print("-" * 20)
    headers = e01_image.get_header_values()
    hashes = e01_image.get_hash_values()
    for k in headers:
        print("{}: {}".format(k, headers[k]))
    for h in hashes:
        print("Acquisition {}: {}".format(h, hashes[h]))
    print("Bytes per Sector: {}".format(e01_image.bytes_per_sector))
    print("Number of Sectors: {}".format(e01_image.get_number_of_sectors()))
    print("Total Size: {}".format(e01_image.get_media_size()))
    return e01_image


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument("EVIDENCE_FILE", help="Evidence file path")
    parser.add_argument("TYPE", help="Type of Evidence", choices=("raw", "ewf"))
    parser.add_argument(
        "-p", help="Partition Type", choices=("DOS", "GPT", "MAC", "SUN")
    )
    parser.add_argument("-f", "--filename", help="Output PDF filename", required=True)
    parser.add_argument(
        "-pwd", "--password", help="Password for the PDF", required=True
    )
    args = parser.parse_args()

    if os.path.exists(args.EVIDENCE_FILE) and os.path.isfile(args.EVIDENCE_FILE):
        main(args.EVIDENCE_FILE, args.TYPE, args.p)
    else:
        print(
            "[-] Supplied input file {} does not exist or is not a file".format(
                args.EVIDENCE_FILE
            )
        )
