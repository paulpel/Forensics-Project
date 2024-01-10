import os
import sys
from open_evidence import main as open_evidence_main
from evidence_metadata import main as evidence_metadata_main
from recovery_files import main as recovery_files_main
from pdf_analysis import main as pdf_forensic_analysis_main


class Forensics:
    def __init__(self):
        self.disk_path = "DiskImages"
        self.dir_path = "RecoveredDiskImages"
        self.file_formats = ["E01", "dmg", "001", "raw", "dd"]
        self.dir_names = ["2023", "2024"]
        self.disk_images = self.find_images()
        self.directories = None
        self.choosen_image = None
        self.choosen_dir = None
        self.password = "123"
        self.encode_base64 = True
        self.menu_text = self.build_menu_text()
        self.options = {
            "1": lambda: self.choose_disk_image(),
            "2": self.extract_info,
            "3": self.extract_metadata,
            "4": self.recover_files,
            "5": self.pdf_forensic_analysis,
            "6": self.change_password,
            "7": self.toggle_base64_encoding,
            "8": self.quit_application,
        }

    def find_images(self):
        """
        Searches for image files within a specified directory path based on predefined file formats.

        :returns: A dictionary mapping filenames to their full paths for all found image files.
        :rtype: dict

        This method traverses the directory specified in `self.disk_path`, searching for files
        that match the image formats listed in `self.file_formats`. It returns a dictionary
        where each key is the filename of an image, and the corresponding value is the full path
        to that file. This method is useful for locating image files within a larger set of data,
        such as a disk image in a digital forensic investigation.
        """
        found_files = {}
        for root, _, files in os.walk(self.disk_path):
            for file in files:
                if any(file.endswith("." + ext) for ext in self.file_formats):
                    found_files[file] = os.path.join(root, file)
        return found_files

    def find_directories(self):
        """
        Searches for specific directories within a given directory path based on predefined directory names.

        :returns: A dictionary mapping directory names to their full paths for all found directories.
        :rtype: dict

        This method traverses the directory specified in `self.dir_path`, searching for subdirectories
        that match the names listed in `self.dir_names`. It returns a dictionary where each key is
        the name of a found directory, and the corresponding value is the full path to that directory.
        This method is particularly useful for locating specific types of directories (e.g., certain
        system or user directories) within a larger file system, often used in digital forensic
        investigations or file system analysis.
        """

        found_directories = {}
        for root, dirs, _ in os.walk(self.dir_path):
            for dir in dirs:
                if any(name in dir for name in self.dir_names):
                    found_directories[dir] = os.path.join(root, dir)
        return found_directories

    def build_menu_text(self):
        """
        Builds and returns the text for the main menu.

        :returns: The main menu text with options.
        :rtype: str

        This method generates a string representing the main menu of the application, listing
        different options for the user to choose from, such as selecting a disk image, extracting
        information, recovering files, and more. This is used to display the main menu to the user.
        """
        return (
            "\nPlease choose an option:\n"
            "1. Choose disk image\n"
            "2. Extract information about documents\n"
            "3. Extract metadata\n"
            "4. Recover files\n"
            "5. Forensic pdf analysis\n"
            "6. Change Password\n"
            "7. Toggle Base64 Encoding\n"
            "8. Exit program\n"
        )

    def choose_disk_image(self):
        """
        Displays available disk images and allows the user to choose one.

        :returns: None
        :raises ValueError: If the user's choice is not a valid number or out of the valid range.

        This method lists all available disk images stored in `self.disk_images` and prompts the
        user to choose one. The user's choice is then used to set the currently selected disk image.
        If the user selects an invalid option, an error message is displayed. The user can also choose
        to go back to the main menu.
        """
        print("\nAvailable disk images:")
        for index, (name, path) in enumerate(self.disk_images.items(), start=1):
            print(f"{index}. {name}")
        print(f"{len(self.disk_images) + 1}. Go back to main menu\n")

        choice = input("Select a disk image number or go back: ")
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(self.disk_images):
                self.choosen_image = list(self.disk_images.values())[choice - 1]
                print(
                    f"\nSelected disk image: {list(self.disk_images.keys())[choice - 1]}"
                )
            elif choice == len(self.disk_images) + 1:
                return
            else:
                print("Invalid selection. Please try again.")

    def change_password(self):
        """
        Allows the user to change the current password.

        :returns: None

        This method prompts the user to enter a new password. Upon entry, it updates `self.password`
        with the new password and notifies the user of the successful password change. This method is
        used for updating the encryption password used in various functions of the application.
        """
        new_password = input("Enter new password: ")
        self.password = new_password
        print("Password changed successfully.")

    def toggle_base64_encoding(self):
        """
        Toggles the state of Base64 encoding for the application.

        :returns: None

        This method switches the state of `self.encode_base64` between True and False, effectively
        toggling the Base64 encoding feature. It also prints out the current state of Base64 encoding
        after the toggle. This feature might be used in various functionalities of the application
        where encoding is required.
        """
        self.encode_base64 = not self.encode_base64
        print(f"Base64 Encoding {'enabled' if self.encode_base64 else 'disabled'}.")

    def print_menu(self):
        """
        Displays the main menu along with the current status of the chosen disk image.

        :returns: None

        This method prints the main menu text, which is stored in `self.menu_text`, to the console.
        It also displays the currently chosen disk image (if any) at the top of the menu. If no disk
        image is selected, it indicates so.
        """
        choosen_image_text = (
            f"Choosen disk image: {os.path.basename(self.choosen_image)}"
            if self.choosen_image
            else "No disk image selected."
        )
        print(f"{choosen_image_text}{self.menu_text}")

    def extract_info(self):
        """
        Extracts information about documents from the chosen disk image.

        :returns: None
        :raises Exception: If there is an error during the extraction process.

        This method initiates the process of extracting information about documents from the currently
        chosen disk image. It checks if a valid disk image is selected and if the selected image is
        of a supported format. If not, it prompts the user to select a valid image. On successful
        validation, it proceeds with the extraction process and handles any exceptions that occur.
        """
        print("[+] Extracting information about documents...")
        print(self.choosen_image)

        if not self.choosen_image or not self.choosen_image.endswith(
            (".E01", ".raw", ".dd")
        ):
            print(
                "[-] Invalid or no image selected. Choose a valid E01 or raw image first."
            )
            self.choose_disk_image(change=False)
            return

        try:
            open_evidence_main(
                self.choosen_image,
                "ewf" if self.choosen_image.endswith(".E01") else "raw",
                password=self.password,
                encode_base64=self.encode_base64,
            )
        except Exception as e:
            print(f"[-] Error extracting information:\n {e}")

    def extract_metadata(self):
        """
        Extracts metadata from the chosen disk image.

        :returns: None
        :raises Exception: If there is an error during the metadata extraction process.

        This method initiates the process of extracting metadata from the currently chosen disk image.
        It verifies that a valid disk image is selected and that the image is in a supported format.
        If the criteria are not met, the user is prompted to select a valid image. The method then
        proceeds with the extraction process, catching and reporting any exceptions encountered.
        """
        print("[+] Extracting metadata from the disk image...")

        if not self.choosen_image or not self.choosen_image.endswith(
            (".E01", ".raw", ".dd")
        ):
            print(
                "[-] Invalid or no image selected. Choose a valid E01 or raw image first."
            )
            self.choose_disk_image(change=False)
            return
        try:
            evidence_metadata_main(
                self.choosen_image,
                "ewf" if self.choosen_image.endswith(".E01") else "raw",
                part_type="DOS",
                encode_base64=self.encode_base64,
                password=self.password,
            )
        except Exception as e:
            print(f"[-] Error extracting metadata:\n {e}")

    def recover_files(self):
        """
        Initiates the file recovery process from the chosen disk image.

        :returns: None
        :raises Exception: If there is an error during the file recovery process.

        This method is responsible for recovering files from the currently selected disk image. It
        ensures that a valid disk image is chosen and that the image format is supported. If not,
        it requests the user to select an appropriate disk image. The method then proceeds with the
        recovery process, managing any exceptions that occur during execution.
        """
        print("[+] Recovering files from the disk image...")

        if not self.choosen_image or not self.choosen_image.endswith(
            (".E01", ".raw", ".dd")
        ):
            print(
                "[-] Invalid or no image selected. Choose a valid E01 or raw image first."
            )
            self.choose_disk_image(change=False)
            return
        try:
            recovery_files_main(
                self.choosen_image,
            )
        except Exception as e:
            print(f"[-] Error extracting metadata:\n {e}")

    def pdf_forensic_analysis(self):
        """
        Performs forensic analysis on PDF files in a chosen directory.

        :returns: None
        :raises Exception: If there is an error during the PDF forensic analysis process.

        This method allows the user to select a directory for PDF forensic analysis. It lists all
        available directories and prompts the user to choose one. The user is then asked to input
        search words for the analysis. Upon selection and input, the method initiates the forensic
        analysis on the PDF files in the chosen directory, handling any exceptions that arise.
        """
        print("[+] PDF analysis...")
        print("\nAvailable directories:")

        self.directories = self.find_directories()

        for index, (name, path) in enumerate(self.directories.items(), start=1):
            print(f"{index}. {name}")
        print(f"{len(self.directories) + 1}. Go back to main menu\n")

        choice = input("Select a directory number or go back: ")
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(self.directories):
                self.chosen_dir = list(self.directories.values())[choice - 1]
                print(
                    f"\nSelected directory: {list(self.directories.keys())[choice - 1]}"
                )

                # Ask for words to search
                search_words = input(
                    "Enter words to search (separated by space): "
                ).split()

                try:
                    pdf_forensic_analysis_main(
                        self.chosen_dir,
                        search_words,
                        self.password,
                    )
                except Exception as e:
                    print(f"[-] Error analysing PDFs:\n {e}")
            elif choice == len(self.directories) + 1:
                return
            else:
                print("Invalid selection. Please try again.")
        else:
            print("Please enter a valid number.")

    def quit_application(self):
        """
        Terminates the application.

        :returns: None

        This method cleanly exits the application when called. It prints a closing message to the
        console and then terminates the program execution.
        """
        print("Closing application...")
        sys.exit(0)

    def main_loop(self):
        """
        The main loop of the application, handling user input and menu navigation.

        :returns: None

        This is the central loop of the application, which continuously displays the menu and
        processes user input. Based on the user's choice, it executes the corresponding function
        from `self.options`. If an unknown option is selected, an error message is displayed. The
        loop continues until the application is exited.
        """
        while True:
            self.print_menu()
            choice = input("Enter the option number: ")
            action = self.options.get(choice)
            if action:
                action()
            else:
                print("Unknown option selected!")


if __name__ == "__main__":
    forensic_instance = Forensics()
    forensic_instance.main_loop()
