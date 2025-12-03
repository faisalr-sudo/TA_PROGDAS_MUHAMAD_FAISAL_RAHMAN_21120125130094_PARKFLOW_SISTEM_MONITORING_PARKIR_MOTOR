from datetime import datetime


class Kendaraan:
    """Represents a vehicle parked in the system.

    Attributes:
        plat (str): vehicle plate number (uppercase, no spaces)
        jenis (str): vehicle type (e.g., Matic, Bebek, Sport)
        waktu_masuk (datetime): timestamp when vehicle was parked
    """
    def __init__(self, plat, jenis):
        self.plat = plat
        self.jenis = jenis
        # record waktu masuk saat objek dibuat
        self.waktu_masuk = datetime.now()


class ParkFlowSystem:
    """Core parking system logic (non-GUI).

    Menangani:
    - slot parkir tetap (list `slots`),
    - antrian ketika slot penuh (`antrian` list of tuples),
    - riwayat keluar masuk (`riwayat` list of dict),
    - undo stack untuk membatalkan aksi terakhir.
    """
    def __init__(self, kapasitas):
        self.kapasitas = kapasitas
        # daftar slot, setiap elemen None atau objek `Kendaraan`
        self.slots = [None] * kapasitas  # MODUL 3: List
        # simpan riwayat keluar (untuk tampilan dan bukti)
        self.riwayat = []                # List of dict
        # antrian ketika parkir penuh; item = (plat, jenis)
        self.antrian = []                # Queue
        # stack untuk undo; menyimpan tuple aksi untuk rollback
        self.undo_stack = []             # Stack untuk UNDO

    def validasi_plat(self, plat):
        """Validasi dan normalisasi plat.

        - Ubah ke uppercase dan trim spasi.
        - Pastikan ada huruf dan angka, dan dimulai huruf.
        - Kembalikan False jika format salah, atau string plat yang sudah dinormalisasi.
        """
        plat = plat.upper().strip()

        if len(plat) < 2:
            return False
        if not plat[0].isalpha():
            return False

        # minimal harus memiliki huruf dan angka
        angka = any(c.isdigit() for c in plat)
        huruf = any(c.isalpha() for c in plat)
        if not angka or not huruf:
            return False

        return plat

    def plat_sudah_ada(self, plat):
        """Periksa apakah plat sudah ada di slot atau antrian.

        Digunakan untuk mencegah duplikasi pendaftaran kendaraan.
        """
        for s in self.slots:
            if s and s.plat == plat:
                return True
        for p, _ in self.antrian:
            if p == plat:
                return True
        return False

    def masuk(self, plat, jenis):
        """Proses kendaraan masuk.

        - Validasi plat
        - Cek duplikasi
        - Jika ada slot kosong: taruh kendaraan di slot pertama kosong dan record aksi ke undo
        - Jika penuh: tambahkan ke antrian dan catat pada undo
        - Mengembalikan True saat berhasil parkir, atau pesan string jika ada masalah.
        """
        plat = self.validasi_plat(plat)
        if not plat:
            return "Format plat salah. Contoh benar: B12A"

        if self.plat_sudah_ada(plat):
            return "Plat sudah terdaftar"

        # cari slot kosong
        for i in range(self.kapasitas):
            if self.slots[i] is None:
                kendaraan = Kendaraan(plat, jenis)
                self.slots[i] = kendaraan
                # simpan aksi untuk memungkinkan undo (hapus dari slot)
                self.undo_stack.append(("masuk", i))
                return True

        # jika tidak ada slot kosong, masukkan ke antrian
        self.antrian.append((plat, jenis))
        self.undo_stack.append(("antrian", plat, jenis))
        return "Slot penuh. Plat masuk antrian"

    def hitung_biaya(self, menit):
        if menit <= 1:
            return 2000
        return 2000 + (menit - 1) * 1000

    def keluar(self, index):
        """Proses kendaraan keluar dari slot `index`.

        - Hitung durasi dan biaya, simpan ke `riwayat`.
        - Catat aksi pada `undo_stack` untuk kemungkinan rollback.
        - Kosongkan slot dan jika ada antrian, pindahkan head antrian ke slot ini.
        - Mengembalikan nilai biaya atau False jika slot kosong.
        """
        kendaraan = self.slots[index]
        if kendaraan is None:
            return False

        keluar = datetime.now()
        # durasi dalam menit, minimal 1
        durasi = max(1, int((keluar - kendaraan.waktu_masuk).total_seconds() // 60))
        biaya = self.hitung_biaya(durasi)

        data = {
            "plat": kendaraan.plat,
            "jenis": kendaraan.jenis,
            "masuk": kendaraan.waktu_masuk,
            "keluar": keluar,
            "durasi": durasi,
            "biaya": biaya
        }
        self.riwayat.append(data)
        # simpan kendaraan lama supaya undo bisa restore
        self.undo_stack.append(("keluar", index, kendaraan))
        self.slots[index] = None

        # jika ada antrian, isi slot kosong dengan head antrian
        if self.antrian:
            p, j = self.antrian.pop(0)
            self.masuk(p, j)

        return biaya

    def undo(self):
        if not self.undo_stack:
            return False
        # ambil aksi terakhir
        aksi = self.undo_stack.pop()
        tipe = aksi[0]

        if tipe == "masuk":
            # undo dari sebuah parkir: kosongkan kembali slot
            index = aksi[1]
            self.slots[index] = None

        elif tipe == "antrian":
            # undo menambahkan ke antrian: hapus entri antrian yang sesuai
            plat, jenis = aksi[1], aksi[2]
            for i, (p, _) in enumerate(self.antrian):
                if p == plat:
                    self.antrian.pop(i)
                    break

        elif tipe == "keluar":
            # undo keluar: kembalikan kendaraan ke slot dan hapus riwayat terakhir
            index, kendaraan = aksi[1], aksi[2]
            self.slots[index] = kendaraan

            # Hapus 1 data riwayat terakhir dari kendaraan itu
            for r in reversed(self.riwayat):
                if r["plat"] == kendaraan.plat:
                    self.riwayat.remove(r)
                    break

        return True
