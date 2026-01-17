# core/rules.py

SAW_WEIGHTS = {
    "C1": 0.50, # Bobot Kategori
    "C2": 0.30, # Bobot Kompleksitas (Panjang kalimat)
    "C3": 0.20  # Bobot Kreativitas (Kata unik)
}

VAL_CATEGORY = {
    "Friend": 90, "Stranger": 90, "Self": 60, "Enemy": 60, "Junk": 0
}

# --- B. KEYWORDS FILTER ---
BAD_KEYWORDS = [
    "pukul", "memukul", "tonjok", "menonjok", "tendang", "menendang", 
    "tampar", "menampar", "bunuh", "membunuh", "hajar", "menghajar",
    "ejek", "mengejek", "hina", "menghina", "bodoh", "goblok", "tolol", 
    "anjing", "babi", "bangsat", "rusak", "merusak", "curi", "mencuri"
]

GOOD_CONTEXT_FOR_BAD_WORDS = ["tidak", "jangan", "stop", "cegah", "melarang", "menasehati", "bukan"]

# 2. Blocklist (Benda Mati/Lokasi -> Trigger Environment/Stranger)
BLOCK_KEYWORDS = [
    "kucing", "anjing", "hewan", "tanaman", "bunga", "siram", "menyiram", 
    "sampah", "sapu", "menyapu", "papan", "lantai", "meja", "kursi",
    "lapangan", "kelas", "halaman", "kantin"
]

HUMAN_KEYWORDS = ["teman", "guru", "orang", "adik", "kakak", "ibu", "ayah", "sahabat"]
SELF_KEYWORDS  = ["tidur", "makan", "belajar", "sholat", "doa", "healing", "main game"]
SOCIAL_VIP_KEYWORDS     = ["jenguk", "donasi", "tolong", "traktir"]
SLANG_DICTIONARY = {
    "yg": "yang", 
    "gk": "tidak", 
    "gak": "tidak", 
    "ga": "tidak", 
    "g": "tidak",
    "bgt": "banget", 
    "banger": "banget", 
    "nggak": "tidak", 
    "krn": "karena", 
    "karna": "karena",
    "udh": "sudah", 
    "udah": "sudah", 
    "sdh": "sudah",
    "blm": "belum", 
    "blom": "belum",
    "kalo": "kalau", 
    "klo": "kalau", 
    "bntr": "sebentar", 
    "bentar": "sebentar",
    "tmn": "teman", 
    "temen": "teman",
    "sy": "saya", 
    "gw": "saya", 
    "aku": "saya", 
    "gue": "saya",
    "lg": "lagi", 
    "lgi": "lagi",
    "dgn": "dengan", 
    "dg": "dengan",
    "sm": "sama", 
    "ama": "sama",
    "dr": "dari", 
    "dri": "dari",
    "jgn": "jangan", 
    "jan": "jangan",
    "bs": "bisa", 
    "bisa": "bisa",
    "km": "kamu", 
    "lu": "kamu", 
    "loe": "kamu",
    "utk": "untuk", 
    "untk": "untuk",
    "dlm": "dalam", 
    "dlam": "dalam",
    "bnyk": "banyak", 
    "banyak": "banyak",
    "dtg": "datang", 
    "dateng": "datang",
    "org": "orang", 
    "orang": "orang",
    "trs": "terus", 
    "trus": "terus",
    "tpi": "tapi", 
    "tp": "tapi",
    "ngasih": "memberi", 
    "kasih": "memberi",
    "nonton": "menonton", 
    "liat": "melihat",
    "ntraktir": "traktir",  
    "nyembunyiin": "sembunyi", 
    "ngumpetin": "sembunyi",
    "cs": "orang", 
    "satpam": "orang",
    "ob": "orang",
    "cleaning": "orang",
    "bekal": "makanan"
}

# --- C. FEEDBACK BANK ---
# --- 7. SMART FEEDBACK BANK (STRUKTUR BARU) ---
# Format: "Kategori": { "keyword_trigger": [list_feedback], "default": [list_umum] }
FEEDBACK_BANK = {
    "Friend": {
        "bantu": [ # Kalau ada kata 'bantu', 'tolong'
            "Wah, pasti dia merasa sangat terbantu. Lanjutkan jiwa sosialmu!",
            "Berbagi beban itu meringankan pundak temanmu. Mulia banget.",
            "Satu tindakan kecilmu bisa mengubah hari buruknya jadi cerah."
        ],
        "dengar": [ # Kalau ada kata 'dengerin', 'curhat'
            "Fix, kamu calon teman curhat favorit satu angkatan.",
            "Kadang sekadar mendengarkan itu obat terbaik buat teman.",
            "Peka banget sih! Gak semua orang bisa sepeduli ini."
        ],
        "default": [ # Feedback Umum
            "Wah, kamu teman yang asik! 🤜🤛",
            "Dunia butuh lebih banyak orang sepertimu. 🌍",
            "Kebaikanmu pasti nular ke teman lain. ✨",
            "Definisi teman sejati! Beruntung banget mereka punya kamu.",
            "Hal kecil gini nih yang bikin persahabatan awet selamanya.",
            "Solid banget! Kebaikanmu pasti nular ke satu kelas.",
            "Kamu adalah alasan temanmu tersenyum hari ini. Keren!",
            "Support system terbaik emang harus kayak gini!",
            "Teman yang baik itu rezeki, dan kamu adalah rezeki buat dia. 🎁",
            "Vibes positifmu nular banget sih! Kelas jadi adem.",
            "Ini baru namanya 'Friendship Goals'! 🔥",
            "Kebaikan yang kamu tanam ke teman, bakal panen kebahagiaan nanti.",
            "Solidaritas tanpa batas! Jangan lelah berbuat baik ke kawan ya."
        ]
    },
    "Self": {
        "tidur": [ # Context: Istirahat
            "Jangan lupa istirahat ya! 💤",
            "Istirahat itu produktif lho. Jangan lupa napas ya!",
            "Duh, penting banget nih! Jangan sampai baterai sosialmu 0%. 🔋",
            "Kadang 'tidak melakukan apa-apa' adalah kebaikan terbaik buat otakmu.",
            "Me time sebentar gak bikin dunia runtuh kok. Santai aja."
        ],
        "makan": [ # Context: Makanan
            "Self-care bukan egois kok, itu bensin buat jiwamu! ⛽",
            "Jangan lupa makan! Tubuhmu butuh energi buat jadi orang keren.",
            "Nikmati makananmu! Kamu berhak bahagia. 😊"
        ],
        "default": [
            "Self-love itu penting! Isi energimu dulu. 🔋",
            "Kesehatan mentalmu adalah investasi terbaik. 💪",
            "Mencintai diri sendiri itu langkah awal mencintai orang lain. 🌿",
            "Kalau kamu happy, orang sekitarmu pasti ketularan happy juga. 😊",
            "Investasi terbaik adalah investasi ke kesehatan mentalmu sendiri.",
            "Memperlakukan diri sendiri seperti sahabat terbaik itu wajib lho.",
            "Proud of you! Menghargai diri sendiri itu skill yang mahal.",
            "Sehat mental itu kunci sukses. Jagain terus ya mood-nya! 🛡️",
            "Kamu hebat sudah bertahan sampai hari ini. Kasih reward buat dirimu!",
            "Mengetahui batasan diri itu tanda kedewasaan. Good job.",
            "Sayangi dirimu, karena kamu akan hidup bersamanya selamanya. ❤️"
        ]
    },
    "Stranger": {
        "default": [
            "Wah, berani bantu orang lain itu jiwa pemimpin! 🦁",
            "Siapa tau dia jadi sahabatmu nanti. 🤝", 
            "Dunia butuh lebih banyak orang ramah kayak kamu. Lanjutkan!",
            "Peduli sama orang asing itu level kebaikan tingkat tinggi lho.",
            "Keren! Kamu baru saja membuat lingkungan sekolah jadi lebih hangat.",
            "Keluar dari zona nyaman buat bantu orang lain? Itu mental juara! 🏆",
            "Ramah tamah adalah mata uang yang berlaku di mana saja. Mantap!",
            "Kamu baru saja menanam benih kebaikan di tempat baru. 🌱",
            "Jiwa sosialmu gak pilih-pilih ya. Salut banget!",
            "Menghargai orang yang tidak dikenal itu tanda tingginya adabmu."
        ]
    },
    "Enemy": {
        "default": [
            "Sumpah ini keren. Memaafkan itu butuh mental baja! 🛡️",
            "Gak semua orang bisa nurunin ego kayak gini. Kamu dewasa banget!",
            "Membalas keburukan dengan kebaikan? Itu ciri orang hebat. 👑",
            "Hatimu luas banget. Damai itu jauh lebih indah, kan?",
            "Air yang tenang bisa memadamkan api amarah. Kamu airnya! 💧",
            "Memutus rantai kebencian itu tugas orang-orang terpilih. Keren.",
            "Menang tanpa merendahkan, damai tanpa syarat. Respect!",
            "Hati yang bersih gak nyimpen dendam. Kamu sudah level up!",
            "Pemenang sesungguhnya adalah yang bisa mengalahkan egonya sendiri.",
            "Fokus ke masa depan, lupakan drama masa lalu. Keputusan tepat!",
            "Kedamaian hati > Memenangkan perdebatan. Kamu cerdas emosional! 🧠"
        ]
    },
    "Environment": { # Kategori Ditolak tapi Sopan
        "default": [
            "Wah, pahlawan lingkungan! Tapi yuk fokus ke teman sekelas dulu. 🧹",
            "Bumi berterima kasih! Next time ceritain kebaikan ke orang ya. 🌍"
        ]
    }
}

# Mapping Keyword ke Sub-Kategori Feedback
# Jika input mengandung "key", maka pilih sub-kategori "value"
CONTEXT_MAPPING = {
    "Self": {
        "tidur": "tidur", "istirahat": "tidur", "rebahan": "tidur", "napas": "tidur",
        "makan": "makan", "minum": "makan", "jajan": "makan", "kenyang": "makan"
    },
    "Friend": {
        "bantu": "bantu", "tolong": "bantu", "ajar": "bantu", "traktir": "bantu",
        "dengar": "dengar", "curhat": "dengar", "simak": "dengar"
    }
}