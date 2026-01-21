# core/rules.py

SLANG_DICTIONARY = {
    "teman" : "teman",
    "tmn" : "teman",
    "temanku" : "teman",
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
    "membagikan": "bagi", 
    "bagi": "bagi",
    "berbagi": "bagi",
    "temanku": "teman", 
    "kawanku": "teman",
    "sahabatku": "teman",
    "makanan": "makan",
    "membelikan": "beli", 
    "beliin": "beli",
    "unuk": "untuk", # Typo spesifik kamu
    "minuman": "minum",
    "haus": "haus", # Pastikan ada
    "kehausan": "haus",
    "memberikan": "memberi",  # KUNCI 1
    "membuatkan": "buat",     # KUNCI 2
    "bikinin": "buat",
    "masakin": "masak",
    "nyiapin": "siap",
    "menyiapkan": "siap",
    "makanan": "makan"
}

# --- C. FEEDBACK BANK ---
# --- 7. SMART FEEDBACK BANK (STRUKTUR BARU) ---
# Format: "Kategori": { "keyword_trigger": [list_feedback], "default": [list_umum] }
FEEDBACK_BANK = {
    "Friend": {
        "healping": [ # Kalau ada kata 'bantu', 'tolong'
            "Wah, pasti dia merasa sangat terbantu. Lanjutkan jiwa sosialmu!",
            "Berbagi beban itu meringankan pundak temanmu. Mulia banget.",
            "Satu tindakan kecilmu bisa mengubah hari buruknya jadi cerah.",
            "Wuih, ringan tangan banget! Temen lo pasti ngerasa beruntung punya lo.",
            "Definisi 'Real Bestie' ya gini nih, ada pas seneng maupun susah. Respect!",
            "Act of service lo ke temen bikin hati adem. Lanjutkan tren positif ini!"
        ],
        "hearing": [ # Kalau ada kata 'dengerin', 'curhat'
            "Fix, kamu calon teman curhat favorit satu angkatan.",
            "Kadang sekadar mendengarkan itu obat terbaik buat teman.",
            "Peka banget sih! Gak semua orang bisa sepeduli ini.",
            "POV: Temen curhat idaman. Kuping lo layak dapet award pendengar terbaik! 🏆",
            "Valid banget! Kadang temen cuma butuh didengerin, dan lo lakuin itu."
        ],
        "teaching": [
            "Mengajarkan ilmu itu amal jariyah lho!",
            "Wah, kamu sudah jadi guru kecil nih."
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
            "Solidaritas tanpa batas! Jangan lelah berbuat baik ke kawan ya.",
            "Solidaritas tanpa batas! Lo support system terbaik satu sekolah sih. 🔥",
            "Ini baru namanya friendship goals. Lo layak dapet predikat temen sejati!",
            "Kebaikan lo valid banget, no debat. Temen sejati emang beda levelnya.",
            "Fix, lo orangnya peka banget sama kondisi sekitar. Vibes positifnya nular!",
            "Satu kebaikan kecil lo hari ini, impact-nya gede banget buat bestie lo.",
            "Gokil, lo ga fake friend! Kebaikan lo tulus dari hati. Menyala abangkuh! 🔥",
            "Temen yang baik itu rezeki, dan lo adalah rezeki buat sirkel lo.",
            "Jangan lelah jadi orang baik ya! Kebaikan lo bakal balik lagi ke lo kok.",
            "Attitude lo ke temen patut dicontoh. Anti toxic club! 🛡️",
            "Lo membuktikan kalau persahabatan itu indah. Keep it up, bestie! ✨"
        ]
    },
    "Self": {
        "rest": [ # Context: Istirahat
            "Jangan lupa istirahat ya! 💤",
            "Istirahat itu produktif lho. Jangan lupa napas ya!",
            "Duh, penting banget nih! Jangan sampai baterai sosialmu 0%. 🔋",
            "Kadang 'tidak melakukan apa-apa' adalah kebaikan terbaik buat otakmu.",
            "Me time sebentar gak bikin dunia runtuh kok. Santai aja."
        ],
        "self_eating": [ # Context: Makanan
            "Self-care bukan egois kok, itu bensin buat jiwamu! ⛽",
            "Jangan lupa makan! Tubuhmu butuh energi buat jadi orang keren.",
            "Nikmati makananmu! Kamu berhak bahagia. 😊"
        ],
        "sport": [
            "Sehat jasmani, sehat rohani! Mantap.",
            "Olahraga bikin pikiran fresh lagi."
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
            "Sayangi dirimu, karena kamu akan hidup bersamanya selamanya. ❤️",
            "Self-love lo ugal-ugalan! Inget, lo pemeran utama di hidup lo sendiri. ✨",
            "Investasi ke diri sendiri ga bakal rugi. Keep growing, you got this! 📈",
            "Menghargai diri sendiri itu skill mahal, dan lo udah punya itu. Slay abis!",
            "Jujur sama diri sendiri itu langkah awal jadi orang sukses. Proud of you!",
            "Disiplin is key! Lo lagi ngebangun versi terbaik diri lo. Semangat!",
            "Mencintai diri sendiri bukan egois, tapi kebutuhan. Lanjutkan vibes positif ini!",
            "Lo keren karena berani tanggung jawab sama kewajiban sendiri. That's mature!",
            "Fokus lo keren banget. Masa depan cerah udah nunggu di depan mata! 🌅",
            "Gapapa pelan-pelan, yang penting progress. Hargai setiap langkah kecil lo.",
            "Sayangi dirimu, karena cuma lo yang bakal nemenin diri lo selamanya. ❤️"
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
            "Menghargai orang yang tidak dikenal itu tanda tingginya adabmu.",
            "Jiwa sosial lo di luar nalar! Berbuat baik tanpa mandang siapa orangnya. 🤯",
            "Lo baru aja bikin sekolah jadi tempat yang lebih nyaman. Respect setinggi langit!",
            "Mulia banget, mau bantu orang/lingkungan yang ga dikenal. Calon pemimpin masa depan! 🦁",
            "Positive vibes only! Kebaikan lo ke orang lain itu emas banget nilainya.",
            "Gapapa ga dikenal, yang penting pahalanya ngalir terus. Keren abis!",
            "Attitude lo kelas banget. Sopan santun adalah mata uang yang berlaku di mana aja.",
            "Peduli lingkungan sekolah = peduli masa depan. Lo pahlawan tanpa jubah! 🦸‍♂️",
            "The real agent of change. Hal kecil gini yang bikin dunia jadi lebih baik.",
            "Siapa tau dari satu kebaikan ini, lo dapet rezeki tak terduga. Aamiin!",
            "Lo membuktikan kalau orang baik itu masih ada. Thanks for being you! 💖"
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
            "Kedamaian hati > Memenangkan perdebatan. Kamu cerdas emosional! 🧠",
            "Kedewasaan lo di atas rata-rata! Memaafkan itu jauh lebih keren daripada balas dendam. 🤝",
            "Lo milih damai daripada drama? Itu keputusan paling 'Sigma' yang pernah ada. 🗿",
            "Hati lo seluas samudra. Nurunin ego itu susah, tapi lo bisa. Salut!",
            "Kill them with kindness. Biarin mereka malu sendiri sama kebaikan lo. 😉",
            "Mental baja! Lo ga gampang kepancing emosi. Ini baru jagoan sejati.",
            "Fokus ke depan, lupain drama yang ga penting. Lo udah level up! 🆙",
            "Memutus rantai kebencian itu tugas orang terpilih. Dan itu elo.",
            "Lo cerdas emosional. Tau kapan harus diam, tau kapan harus damai.",
            "Berdamai sama musuh itu flex paling gokil sih. Respect maksimal!",
            "Langit ga perlu ngejelasin kalau dia tinggi. Tetep baik walau dijahatin ya! 🌈"
        ]
    }
}

# Mapping Keyword ke Sub-Kategori Feedback
CONTEXT_MAPPING = {
    # KATEGORI SELF (Diri Sendiri)
    "Self": {
        "makan": "self_eating",
        "minum": "self_eating",
        "masak": "self_eating",
        "belajar": "study",
        "baca": "study",
        "tidur": "rest",
        "lari": "sport",
        "senam": "sport"
    },

    # KATEGORI FRIEND (Orang Lain / Hewan)
    "Friend": {
        "makan": "sharing_food",    # <--- KUNCINYA DI SINI
        "suap": "sharing_food",
        "masak": "sharing_food",
        "bagi": "sharing_food",
        "traktir": "sharing_food",
        "ajar": "teaching",
        "ngajarin": "teaching",
        "dengar": "hearing",
        "bantu": "helping",
        "tolong": "helping"
    }
}