import os
import sys
from open_evidence import main as open_evidence_main
from evidence_metadata import main as evidence_metadata_main


class Forensics:
    def __init__(self):
        self.disk_path = "DiskImages"
        self.file_formats = ["E01", "dmg", "001", "raw", "dd"]
        self.disk_images = self.find_images()
        self.choosen_image = None
        self.password = "default_password"
        self.encode_base64 = True
        self.menu_text = self.build_menu_text()
        self.options = {
            "1": lambda: self.choose_disk_image(),
            "2": self.extract_info,
            "3": self.extract_metadata,
            "4": self.change_password,
            "5": self.toggle_base64_encoding,
            "6": self.quit_application,
        }

    def find_images(self):
        found_files = {}
        for root, _, files in os.walk(self.disk_path):
            for file in files:
                if any(file.endswith("." + ext) for ext in self.file_formats):
                    found_files[file] = os.path.join(root, file)
        return found_files

    def build_menu_text(self):
        return (
            "\nPlease choose an option:\n"
            "1. Choose disk image\n"
            "2. Extract information about documents\n"
            "3. Extract metadata\n"
            "4. Change Password\n"
            "5. Toggle Base64 Encoding\n"
            "6. Exit program\n"
        )

    def choose_disk_image(self):
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
        new_password = input("Enter new password: ")
        self.password = new_password
        print("Password changed successfully.")

    def toggle_base64_encoding(self):
        self.encode_base64 = not self.encode_base64
        print(f"Base64 Encoding {'enabled' if self.encode_base64 else 'disabled'}.")

    def print_menu(self):
        choosen_image_text = (
            f"Choosen disk image: {os.path.basename(self.choosen_image)}"
            if self.choosen_image
            else "No disk image selected."
        )
        print(f"{choosen_image_text}{self.menu_text}")

    def extract_info(self):
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
        print("[+] Extracting metadata from the disk image...")

        if not self.choosen_image or not self.choosen_image.endswith(
            (".E01", ".raw", ".dd")
        ):
            print(
                "[-] Invalid or no image selected. Choose a valid E01 or raw image first."
            )
            self.choose_disk_image(change=False)
            return

        partition_types = ["DOS", "GPT", "MAC", "SUN", "Cancel"]
        for index, p_type in enumerate(partition_types, start=1):
            print(f"{index}. {p_type}")

        choice = input("Enter your choice: ")
        if not choice.isdigit() or not 1 <= int(choice) <= len(partition_types):
            print("Invalid selection. Please try again.")
            return

        if choice == str(len(partition_types)):  # Cancel option
            print("Metadata extraction cancelled.")
            return

        selected_partition_type = partition_types[int(choice) - 1]
        print(f"Selected partition type: {selected_partition_type}")

        try:
            evidence_metadata_main(
                self.choosen_image,
                "ewf" if self.choosen_image.endswith(".E01") else "raw",
                part_type=selected_partition_type,
                password=self.password,
            )
        except Exception as e:
            print(f"[-] Error extracting metadata:\n {e}")

    def quit_application(self):
        print("Closing application...")
        sys.exit(0)

    def main_loop(self):
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
