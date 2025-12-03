import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from models import ParkFlowSystem
from utils import hanya_alnum


class GUI:
    def __init__(self, root):
        """Graphical User Interface for ParkFlowSystem.

        Menyediakan input plat/jenis, tombol aksi, dan tampilan slot/riwayat.
        Variable `antrian_window` menyimpan referensi ke jendela Toplevel
        untuk mencegah pembukaan banyak jendela antrian.
        """
        self.sys = ParkFlowSystem(10)
        self.root = root
        root.title("ParkFlow Motor")
        root.geometry("850x600")
        root.configure(bg="#2C3E50")
        # ref ke jendela antrian; None berarti belum dibuka
        self.antrian_window = None

        title = tk.Label(root, text="ParkFlow : Sistem Parkir Motor",
                         font=("Segoe UI", 16, "bold"), bg="#2C3E50", fg="white")
        title.pack(pady=10)

        frm = tk.Frame(root, bg="#2C3E50", relief="ridge", bd=2)
        frm.pack(pady=10, padx=10)

        vcmd = root.register(hanya_alnum)

        tk.Label(frm, text="Plat Nomor", bg="#2C3E50", fg="white", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=10, pady=5)
        self.in_plat = tk.Entry(frm, validate="key", validatecommand=(vcmd, "%S"), relief="sunken", bd=2)
        self.in_plat.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(frm, text="Jenis Motor", bg="#2C3E50", fg="white", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, padx=10, pady=5)
        self.jenis_var = tk.StringVar()
        self.jenis = ttk.Combobox(frm, textvariable=self.jenis_var,
                values=["Matic", "Bebek", "Sport"], state="readonly")
        self.jenis.grid(row=1, column=1, padx=10, pady=5)
        self.jenis.current(0)

        tk.Button(frm, text="Masuk", command=self.masuk, relief="raised", bd=2).grid(row=2, column=0, pady=10, padx=5)
        tk.Button(frm, text="Keluar", command=self.keluar, relief="raised", bd=2).grid(row=2, column=1, pady=10, padx=5)
        tk.Button(frm, text="Undo", command=self.undo, relief="raised", bd=2).grid(row=2, column=2, pady=10, padx=5)
        tk.Button(frm, text="Antrian", command=self.show_q, relief="raised", bd=2).grid(row=2, column=3, pady=10, padx=5)
        tk.Button(frm, text="Refresh", command=self.refresh, relief="raised", bd=2).grid(row=2, column=4, pady=10, padx=5)

        self.slot = ttk.Treeview(root, columns=("Slot","Plat","Jenis","Masuk","Durasi"),
                                 show="headings", height=7)
        for c in ("Slot","Plat","Jenis","Masuk","Durasi"):
            self.slot.heading(c, text=c)
        self.slot.pack(pady=10)

        tk.Label(root, text="Riwayat Parkir", font=("Segoe UI",12,"bold"),
                 bg="#2C3E50", fg="white").pack()

        self.riwayat = ttk.Treeview(root,
                columns=("Plat","Jenis","Masuk","Keluar","Durasi","Biaya"),
                show="headings", height=7)
        for c in ("Plat","Jenis","Masuk","Keluar","Durasi","Biaya"):
            self.riwayat.heading(c, text=c)
        self.riwayat.pack(pady=10)

        self.refresh()

    def show_q(self):
        # Jika sudah ada window antrian aktif, fokuskan dan jangan buat baru
        if self.antrian_window and getattr(self.antrian_window, "winfo_exists", lambda: False)() and self.antrian_window.winfo_exists():
            try:
                self.antrian_window.lift()
                self.antrian_window.focus_force()
            except Exception:
                pass
            return

        w = tk.Toplevel(self.root)
        self.antrian_window = w
        w.title("Antrian")
        w.geometry("250x300")
        w.configure(bg="#34495E")

        # Listbox menampilkan isi antrian saat jendela dibuat (satu kali)
        lb = tk.Listbox(w, width=30)
        lb.pack(pady=10)

        for a in self.sys.antrian:
            lb.insert(tk.END, a[0]+" ("+a[1]+")")

        # Ketika window ditutup, set referensi ke None agar bisa dibuka lagi
        def _on_close():
            try:
                self.antrian_window = None
            finally:
                w.destroy()

        w.protocol("WM_DELETE_WINDOW", _on_close)

    def masuk(self):
        # Ambil input dan lakukan validasi lebih ramah di sisi GUI
        plat_raw = self.in_plat.get().strip()
        jenis = self.jenis_var.get()

        # Validasi karakter: hanya alnum
        if not plat_raw:
            messagebox.showerror("Kesalahan", "Plat tidak boleh kosong.")
            return
        if not plat_raw.isalnum():
            messagebox.showerror("Kesalahan", "Plat hanya boleh berisi huruf dan angka.")
            return
        if len(plat_raw) < 2:
            messagebox.showerror("Kesalahan", "Plat minimal memiliki dua karakter.")
            return
        if not any(c.isalpha() for c in plat_raw) or not any(c.isdigit() for c in plat_raw):
            messagebox.showerror("Kesalahan", "Plat wajib mengandung minimal satu huruf dan satu angka.")
            return

        # Normalisasi untuk pengecekan duplikasi (model juga akan menormalisasi)
        plat_norm = plat_raw.upper()

        # Cek duplikasi di slot menggunakan Treeview `self.slot` (kolom Plat ada di index 1)
        for item in self.slot.get_children():
            vals = self.slot.item(item)["values"]
            # beberapa baris menampilkan "Kosong" pada kolom Plat
            try:
                plat_in_slot = str(vals[1]).upper()
            except Exception:
                plat_in_slot = ""
            if plat_in_slot == plat_norm:
                messagebox.showerror("Kesalahan", "Plat sudah terdaftar di slot parkir.")
                return

        # Cek duplikasi di antrian model (self.sys.antrian menyimpan (plat, jenis))
        for p, _ in self.sys.antrian:
            if p == plat_norm:
                messagebox.showerror("Kesalahan", "Plat sudah berada di dalam antrian.")
                return

        # Semua validasi GUI lulus; panggil logic sistem (model) — model juga memvalidasi
        res = self.sys.masuk(plat_norm, jenis)
        if res is True:
            self.in_plat.delete(0, tk.END)
        else:
            messagebox.showinfo("Informasi", res)

        self.refresh()

    def keluar(self):
        pilih = self.slot.selection()
        if not pilih:
            messagebox.showwarning("Perhatian", "Pilih kendaraan dulu")
            return

        index = int(pilih[0])
        biaya = self.sys.keluar(index)
        if biaya:
            messagebox.showinfo("Pembayaran", "Biaya: Rp"+str(biaya))

        self.refresh()

    def undo(self):
        if not self.sys.undo():
            messagebox.showinfo("Informasi", "Tidak ada yang bisa dibatalkan")
        self.refresh()

    def refresh(self):
        for i in self.slot.get_children():
            self.slot.delete(i)

        for i, s in enumerate(self.sys.slots):
            if s:
                dur = round((datetime.now() - s.waktu_masuk).total_seconds() / 60, 2)
                self.slot.insert("", "end", iid=str(i),
                        values=(i+1, s.plat, s.jenis,
                                s.waktu_masuk.strftime("%d/%m/%Y %H:%M"),
                                str(dur)+" menit"))
            else:
                self.slot.insert("", "end", iid=str(i),
                        values=(i+1,"Kosong","","",""))

        for i in self.riwayat.get_children():
            self.riwayat.delete(i)

        for r in self.sys.riwayat:
            self.riwayat.insert("", "end",
                    values=(r["plat"], r["jenis"],
                            r["masuk"].strftime("%d/%m/%Y %H:%M"),
                            r["keluar"].strftime("%d/%m/%Y %H:%M"),
                            str(r["durasi"])+" menit",
                            "Rp"+str(r["biaya"])))


def run_app():
    root = tk.Tk()
    GUI(root)
    root.mainloop()
