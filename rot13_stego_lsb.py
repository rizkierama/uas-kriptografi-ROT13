import customtkinter as ctk          # GUI library (Custom Tkinter)
from tkinter import filedialog, messagebox   # Dialog & pop-up
from PIL import Image                # Load dan manipulasi gambar
import os                            # Cek file dan path

STOP = "||STOP||"                    # Penanda akhir pesan
SIGN = "STEGO#"                     # Penanda bahwa gambar adalah stego

# ================= ROT13 =================
def rot13(s):
    out=[]
    for c in s:
        # Shift huruf kecil 13 posisi
        if 'a'<=c<='z': out.append(chr((ord(c)-97+13)%26+97))
        # Shift huruf besar 13 posisi
        elif 'A'<=c<='Z': out.append(chr((ord(c)-65+13)%26+65))
        # Karakter non-huruf tidak berubah
        else: out.append(c)
    return ''.join(out)

# ================ EMBED LSB ================
def embed_lsb(path, msg):
    img = Image.open(path).convert("RGB")  # Paksa ke RGB
    w,h = img.size                         # Ambil ukuran
    if w<128 or h<128:                     # Validasi sesuai ketentuan
        raise ValueError("Minimal 128x128 px!")

    data = SIGN + msg + STOP               # Gabung signature + pesan + stop
    bits = ''.join(f"{ord(c):08b}" for c in data)   # Konversi ke bit 8-bit/karakter

    # Validasi kapasitas penyisipan
    if len(bits) > w*h*3:
        raise ValueError("Pesan terlalu panjang!")

    px = img.load()
    i=0
    # Sisipkan bit ke LSB pixel
    for y in range(h):
        for x in range(w):
            if i>=len(bits): break
            r,g,b = px[x,y]
            if i<len(bits): r=(r&254)|int(bits[i]); i+=1
            if i<len(bits): g=(g&254)|int(bits[i]); i+=1
            if i<len(bits): b=(b&254)|int(bits[i]); i+=1
            px[x,y]=(r,g,b)
        if i>=len(bits): break

    # Buat output file stego otomatis (hindari overwrite)
    base = os.path.splitext(path)[0]
    out = f"{base}_stego.bmp"
    k=1
    while os.path.exists(out):
        out = f"{base}_stego_{k}.bmp"; k+=1

    img.save(out,"BMP")              # Simpan hasil sebagai BMP
    return out

# ================ EXTRACT LSB ================
def extract_lsb(path):
    img = Image.open(path).convert("RGB")
    px = img.load()
    bits=""; text=""

    for y in range(img.height):
        for x in range(img.width):
            r,g,b = px[x,y]
            # Ambil LSB tiap channel
            bits += f"{r&1}{g&1}{b&1}"

            # Konversi 8 bit menjadi karakter
            while len(bits)>=8:
                ch = chr(int(bits[:8],2))
                text += ch
                bits = bits[8:]
                # Deteksi end of message
                if text.endswith(STOP):
                    text = text[:-len(STOP)]
                    # Verifikasi signature
                    if text.startswith(SIGN):
                        return text[len(SIGN):]
                    return None
    return None

# ================= GUI =================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ROT13 + LSB Steganography")
        self.geometry("500x540")
        self.file=None                  # Menyimpan path gambar

        ctk.CTkLabel(self,text="Pesan:").pack(pady=4)
        self.txt_in = ctk.CTkTextbox(self,height=70)
        self.txt_in.pack(padx=20,fill="x")

        # Tombol browse & reset file
        box = ctk.CTkFrame(self,fg_color="transparent"); box.pack(pady=6)
        ctk.CTkButton(box,text="Pilih Gambar",command=self.browse).pack(side="left",padx=5)
        ctk.CTkButton(box,text="X",width=35,fg_color="red",hover_color="darkred",
                      command=self.reset).pack(side="left",padx=5)

        self.lbl = ctk.CTkLabel(self,text="File: -")
        self.lbl.pack()

        ctk.CTkButton(self,text="CEK STEGO",command=self.do_check).pack(pady=4)
        ctk.CTkButton(self,text="ENKRIPSI (Embed)",command=self.do_embed).pack(pady=4)
        ctk.CTkButton(self,text="DEKRIPSI (Extract)",command=self.do_extract).pack(pady=4)

        ctk.CTkLabel(self,text="Hasil:").pack(pady=4)
        self.txt_out = ctk.CTkTextbox(self,height=120)
        self.txt_out.pack(padx=20,fill="x")

    # Pilih gambar BMP/JPG
    def browse(self):
        p = filedialog.askopenfilename(filetypes=[("BMP/JPG","*.bmp;*.jpg")])
        if not p: return
        self.file=p
        self.lbl.configure(text=os.path.basename(p))

    # Reset file
    def reset(self):
        self.file=None
        self.lbl.configure(text="File: -")
        self.txt_out.delete("1.0","end")

    # Cek apakah gambar mengandung stego
    def do_check(self):
        if not self.file:
            return messagebox.showerror("Error","Belum pilih gambar")
        cipher = extract_lsb(self.file)
        self.txt_out.delete("1.0","end")
        if cipher is None:
            self.txt_out.insert("end","Status: Tidak ada pesan tersembunyi")
        else:
            self.txt_out.insert("end", f"Status: Ada ciphertext\nCiphertext: {cipher}")

    # Embed + ROT13
    def do_embed(self):
        if not self.file:
            return messagebox.showerror("Error","Belum pilih gambar")
        msg = self.txt_in.get("1.0","end").strip()
        if not msg:
            return messagebox.showerror("Error","Pesan kosong")
        try:
            stego = embed_lsb(self.file, rot13(msg))
            messagebox.showinfo("Sukses",f"Stego disimpan: {os.path.basename(stego)}")
            self.txt_in.delete("1.0","end")
            self.reset()
        except Exception as e:
            messagebox.showerror("Gagal",str(e))

    # Extract + ROT13
    def do_extract(self):
        if not self.file:
            return messagebox.showerror("Error","Belum pilih stego")
        cipher = extract_lsb(self.file)
        self.txt_out.delete("1.0","end")
        if cipher is None:
            self.txt_out.insert("end","Tidak ada pesan tersembunyi")
        else:
            plain = rot13(cipher)
            self.txt_out.insert("end", f"Ciphertext: {cipher}\nPlaintext: {plain}")

# MAIN
if __name__=="__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("green")
    App().mainloop()
