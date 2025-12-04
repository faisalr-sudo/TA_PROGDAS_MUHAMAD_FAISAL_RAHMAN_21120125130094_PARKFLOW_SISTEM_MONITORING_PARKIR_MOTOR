import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from models import ParkFlowSystem
from utils import hanya_alnum


def format_durasi(detik):
    """Format durasi dalam detik menjadi string 'HH:MM:SS.SSS'."""
    jam = int(detik // 3600)
    menit = int((detik % 3600) // 60)
    detik_sisa = int(detik % 60)
    milidetik = int((detik % 1) * 1000)
    return f"{jam:02d}:{menit:02d}:{detik_sisa:02d}.{milidetik:03d}"


# Kelas GUI untuk antarmuka grafis sistem ParkFlow
class GUI:
    def __init__(self, root):
        """Graphical User Interface for ParkFlowSystem.

        Menyediakan input plat/jenis, tombol aksi, dan tampilan slot/riwayat.
        Variable `antrian_window` menyimpan referensi ke jendela Toplevel
        untuk mencegah pembukaan banyak jendela antrian.
        """
        # Buat instance sistem parkir dengan kapasitas 10 slot
        self.sys = ParkFlowSystem(10)
        # Simpan referensi ke root window
        self.root = root
        # Set judul window
        root.title("ParkFlow Motor")
        # Set ukuran window
        root.geometry("850x600")
        # Set warna background
        root.configure(bg="#2C3E50")
        # Referensi ke jendela antrian; None berarti belum dibuka
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
        # Start auto-refresh for slot durations
        self.auto_refresh()

    def auto_refresh(self):
        """Update durasi slot setiap milidetik secara otomatis.

        Loop melalui semua item di Treeview slot, jika slot terisi,
        hitung ulang durasi parkir dan update tampilan.
        Jadwalkan pemanggilan ulang method ini setiap 1 milidetik.
        """
        for i in self.slot.get_children():
            item = self.slot.item(i)
            vals = item["values"]
            if vals[1] != "Kosong":  # Jika slot tidak kosong
                # Hitung ulang durasi
                slot_index = int(i)
                s = self.sys.slots[slot_index]
                if s:
                    dur_detik = (datetime.now() - s.waktu_masuk).total_seconds()
                    new_vals = list(vals)
                    new_vals[4] = format_durasi(dur_detik)
                    self.slot.item(i, values=new_vals)
        # Jadwalkan update berikutnya dalam 1 milidetik
        self.root.after(1, self.auto_refresh)

    def show_q(self):
        """Menampilkan jendela antrian parkir.

        Jika jendela antrian sudah terbuka, fokuskan ke jendela tersebut.
        Jika belum, buat jendela baru dengan listbox yang menampilkan antrian.
        """
        # Jika sudah ada window antrian aktif, fokuskan dan jangan buat baru
        if self.antrian_window and getattr(self.antrian_window, "winfo_exists", lambda: False)() and self.antrian_window.winfo_exists():
            try:
                self.antrian_window.lift()
                self.antrian_window.focus_force()
            except Exception:
                pass
            return

        # Buat jendela baru untuk antrian
        w = tk.Toplevel(self.root)
        self.antrian_window = w
        w.title("Antrian")
        w.geometry("250x300")
        w.configure(bg="#34495E")

        # Listbox untuk menampilkan isi antrian saat jendela dibuat (satu kali)
        lb = tk.Listbox(w, width=30)
        lb.pack(pady=10)

        # Isi listbox dengan data antrian
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
        """Proses kendaraan masuk melalui GUI.

        Ambil input dari field plat dan jenis, lakukan validasi di sisi GUI,
        cek duplikasi, lalu panggil method masuk di sistem backend.
        """
        # Ambil input dari entry field dan strip spasi
        plat_raw = self.in_plat.get().strip()
        jenis = self.jenis_var.get()

        # Validasi input: plat tidak boleh kosong
        if not plat_raw:
            messagebox.showerror("Kesalahan", "Plat tidak boleh kosong.")
            return
        # Validasi: hanya alfanumerik
        if not plat_raw.isalnum():
            messagebox.showerror("Kesalahan", "Plat hanya boleh berisi huruf dan angka.")
            return
        # Validasi: minimal 2 karakter
        if len(plat_raw) < 2:
            messagebox.showerror("Kesalahan", "Plat minimal memiliki dua karakter.")
            return
        # Validasi: harus ada huruf dan angka
        if not any(c.isalpha() for c in plat_raw) or not any(c.isdigit() for c in plat_raw):
            messagebox.showerror("Kesalahan", "Plat wajib mengandung minimal satu huruf dan satu angka.")
            return

        # Normalisasi plat ke uppercase untuk pengecekan duplikasi
        plat_norm = plat_raw.upper()

        # Cek duplikasi di slot parkir yang ditampilkan di Treeview
        for item in self.slot.get_children():
            vals = self.slot.item(item)["values"]
            try:
                plat_in_slot = str(vals[1]).upper()
            except Exception:
                plat_in_slot = ""
            if plat_in_slot == plat_norm:
                messagebox.showerror("Kesalahan", "Plat sudah terdaftar di slot parkir.")
                return

        # Cek duplikasi di antrian sistem
        for p, _ in self.sys.antrian:
            if p == plat_norm:
                messagebox.showerror("Kesalahan", "Plat sudah berada di dalam antrian.")
                return

        # Semua validasi lulus, panggil method masuk di backend
        res = self.sys.masuk(plat_norm, jenis)
        if res is True:
            # Jika berhasil, clear input field
            self.in_plat.delete(0, tk.END)
        else:
            # Jika ada pesan error, tampilkan info
            messagebox.showinfo("Informasi", res)

        # Refresh tampilan
        self.refresh()

    def keluar(self):
        """Proses kendaraan keluar melalui GUI.

        Ambil slot yang dipilih dari Treeview, panggil method keluar di backend,
        tampilkan biaya jika berhasil, lalu refresh tampilan.
        """
        # Ambil item yang dipilih di Treeview slot
        pilih = self.slot.selection()
        if not pilih:
            messagebox.showwarning("Perhatian", "Pilih kendaraan dulu")
            return

        # Konversi ID item ke index slot (item ID adalah string index)
        index = int(pilih[0])
        # Panggil method keluar di backend
        biaya = self.sys.keluar(index)
        if biaya:
            # Jika ada biaya, tampilkan pesan pembayaran
            messagebox.showinfo("Pembayaran", "Biaya: Rp"+str(biaya))

        # Refresh tampilan setelah aksi
        self.refresh()

    def undo(self):
        if not self.sys.undo():
            messagebox.showinfo("Informasi", "Tidak ada yang bisa dibatalkan")
        self.refresh()

    def refresh(self):
        """Refresh tampilan slot dan riwayat.

        Kosongkan Treeview slot dan riwayat, lalu isi ulang dengan data terbaru
        dari sistem backend.
        """
        # Kosongkan Treeview slot
        for i in self.slot.get_children():
            self.slot.delete(i)

        # Isi ulang Treeview slot dengan data dari self.sys.slots
        for i, s in enumerate(self.sys.slots):
            if s:
                # Jika slot terisi, hitung durasi dan tampilkan data kendaraan
                dur_detik = (datetime.now() - s.waktu_masuk).total_seconds()
                self.slot.insert("", "end", iid=str(i),
                        values=(i+1, s.plat, s.jenis,
                                s.waktu_masuk.strftime("%d/%m/%Y %H:%M"),
                                format_durasi(dur_detik)))
            else:
                # Jika slot kosong, tampilkan "Kosong"
                self.slot.insert("", "end", iid=str(i),
                        values=(i+1,"Kosong","","",""))

        # Kosongkan Treeview riwayat
        for i in self.riwayat.get_children():
            self.riwayat.delete(i)

        # Isi ulang Treeview riwayat dengan data dari self.sys.riwayat
        for r in self.sys.riwayat:
            self.riwayat.insert("", "end",
                    values=(r["plat"], r["jenis"],
                            r["masuk"].strftime("%d/%m/%Y %H:%M"),
                            r["keluar"].strftime("%d/%m/%Y %H:%M"),
                            format_durasi(r["durasi"]),
                            "Rp"+str(r["biaya"])))


def run_app():
    """Fungsi utama untuk menjalankan aplikasi ParkFlow.

    Buat root window Tkinter, inisialisasi GUI, dan mulai event loop.
    """
    root = tk.Tk()
    GUI(root)
    root.mainloop()
