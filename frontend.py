import sys
import os 
import random
from PyQt6.QtWidgets import (
    QApplication, QWidget,
    QHBoxLayout, QVBoxLayout,
    QLabel, QFrame,
    QProgressBar, QPushButton
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QTime, QTimer

# Testing Changes
class CarDashboard(QWidget):
    def __init__(self):
        super().__init__()

        # Use Segoe UI for a clean car‑style look
        self.setFont(QFont("Segoe UI", 10))

        # ── Dynamic state ──
        self.dark_mode       = True
        self.speed           = 40      # km/h
        self._speed_dir      = 1
        self.next_distance   = 20.0    # meters
        self.power           = 250     # out of 300
        self.arrival_offset  = 31*60   # seconds until arrival

        # ── Slideshow state ──
        self.slides          = []
        self.current_slide   = 0

        self.setWindowTitle("Car Dashboard")
        self.setFixedSize(1200, 700)

        self._build_ui()
        self._load_slideshow()

        # ── Timers ──
        self.slide_timer   = QTimer(self)       # every 2s: slideshow + distance
        self.slide_timer.timeout.connect(self._on_slide_tick)
        self.slide_timer.start(2000)

        self.second_timer  = QTimer(self)       # every 1s: clock, arrival, speed
        self.second_timer.timeout.connect(self._on_second_tick)
        self.second_timer.start(1000)

        self.power_timer   = QTimer(self)       # every 1min: drain power
        self.power_timer.timeout.connect(self._decrement_power)
        self.power_timer.start(60_000)

        # ── Initial displays ──
        self.set_next_distance(54_000)  # start safe
        self._on_second_tick()          # init time & speed
        self._decrement_power()         # init power
        self.apply_theme()

    # ── Timer callbacks ──

    def _on_slide_tick(self):
        if self.slides:
            self.current_slide = (self.current_slide + 1) % len(self.slides)
            self.slide_lbl.setPixmap(self.slides[self.current_slide])
        self.set_next_distance(random.uniform(5, 20))

    def _on_second_tick(self):
        now = QTime.currentTime()
        self.time_lbl.setText(now.toString("hh:mm"))
        arrival = now.addSecs(self.arrival_offset)
        self.arrival_val_lbl.setText(arrival.toString("hh:mm"))

        # oscillate speed between 40 and 70
        self.speed += self._speed_dir
        if self.speed >= 70:
            self._speed_dir = -1
        elif self.speed <= 40:
            self._speed_dir = 1
        self.speed_lbl.setText(f"{self.speed} km/h")

    def _decrement_power(self):
        if self.power > 0:
            self.power -= 1
            pct = int(self.power / 300 * 100)
            self.power_bar.setValue(self.power)
            self.power_bar.setFormat(f"{pct}%")

    # ── State setter ──

    def set_next_distance(self, meters: float):
        self.next_distance = meters
        self.dist_val_lbl.setText(f"{int(meters)} m")
        self._update_instruction_card()

    # ── Theming & instruction logic ──

    def apply_theme(self):
        if self.dark_mode:
            bg, card, alt, fg, btn_col, ico = (
                "#111", "#1a1a1a", "#222", "white", "#333", "lightgrey"
            )
            track, chunk, pct_text = "#333", "#28a745", "white"
        else:
            bg, card, alt, fg, btn_col, ico = (
                "#f0f0f0", "#fff", "#e0e0e0", "#111", "#ccc", "black"
            )
            track, chunk, pct_text = "#ddd", "#28a745", "black"

        # Window
        self.setStyleSheet(f"background:{bg}; color:{fg}; font-family:Segoe UI;")

        # Top‑bar icons
        for w in (self.bullet_lbl, self.lte_lbl, self.snd_lbl):
            w.setStyleSheet(f"font-size:14px; color:{ico};")
        # Sidebar icons
        for lbl in self.nav_container.findChildren(QLabel):
            lbl.setStyleSheet(f"font-size:24px; color:{ico};")

        # Left panel
        self.left_box.setStyleSheet(f"background:{card}; border-radius:12px;")
        self.speed_lbl.setStyleSheet(f"font-size:48px; color:{fg};")
        self.mode_btn.setStyleSheet(f"""
            QPushButton {{
                background: {btn_col};
                color: {fg};
                border-radius: 25px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {btn_col[:-1]+'5'};
            }}
        """)

        # Power bar styling
        self.power_bar.setFixedHeight(20)
        self.power_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {track};
                border: 2px solid {chunk};
                border-radius: 10px;
                text-align: center;
                color: {pct_text};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background: {chunk};
                border-radius: 10px;
            }}
        """)

        # Right boxes
        self.qbox_frame.setStyleSheet(f"background:{alt}; border-radius:8px;")
        self.arrival_box .setStyleSheet(f"background:{alt}; border-radius:8px; color:{fg};")
        self.dist_box    .setStyleSheet(f"background:{alt}; border-radius:8px; color:{fg};")

        # Instruction card
        self._update_instruction_card()

    def _update_instruction_card(self):
        d = self.next_distance
        if d < 10:
            text, color = "DANGER: Obstacle within 10 m", "#dc3545"
        elif d < 15:
            text, color = "CAUTION: Obstacle approaching", "#ffc107"
        else:
            text, color = "ALL CLEAR", "#28a745"

        self.instr_card .setFixedHeight(100)
        self.instr_label.setText(text)
        self.instr_label.setStyleSheet("font-size:20px; font-weight:bold; color:white;")
        self.instr_card.setStyleSheet(f"background:{color}; border-radius:8px;")

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.mode_btn.setText("Dark Mode" if not self.dark_mode else "Light Mode")
        self.apply_theme()

    # ── UI construction ──

    def _build_ui(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(0,0,0,0)
        main.setSpacing(0)

        # Sidebar
        nav = QVBoxLayout(); nav.setContentsMargins(0,0,0,0); nav.setSpacing(80)
        for icon in [" ", "📍", "☰", "♫", "📞", "🚗", " "]:
            nav.addWidget(QLabel(icon, alignment=Qt.AlignmentFlag.AlignCenter))
        nav.addStretch()
        self.nav_container = QFrame()
        self.nav_container.setFixedWidth(60)
        self.nav_container.setLayout(nav)
        main.addWidget(self.nav_container)

        # Content
        content = QVBoxLayout(); content.setContentsMargins(0,0,0,0); content.setSpacing(0)

        # Top bar
        header = QFrame(); header.setFixedHeight(50)
        h = QHBoxLayout(header); h.setContentsMargins(10,0,10,0)
        self.bullet_lbl = QLabel("● ● ●", alignment=Qt.AlignmentFlag.AlignLeft)
        self.lte_lbl    = QLabel("LTE 🔒", alignment=Qt.AlignmentFlag.AlignLeft)
        self.snd_lbl    = QLabel("🔊", alignment=Qt.AlignmentFlag.AlignLeft)
        for w in (self.bullet_lbl, self.lte_lbl, self.snd_lbl):
            h.addWidget(w)
        h.addStretch()
        self.time_lbl = QLabel("", alignment=Qt.AlignmentFlag.AlignRight)
        self.temp_lbl = QLabel("17°C ", alignment=Qt.AlignmentFlag.AlignRight)
        for w in (self.temp_lbl, self.time_lbl):
            w.setStyleSheet("font-size:14px;")
            h.addWidget(w)
        content.addWidget(header)

        # Body
        body = QHBoxLayout(); body.setContentsMargins(20,0,20,20); body.setSpacing(50)

        # Left box
        self.left_box = QFrame(); self.left_box.setFixedSize(300,600)
        lb = QVBoxLayout(self.left_box); lb.setContentsMargins(20,20,20,20); lb.setSpacing(20)
        car_img = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        cp = os.path.join("assets","car_top_view.png")
        if os.path.exists(cp):
            car_img.setPixmap(QPixmap(cp).scaled(
                260,180, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            car_img.setText("[Car]")
        lb.addWidget(car_img)

        self.speed_lbl = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        lb.addWidget(self.speed_lbl)

        self.mode_btn = QPushButton("Light Mode")
        self.mode_btn.setFixedSize(180,50)
        self.mode_btn.clicked.connect(self.toggle_theme)
        lb.addWidget(self.mode_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        lb.addStretch()

        # ←── NEW: Power inline ──→
        prow = QHBoxLayout()
        prow.setContentsMargins(0,0,0,0)
        prow.setSpacing(10)
        power_lbl = QLabel("Power")
        power_lbl.setStyleSheet("font-size:14px;")
        prow.addWidget(power_lbl)
        self.power_bar = QProgressBar()
        self.power_bar.setRange(0,300)
        self.power_bar.setValue(self.power)
        self.power_bar.setTextVisible(True)
        self.power_bar.setFormat(f"{int(self.power/300*100)}%")
        prow.addWidget(self.power_bar, stretch=1)
        lb.addLayout(prow)

        body.addWidget(self.left_box)

        # Right info box
        right = QFrame(); right.setFixedSize(650,600)
        rb = QVBoxLayout(right); rb.setContentsMargins(20,20,20,20); rb.setSpacing(20)

        # Instruction card
        self.instr_card  = QFrame()
        self.instr_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        ic = QVBoxLayout(self.instr_card); ic.addWidget(self.instr_label)
        rb.addWidget(self.instr_card)

        # Slideshow
        self.qbox_frame = QFrame(); self.qbox_frame.setFixedHeight(300)
        fl = QVBoxLayout(self.qbox_frame)
        self.slide_lbl = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.slide_lbl.setFixedSize(610,300)
        self.slide_lbl.setScaledContents(True)
        fl.addWidget(self.slide_lbl)
        rb.addWidget(self.qbox_frame)

        # Arrival & distance
        ih = QHBoxLayout()
        self.arrival_box = QFrame(); self.arrival_box.setFixedSize(300,80)
        av = QVBoxLayout(self.arrival_box)
        av.addWidget(QLabel("Arrival Time", alignment=Qt.AlignmentFlag.AlignCenter))
        self.arrival_val_lbl = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        av.addWidget(self.arrival_val_lbl)
        ih.addWidget(self.arrival_box)

        self.dist_box = QFrame(); self.dist_box.setFixedSize(300,80)
        dv = QVBoxLayout(self.dist_box)
        dv.addWidget(QLabel("Next Object Distance", alignment=Qt.AlignmentFlag.AlignCenter))
        self.dist_val_lbl = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        dv.addWidget(self.dist_val_lbl)
        ih.addWidget(self.dist_box)

        rb.addLayout(ih)
        body.addWidget(right)

        content.addLayout(body)
        main.addLayout(content)

    def _load_slideshow(self):
        folder = os.path.join(os.path.dirname(__file__), "data", "CameraA")
        if not os.path.isdir(folder):
            print(f"⚠️ Slideshow folder not found: {folder}")
            return
        self.slides.clear()
        for fn in sorted(os.listdir(folder)):
            if fn.lower().endswith((".png", ".jpg", ".jpeg")):
                pix = QPixmap(os.path.join(folder, fn)).scaled(
                    610,300,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.slides.append(pix)
        if self.slides:
            self.slide_lbl.setPixmap(self.slides[0])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = CarDashboard()
    dashboard.show()
    sys.exit(app.exec())

