import ctypes
import json
import shutil
import subprocess

import psutil
import tqdm
import os
import configparser
import zipfile

import requests

from tkinter import Tk
from tkinter.filedialog import askdirectory


class PVM:
    def __init__(self, args):
        self.args = args
        self.command = args[0]
        self.args = args[1:]
        self.laragon_is_working = False

        self.config = configparser.ConfigParser()
        self.config.read("pvm.ini")
        self.laragon_path = self.config["laragon"]["path"]
        self.php_path = os.path.join(self.laragon_path, "bin", "php")

        pvm_ini = os.path.join(self.laragon_path, "bin", "pvm", "pvm.ini")

        if not os.path.exists(pvm_ini):
            ctypes.windll.user32.MessageBoxW(0, "Please select Laragon path", "PvmManager", 0x40)

            root = Tk()
            root.withdraw()
            laragon_path = askdirectory(title="PvmManager - Select Laragon path")
            root.destroy()

            if not laragon_path:
                print("Laragon path not selected")
                exit(1)

            laragon_path = laragon_path.replace("/", "\\")

            config = configparser.ConfigParser()
            config["laragon"] = {"path": laragon_path}
            with open(pvm_ini, "w") as file:
                config.write(file)

    def run(self):
        if self.command == "help":
            self.help()
        elif self.command == "install":
            self.install()
        elif self.command == "use":
            self.use()
        elif self.command == "list":
            self.list()
        else:
            print("Invalid command")

    def help(self):
        print("🙏 PvmManager help")
        print("Commands:")
        print("  help - Show this help message")
        print("  install <version> - Install a new version of PHP")
        print("  use <version> - Use a version of PHP")
        print("  list - List installed versions of PHP")

    def downloader(self, url, file_name):
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024
        with open(file_name, "wb") as file:
            for data in tqdm.tqdm(
                    response.iter_content(block_size),
                    total=total_size // block_size,
                    unit="KB",
                    unit_scale=True,
            ):
                file.write(data)

    def kill_laragon(self):
        # laragon pid bul
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.info["name"] == "laragon.exe":
                self.laragon_is_working = True
                # kill child processes
                for child in proc.children(recursive=True):
                    child.kill()
                # kill parent process
                proc.kill()
                break

    def start_laragon(self):
        if not self.laragon_is_working:
            return
        laragon_exe = os.path.join(self.laragon_path, "laragon.exe")
        subprocess.Popen([laragon_exe])

    def install(self):
        if len(self.args) == 0:
            print("🙅 Please specify a version to install")
            return

        version = self.args[0]
        print("▶️ PVM started for ", version)

        php_path = self.php_path

        json_url = "https://windows.php.net/downloads/releases/releases.json"
        parse = json.loads(requests.get(json_url).text)
        # yazılan versiyona en yakın versiyonu bul
        keys = list(parse.keys())
        keys.sort()
        for key in keys:
            if key.startswith(version):
                version = key
                break
        else:
            print("💢 Version not found")
            return

        print("🕗 Downloading PHP version", version)

        # ts-v ile başlayan keyi bul
        thread_safe = None
        for key in parse[version]:
            if key.startswith("ts-v") and key.endswith("x64"):
                thread_safe = key
                break
        else:
            print("💢 Thread safe version not found")
            return

        zip_file = parse[version][thread_safe]["zip"]["path"]
        zip_name = zip_file[:-4]
        print("Downloading", zip_file)

        url = f"https://windows.php.net/downloads/releases/{zip_file}"

        # zip dosyasını indir
        self.downloader(url, os.path.join(php_path, zip_file))

        print("🏁 PHP version", version, "downloaded.")
        print("🕗 Extracting PHP version", version)

        with zipfile.ZipFile(os.path.join(php_path, zip_file), "r") as zip_ref:
            zip_ref.extractall(os.path.join(php_path, zip_name))

        print("🏁 PHP version", version, "extracted")

        # zip dosyasını sil
        os.remove(os.path.join(php_path, zip_file))

        # php.ini-development dosyasını php.ini olarak kopyala
        php_ini_development = os.path.join(php_path, zip_name, "php.ini-development")
        php_ini = os.path.join(php_path, zip_name, "php.ini")
        shutil.copy(php_ini_development, php_ini)

        # https://curl.se/ca/cacert.pem adresinden cacert.pem dosyasını indir ve php klasörüne kopyala
        print("🕗 Downloading cacert.pem")
        pem = os.path.join(php_path, zip_name, "cacert.pem")
        url = "https://curl.se/ca/cacert.pem"
        self.downloader(url, pem)

        print("🏁 cacert.pem downloaded")

        print("📦 Opening curl fileinfo gd2 intl mbstring exif mysqli openssl pdo_mysql soap xsl zip extensions")
        with open(php_ini, "r") as file:
            php_ini_content = file.read()

        php_ini_content = (php_ini_content
                           .replace(";extension_dir = \"ext\"", "extension_dir = \"ext\"")
                           .replace(";extension=curl", "extension=curl")
                           .replace(";extension=fileinfo", "extension=fileinfo")
                           .replace(";extension=gd2", "extension=gd2")
                           .replace(";extension=intl", "extension=intl")
                           .replace(";extension=mbstring", "extension=mbstring")
                           .replace(";extension=exif", "extension=exif")
                           .replace(";extension=mysqli", "extension=mysqli")
                           .replace(";extension=openssl", "extension=openssl")
                           .replace(";extension=pdo_mysql", "extension=pdo_mysql")
                           .replace(";extension=soap", "extension=soap")
                           .replace(";extension=xsl", "extension=xsl")
                           .replace(";extension=zip", "extension=zip")
                           .replace(";curl.cainfo =", f"curl.cainfo = {pem}")
                           .replace(";openssl.cafile=", f"openssl.cafile={pem}"))

        with open(php_ini, "w") as file:
            file.write(php_ini_content)

        print("🏁 PHP version", version, "installed")

    def use(self):
        if len(self.args) == 0:
            print("🙅 Please specify a version to use")
            return

        use_version = self.args[0]

        # pathe ekle
        php_path = self.php_path

        # php klasörüne gir ve en uygun olan php klasörünü bul
        php_folders = os.listdir(php_path)
        php_folders.sort()
        for folder in php_folders:
            if folder.startswith("php-" + use_version):
                use_version = folder
                break
        else:
            print("🙅 Version not found")
            return

        use_version_path = os.path.join(php_path, use_version)

        # şuan bulunduğun dizine php adında bir kısayol oluştur ve php klasörüne yönlendir
        php_sym_path = os.path.join(self.laragon_path, "bin", "pvm", "php")
        if os.path.exists(php_sym_path):
            os.remove(php_sym_path)

        # yönetici olarak
        p = subprocess.Popen([
            "powershell",
            "Start-Process",
            "cmd",
            "-Verb",
            "runAs",
            "-ArgumentList",
            f"\"/c mklink /d {php_sym_path} {use_version_path}\""
        ])
        p.communicate()

        # run powershell command
        old_path = os.popen("powershell [Environment]::GetEnvironmentVariable('path', 'user');").read().strip()
        path_vars = old_path.split(";")

        # php_sym_path var mı kontrol et eğer yoksa ekle
        if php_sym_path not in path_vars:
            path_vars.append(php_sym_path)

            # yeni pathi ayırıcı ile birleştir
            new_path = ";".join(path_vars)
            command = "[Environment]::SetEnvironmentVariable('path','%new_path%','user')"
            command = command.replace("%new_path%", new_path)

            # yönetici bir cmd aç ve powershell çalıştır
            p = subprocess.Popen([
                "powershell",
                "Start-Process",
                "powershell",
                "-Verb",
                "runAs",
                "-ArgumentList",
                f"\"{command}\""
            ])

            p.communicate()

        # laragonu kapat
        self.kill_laragon()

        laragon_ini = os.path.join(self.laragon_path, "usr", "laragon.ini")
        cp = configparser.ConfigParser()
        cp.read(laragon_ini)
        cp["php"]["Version"] = use_version
        with open(laragon_ini, "w") as file:
            cp.write(file)

        # laragonu başlat
        self.start_laragon()

    def list(self):
        php_folders = os.listdir(self.php_path)
        php_folders.sort()

        versions = []
        for folder in php_folders:
            if folder.startswith("php-"):
                versions.append(folder.split("-")[1])

        current_version = None
        laragon_ini = os.path.join(self.laragon_path, "usr", "laragon.ini")
        cp = configparser.ConfigParser()
        cp.read(laragon_ini)
        current_version = cp["php"]["version"].split("-")[1].strip()

        versions.sort()
        print("📋 Installed versions:")
        for version in versions:
            if version == current_version:
                print("⚪ ", version)
            else:
                print("⚫ ", version)
