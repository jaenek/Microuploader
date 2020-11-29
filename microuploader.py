import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import serial.tools.list_ports
import subprocess
import os
import shutil


class Uploader:
    def __init__(self):
        self.port = ""
        self.baud = "115200"
        self.action = "write_flash"
        self.address = ""
        self.filename = ""

    def set_com_port(self, port):
        self.port = port.split()[0][:-1]
    
    def set_address(self, address):
        self.address = address

    def set_filename(self, filename):
        self.filename = filename

    def list_ports():
        ports = serial.tools.list_ports.comports()

        results = []
        for port, desc, hwid in sorted(ports):
            results.append("{}: {}".format(port, desc))

        return results

    def list_addresses():
        return ["0x000000", "0x200000"]


    def create_process(self):
        command = [
            ".\deps\esptool.exe",
            "--chip", "esp8266",
            "--port", self.port,
            "--baud", self.baud,
            self.action, self.address, self.filename
        ]

        if self.port == "":
            return None
        
        if self.filename == "":
            return None

        if self.address not in Uploader.list_addresses():
            return None

        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


class Packer:
    def __init__(self):
        self.image_filename = ""
        self.dir = "./tmp/"
        self.block_size = "8192"
        self.page_size = "256"
        self.image_size = "1044464"

    def set_image_filename(self, filename):
        self.image_filename = filename
    
    def create_process(self, action):
        action_flag = ""
        if action == "pack":
            action_flag = "-c"
        elif action == "unpack":
            action_flag = "-u"
        else:
            return None

        command = [
            ".\deps\mklittlefs.exe",
            "--block", self.block_size,
            "--page", self.page_size,
            "--size", self.image_size,
            action_flag, self.dir,
            self.image_filename
        ]

        if self.image_filename == "":
            return None

        if self.dir == "":
            return None

        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Microuploader")
        self.master.geometry("720x510")
        self.master.resizable(False, False)
        self.pack()
        self.create_widgets()
        self.uploader = Uploader()
        self.packer = Packer()

    def create_widgets(self):
        content = tk.Frame(self)
        content.grid(column=0, row=0)

        output = tk.Frame(content)
        
        self.output_text = tk.Text(
            output,
            width=80, height=25
        )
        self.output_text.insert(tk.END, "Wyjście procesów\n")
        self.output_text.pack(side=tk.LEFT)

        scrollbar = ttk.Scrollbar(
            output,
            orient="vertical",
            command=self.output_text.xview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        output.pack(pady=10)

        packer_frame = tk.Frame(content, bd=1, relief="solid")

        ssid_label = tk.Label(packer_frame, text="SSID:")
        ssid_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.ssid = tk.Entry(packer_frame)
        self.ssid.pack(side=tk.LEFT, padx=5, pady=5)

        password_label = tk.Label(packer_frame, text="Hasło:")
        password_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.password = tk.Entry(packer_frame)
        self.password.pack(side=tk.LEFT, padx=5, pady=5)

        choose_image_filename = tk.Button(packer_frame)
        choose_image_filename["text"] = "Wybierz plik"
        choose_image_filename["command"] = self.ask_image_filename
        choose_image_filename.pack(side=tk.LEFT, padx=5,pady=5)

        modify_image = tk.Button(packer_frame)
        modify_image["text"] = "Modyfikuj obraz"
        modify_image["command"] = self.modify_image
        modify_image.pack(side=tk.LEFT, padx=5, pady=5)

        packer_frame.pack()

        upload_frame = tk.Frame(content, bd=1, relief="solid")

        self.port_list = ttk.Combobox(upload_frame, width=35, values=Uploader.list_ports())
        self.port_list.set("Wybierz port")
        self.port_list.pack(side=tk.LEFT, padx=5, pady=5)

        refresh_port_list = tk.Button(upload_frame)
        refresh_port_list["text"] = "Odśwież listę portów"
        refresh_port_list["command"] = self.fill_port_list
        refresh_port_list.pack(side=tk.LEFT, padx=5, pady=5)

        self.address_list = ttk.Combobox(upload_frame, width=13, values=Uploader.list_addresses())
        self.address_list.set("Wybierz adres")
        self.address_list.pack(side=tk.LEFT, padx=5, pady=5)

        choose_filename = tk.Button(upload_frame)
        choose_filename["text"] = "Wybierz plik"
        choose_filename["command"] = self.ask_filename
        choose_filename.pack(side=tk.LEFT, padx=5,pady=5)

        upload = tk.Button(upload_frame)
        upload["text"] = "Wgraj"
        upload["command"] = self.upload
        upload.pack(side=tk.LEFT, padx=5, pady=5)

        upload_frame.pack(pady=5)


    def fill_port_list(self):
        self.port_list["values"] = Uploader.list_ports()
    
    def ask_filename(self):
        path = filedialog.askopenfile(initialdir="./", title="Select a file to flash",
                    filetypes=(("binary files", "*.bin"), ("all files", "*.*")))
        if path is not None:
            self.uploader.set_filename(path.name)

    def ask_image_filename(self):
        path = filedialog.askopenfile(initialdir="./", title="Select a image file to modify",
                    filetypes=(("binary files", "*.bin"), ("all files", "*.*")))
        if path is not None:
            self.packer.set_image_filename(path.name)

    def modify_image(self):
        os.mkdir(self.packer.dir)
        try:
            packer_process = self.packer.create_process(action="unpack")
            if packer_process is not None:
                for line in packer_process.stdout:
                    self.output_text.insert(tk.END, line)
            else:
                self.output_text.insert(tk.END, "Wybierz plik\n")
                return

            self.output_text.insert(tk.END, "Zmienianie konfiguracji wifi...\n")
            with open(self.packer.dir + "wifisetup", "w") as f:
                f.write(self.ssid.get() + "\t" + self.password.get())

            packer_process = self.packer.create_process(action="pack")
            if packer_process is not None:
                for line in packer_process.stdout:
                    self.output_text.insert(tk.END, line)
            else:
                self.output_text.insert(tk.END, "Wybierz plik\n")
        finally:
            shutil.rmtree(self.packer.dir)
    

    def upload(self):
        self.uploader.set_com_port(self.port_list.get())
        self.uploader.set_address(self.address_list.get())

        self.output_text.insert(tk.END, "Wgrywanie...\n")
        uploader_process = self.uploader.create_process()
        if uploader_process is not None:
            for line in uploader_process.stdout:
                self.output_text.insert(tk.END, line)
        else:
            self.output_text.insert(tk.END, "Sprawdź wprowadzone dane\n")


root = tk.Tk()
app = Application(master=root)
app.mainloop()