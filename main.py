import os

class Forensics:

    def __init__(self) -> None:
        self.disk_path = "DiskImages"
        self.file_formats = ["E01", "dmg"]
        self.disk_images = self.find_images()
        self.choosen_image = self.disk_images[0]

    def find_images(self):
        found_files = []

        for root, dirs, files in os.walk(self.disk_path):
            for file in files:
                if any(file.endswith('.' + ext) for ext in self.file_formats):
                    found_files.append(os.path.join(root, file))

        return found_files
    
    def main_loop(self):
        print(self.disk_images)
        print(self.choosen_image)

if __name__ == "__main__":
    forensic_instance = Forensics()
    forensic_instance.main_loop()
