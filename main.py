import tkinter as tk
from tkinter import messagebox
import random
import math
import os
import winsound
import threading
import time

# ============================
# CLEAN MODERN UI THEME
# ============================
BG_COLOR = "#0b1220"       
PANEL_COLOR = "#0f172a"
BTN_BG = "#121a2a"

ACCENT_GREEN = "#00ff66"
ACCENT_RED = "#ff4444"
ACCENT_YELLOW = "#ffff00"
ACCENT_BLUE = "#38bdf8"

TEXT_PRIMARY = "#e6e6e6"
TEXT_SECONDARY = "#9ca3af"
HIGHLIGHT = "#1f2937"

class RSAVaultFinal:
    def __init__(self, root):
        self.root = root
        self.root.title("RSA MISSION CONTROL v3.2")
        self.root.geometry("1150x680")
        self.root.configure(bg=BG_COLOR)
        # ====== AUDIO STATE ======
        self.music_playing = False
        self.music_muted = False
        self.music_volume = 0.3   # default volume (30%)
        # State Variables
        self.agent_name = "Unknown Agent"
        self.p = self.q = self.n = self.phi = self.e = self.d = 0
        self.time_left = 120       
        self.timer_running = False
        self.time_spent = 0
        self.leaderboard_file = "leaderboard.txt"
        self.difficulty = ""
        self.current_range = (10, 50)

        # Progress tracker
        self.stage_names = [
            "IDENTITY",
            "DIFFICULTY",
            "PRIMES",
            "KEYGEN",
            "ENCRYPT",
            "DECRYPT",
            "SUCCESS"
        ]
        self.current_stage_index = 0

        # ==== NEW: hover sound control (prevents delay) ====
        self.last_hover_time = 0

        self.setup_welcome_screen()

    # ============================
    # 🔊 SOUND EFFECTS (FIXED DELAY)
    # ============================
    def play_hover_sound(self):
        """Play hover sound only if enough time has passed (prevents stacking)."""
        now = time.time()
        if now - self.last_hover_time > 0.0001: 
            self.last_hover_time = now
            threading.Thread(
                target=lambda: winsound.Beep(2400, 15),
                daemon=True
            ).start()

    def play_background_music(self):
        """Play looping background music (built-in Windows only)."""
        if not self.music_playing:
            try:
                winsound.PlaySound(
                    "background.wav",
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
                )
                self.music_playing = True
            except:
                print("Music file not found. Please add background.wav")


    def toggle_mute(self, btn):
        if not self.music_muted:
            winsound.PlaySound(None, winsound.SND_PURGE)
            self.music_muted = True
            btn.config(text="🔇")
        else:
            self.music_muted = False
            self.play_background_music()
            btn.config(text="🔊")



    def stop_background_music(self):
        """Stop music when leaving main page."""
        self.music_playing = False
        winsound.PlaySound(None, winsound.SND_PURGE)


    def update_volume(self, value):
        """Simulate volume by restarting music at different perceived levels."""
        self.music_volume = int(value) / 100

        if not self.music_muted:
            # Stop and restart music (this makes the change feel responsive)
            winsound.PlaySound(None, winsound.SND_PURGE)

            # If volume is very low, we just don't play sound
            if self.music_volume > 0.05:
                winsound.PlaySound(
                    "background.wav",
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
                )


    def play_click_sound(self):
        """Clear confirmation sound on click."""
        threading.Thread(
            target=lambda: winsound.Beep(900, 120),
            daemon=True
        ).start()

    # ============================
    # UI UTILITIES
    # ============================

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def styled_button(self, parent, text, command, color=ACCENT_GREEN, width=22):
        btn = tk.Button(
            parent,
            text=text,
            command=lambda: self.animate_button(btn, command),
            bg=BTN_BG,
            fg=color,
            activebackground=color,
            activeforeground=BG_COLOR,
            font=("Courier New", 11, "bold"),
            width=width,
            height=2,
            bd=1,
            relief="flat",
            cursor="hand2"
        )
        btn.bind("<Enter>", lambda e: [btn.config(bg=color, fg=BG_COLOR), self.play_hover_sound()])
        btn.bind("<Leave>", lambda e: btn.config(bg=BTN_BG, fg=color))
        return btn

    def animate_button(self, btn, command):
        original_color = btn.cget("bg")
        self.play_click_sound()
        btn.config(bg="#ffffff")
        self.root.after(120, lambda: btn.config(bg=original_color))
        self.root.after(150, command)

    def draw_progress(self):
        prog_frame = tk.Frame(self.left_panel, bg=BTN_BG)
        prog_frame.pack(pady=12)

        tk.Label(
            prog_frame,
            text="MISSION PROGRESS",
            fg=ACCENT_GREEN,
            bg=BTN_BG,
            font=("Courier New", 10, "bold")
        ).pack()

        bar_container = tk.Frame(prog_frame, bg=HIGHLIGHT, height=8, width=280)
        bar_container.pack(pady=6)

        filled_width = int((self.current_stage_index / (len(self.stage_names)-1)) * 280)

        bar = tk.Frame(bar_container, bg=ACCENT_GREEN, height=8, width=filled_width)
        bar.place(x=0, y=0)

        dots_frame = tk.Frame(prog_frame, bg=BTN_BG)
        dots_frame.pack(pady=6)

        for i, stage in enumerate(self.stage_names):
            color = ACCENT_GREEN if i <= self.current_stage_index else "#555555"
            dot = tk.Label(
                dots_frame,
                text="●",
                fg=color,
                bg=BTN_BG,
                font=("Courier New", 10)
            )
            dot.pack(side="left", padx=5)

    # ============================
    # MAIN LAYOUT (LEFT + RIGHT)
    # ============================
    def get_difficulty_color(self):
        if self.difficulty == "EASY":
            return ACCENT_GREEN
        elif self.difficulty == "MEDIUM":
            return ACCENT_YELLOW
        elif self.difficulty == "HARD":
            return ACCENT_RED
        return ACCENT_GREEN

    def create_layout(self, stage_name, instruction):
        self.clear_screen()

        # LEFT PANEL
        self.left_panel = tk.Frame(self.root, bg=BTN_BG, width=360)
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)

        agent_card = tk.Frame(self.left_panel, bg=HIGHLIGHT, padx=15, pady=12)
        agent_card.pack(pady=(20, 10), padx=15, fill="x")

        left_info = tk.Frame(agent_card, bg=HIGHLIGHT)
        left_info.pack(side="left")

        tk.Label(
            left_info,
            text="🕵️",
            fg=ACCENT_GREEN,
            bg=HIGHLIGHT,
            font=("Courier New", 14)
        ).pack(side="left")

        tk.Label(
            left_info,
            text=f"  {self.agent_name}",
            fg=ACCENT_GREEN,
            bg=HIGHLIGHT,
            font=("Courier New", 11, "bold")
        ).pack(side="left")

        level_badge = tk.Frame(agent_card, bg=BG_COLOR, padx=8, pady=3)
        level_badge.pack(side="right")

        tk.Label(
            level_badge,
            text=f"🔷 {self.difficulty}",
            fg=self.get_difficulty_color(),
            bg=BG_COLOR,
            font=("Courier New", 10, "bold")
        ).pack()

        timer_pill = tk.Frame(self.left_panel, bg=BG_COLOR, padx=10, pady=5)
        timer_pill.pack(pady=5)

        self.timer_label = tk.Label(
            timer_pill,
            text=f"⏱ {self.time_left}s",
            fg=ACCENT_GREEN,
            bg=BG_COLOR,
            font=("Courier New", 12, "bold")
        )
        self.timer_label.pack()

        self.draw_progress()

        status_card = tk.Frame(self.left_panel, bg=HIGHLIGHT, padx=15, pady=12)
        status_card.pack(pady=15, padx=15, fill="x")

        status_color = self.get_difficulty_color() if stage_name == "DIFFICULTY" else ACCENT_GREEN


        tk.Label(
            status_card,
            text=f"STATUS: {stage_name}",
            fg=status_color,
            bg=HIGHLIGHT,
            font=("Courier New", 12, "bold")
        ).pack(anchor="w")

        tk.Label(
            status_card,
            text=instruction,
            fg=TEXT_PRIMARY,
            bg=HIGHLIGHT,
            font=("Courier New", 10),
            wraplength=300,
            justify="left"
        ).pack(anchor="w", pady=(5, 0))

        self.styled_button(
            self.left_panel,
            "ABORT MISSION",
            self.abort_mission,
            color=ACCENT_RED,
            width=16
        ).pack(side="bottom", pady=25)

        # RIGHT PANEL
        self.workspace = tk.Frame(self.root, bg=BG_COLOR)
        self.workspace.pack(side="right", expand=True, fill="both")

    def abort_mission(self):
        self.stop_background_music()
        self.timer_running = False
        self.time_spent = 0
        self.setup_welcome_screen()

    # ============================
    # ✨ ENHANCED FRONT PAGE ✨
    # ============================
    def setup_welcome_screen(self):
        self.timer_running = False
        self.time_left = 120
        self.time_spent = 0
        self.difficulty = ""            
        self.current_stage_index = 0
        self.clear_screen()
        if not self.music_muted:
            self.play_background_music()


        # Smooth moving scan line
        self.scan_line = tk.Frame(self.root, bg=ACCENT_GREEN, height=2, width=300)
        self.scan_line.place(x=0, y=140)

        def animate_scan():
            x = (self.scan_line.winfo_x() + 12) % max(1, self.root.winfo_width())
            self.scan_line.place(x=x, y=140)
            self.root.after(35, animate_scan)

        animate_scan()

        # Floating cyber particles
        self.particles = []
        for _ in range(12):
            p = tk.Label(self.root, text="•", fg=ACCENT_BLUE, bg=BG_COLOR, font=("Courier New", 10))
            p.place(x=random.randint(0, 1100), y=random.randint(0, 650))
            self.particles.append(p)

        def animate_particles():
            for p in self.particles:
                x = p.winfo_x() + random.choice([-2, -1, 1, 2])
                y = p.winfo_y() + random.choice([-1, 1])
                p.place(x=x % 1100, y=y % 650)
            self.root.after(80, animate_particles)

        animate_particles()

        # ====== MUSIC CONTROL PANEL (TOP RIGHT) ======
        audio_panel = tk.Frame(self.root, bg=HIGHLIGHT, padx=10, pady=6)
        audio_panel.place(relx=0.95, rely=0.05, anchor="ne")

        # Mute / Unmute Button
        self.mute_btn = tk.Button(
            audio_panel,
            text="🔊",
            bg=BTN_BG,
            fg=ACCENT_GREEN,
            font=("Courier New", 12),
            bd=0,
            relief="flat",
            cursor="hand2",
            command=lambda: self.toggle_mute(self.mute_btn)
        )
        self.mute_btn.pack(side="left", padx=5)

        # Volume Label
        tk.Label(
            audio_panel,
            text="VOL",
            fg=TEXT_SECONDARY,
            bg=HIGHLIGHT,
            font=("Courier New", 9)
        ).pack(side="left", padx=5)

        # Volume Slider (visual control)
        self.volume_slider = tk.Scale(
            audio_panel,
            from_=0,
            to=100,
            orient="horizontal",
            length=120,
            bg=HIGHLIGHT,
            fg=ACCENT_GREEN,
            highlightthickness=0,
            troughcolor=BTN_BG,
            showvalue=False,
            command=self.update_volume
        )

        self.volume_slider.set(int(self.music_volume * 100))
        self.volume_slider.pack(side="left")

        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Pulsating glowing title
        self.title_label = tk.Label(
            main_frame,
            text="R S A   V A U L T",
            fg=ACCENT_GREEN,
            bg=BG_COLOR,
            font=("Courier New", 44, "bold")
        )
        self.title_label.pack()

        glow_state = {"brightness": 0}

        def animate_glow():
            glow_state["brightness"] = (glow_state["brightness"] + 1) % 10
            green = 255 - glow_state["brightness"] * 15
            color = f"#00{green:02x}66"
            self.title_label.config(fg=color)
            self.root.after(120, animate_glow)

        animate_glow()

        tk.Frame(main_frame, bg=ACCENT_GREEN, height=2, width=260).pack(pady=8)

        tk.Label(
            main_frame,
            text="Secure Data Transmission Training Simulator",
            fg=TEXT_SECONDARY,
            bg=BG_COLOR,
            font=("Courier New", 12)
        ).pack(pady=10)

        card = tk.Frame(main_frame, bg=HIGHLIGHT, padx=25, pady=20)
        card.pack(pady=20)

        tk.Label(
            card,
            text="MISSION OBJECTIVES",
            fg=ACCENT_BLUE,
            bg=HIGHLIGHT,
            font=("Courier New", 12, "bold")
        ).pack()

        tk.Label(
            card,
            text=(
                "⚙️  Select two prime numbers\n"
                "🔐  Generate encryption keys\n"
                "⚙️  Encrypt a secret message\n"
                "🔓  Decrypt it using your private key"
            ),
            fg=TEXT_PRIMARY,
            bg=HIGHLIGHT,
            font=("Courier New", 10),
            justify="left"
        ).pack(pady=5)


        btn_row = tk.Frame(main_frame, bg=BG_COLOR)
        btn_row.pack(pady=25)

        self.styled_button(btn_row, "▶ INITIATE MISSION", self.agent_id_screen).pack(side="left", padx=12)
        self.styled_button(btn_row, "🏆 VIEW LEADERBOARD", self.show_leaderboard, color=ACCENT_YELLOW).pack(side="left", padx=12)

    
    # ============================
    # AGENT ID
    # ============================
    def agent_id_screen(self):
        self.stop_background_music()
        self.current_stage_index = 0
        self.clear_screen()

        cont = tk.Frame(self.root, bg=BG_COLOR)
        cont.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            cont,
            text="IDENTITY VERIFICATION",
            fg=ACCENT_GREEN,
            bg=BG_COLOR,
            font=("Courier New", 20, "bold")
        ).pack(pady=10)

        tk.Label(
            cont,
            text="Enter your Agent Name to begin your mission:",
            fg=TEXT_PRIMARY,
            bg=BG_COLOR,
            font=("Courier New", 11)
        ).pack(pady=5)

        self.name_entry = tk.Entry(
            cont,
            font=("Courier New", 20),
            bg=BTN_BG,
            fg=ACCENT_GREEN,
            justify="center",
            relief="flat",
            width=22
        )
        self.name_entry.pack(pady=20, ipady=5)
        self.name_entry.focus_set()

        self.styled_button(cont, "AUTHORIZE ACCESS", self.process_agent_id).pack(pady=10)


        back_btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        back_btn_frame.place(relx=0.02, rely=0.95, anchor="sw")

        self.styled_button(
            back_btn_frame,
            "◀ BACK TO HOME",
            self.setup_welcome_screen,
            color=ACCENT_BLUE,
            width=18
        ).pack()

    def process_agent_id(self):
        name = self.name_entry.get().strip()
        if name:
            self.agent_name = name
            self.current_stage_index = 1
            self.difficulty_selection()
        else:
            messagebox.showwarning("IDENTITY ERROR", "Agent ID cannot be empty.")

    # ============================
    # DIFFICULTY
    # ============================
    def difficulty_selection(self):
        self.create_layout(
            "DIFFICULTY",
            f"Agent {self.agent_name}, choose your mission complexity:\n\n"
            "EASY   → Best for beginners\n"
            "MEDIUM → Balanced challenge\n"
            "HARD   → More complex encryption"
        )

        cont = tk.Frame(self.workspace, bg=BG_COLOR)
        cont.place(relx=0.5, rely=0.5, anchor="center")

        levels = {"EASY": (1, 50), "MEDIUM": (50, 150), "HARD": (150, 300)}

        for lvl, r in levels.items():
            color = ACCENT_GREEN if lvl == "EASY" else ACCENT_YELLOW if lvl == "MEDIUM" else ACCENT_RED
            self.styled_button(cont, lvl, lambda l=lvl, rr=r: self.start_game(l, rr), color=color).pack(pady=10)


    def start_game(self, level, r):
        self.time_spent = 0
        self.difficulty = level
        self.current_range = r
        self.time_left = 120         
        self.current_stage_index = 2
        self.timer_running = True
        self.update_timer()           
        self.stage_1_prime_input()

    # ============================
    # STAGE 1: PRIME INPUT
    # ============================
    def stage_1_prime_input(self):
        self.create_layout(
            "STAGE 1: PRIME SELECTION",
            "RSA begins with two PRIME numbers (p and q).\n\n"
            "A PRIME number has only two factors: 1 and itself.\n"
            "Examples: 2, 3, 5, 7,\n\n"
            "\n"
            f"• Enter your own PRIME numbers based on {self.difficulty} level  OR\n"

            "• Click AUTO-GENERATE to let the system choose."
        )

        input_card = tk.Frame(self.workspace, bg=HIGHLIGHT, padx=30, pady=25)
        input_card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            input_card,
            text="🔐 PRIME INPUT TERMINAL",
            fg=ACCENT_BLUE,
            bg=HIGHLIGHT,
            font=("Courier New", 14, "bold")
        ).pack(pady=(0, 10))

        tk.Frame(input_card, bg=ACCENT_GREEN, height=2, width=350).pack(pady=5)

        tk.Label(
            input_card,
            text="Enter two prime numbers",
            fg=TEXT_PRIMARY,
            bg=HIGHLIGHT,
            font=("Courier New", 10)
        ).pack(pady=8)

        form = tk.Frame(input_card, bg=HIGHLIGHT)
        form.pack(pady=10)

        vcmd = (self.root.register(self.validate_numeric_input), "%P")

        tk.Label(
            form, text="PRIME p:",
            fg=ACCENT_GREEN, bg=HIGHLIGHT,
            font=("Courier New", 11, "bold")
        ).grid(row=0, column=0, padx=10, pady=8, sticky="e")

        self.p_entry = tk.Entry(
            form,
            font=("Courier New", 14),
            bg=BTN_BG,
            fg=ACCENT_GREEN,
            justify="center",
            width=20,
            relief="flat",
            validate="key",
            validatecommand=vcmd
        )
        self.p_entry.grid(row=0, column=1, padx=10, pady=8)

        tk.Label(
            form, text="PRIME q:",
            fg=ACCENT_GREEN, bg=HIGHLIGHT,
            font=("Courier New", 11, "bold")
        ).grid(row=1, column=0, padx=10, pady=8, sticky="e")

        self.q_entry = tk.Entry(
            form,
            font=("Courier New", 14),
            bg=BTN_BG,
            fg=ACCENT_GREEN,
            justify="center",
            width=20,
            relief="flat",
            validate="key",
            validatecommand=vcmd
        )
        self.q_entry.grid(row=1, column=1, padx=10, pady=8)

        btn_row = tk.Frame(input_card, bg=HIGHLIGHT)
        btn_row.pack(pady=15)

        self.styled_button(
            btn_row,
            "AUTO-GENERATE",
            self.auto_gen_primes,
            width=16
        ).pack(side="left", padx=10)

        self.styled_button(
            btn_row,
            "VALIDATE",
            self.validate_primes_input,
            color=ACCENT_BLUE,
            width=16
        ).pack(side="left", padx=10)


    def validate_primes_input(self):
        try:
            p_val = int(self.p_entry.get())
            q_val = int(self.q_entry.get())

            if p_val < 0 or q_val < 0:
                messagebox.showerror("INPUT ERROR", "Prime numbers cannot be negative.")
                return

            if p_val == q_val:
                messagebox.showerror("INPUT ERROR", "p and q must be different primes.")
                return

            if not self.validate_prime_by_difficulty(p_val):
                return
            if not self.validate_prime_by_difficulty(q_val):
                return

            if self.is_prime(p_val) and self.is_prime(q_val):
                self.p, self.q = p_val, q_val
                self.current_stage_index = 3
                self.stage_2_keygen()
            else:
                messagebox.showerror("ERROR", "One or both numbers are not prime.")

        except ValueError:
            messagebox.showerror("ERROR", "Please enter valid integers.")


    def auto_gen_primes(self):
        primes = [n for n in range(self.current_range[0], self.current_range[1]) if self.is_prime(n)]
        p, q = random.sample(primes, 2)
        self.p_entry.delete(0, tk.END)
        self.p_entry.insert(0, str(p))
        self.q_entry.delete(0, tk.END)
        self.q_entry.insert(0, str(q))

    # ============================
    # STAGE 2: KEY GENERATION
    # ============================
    def stage_2_keygen(self):
        self.n, self.phi = self.p * self.q, (self.p - 1) * (self.q - 1)

        e_opts = [e for e in range(3, self.phi) if math.gcd(e, self.phi) == 1][:5]

        self.create_layout(
            "STAGE 2: KEY GENERATION",
            f"Your system created:\n"
            f"• Public number n = {self.n}\n"
            f"• Special value φ = {self.phi}\n\n"
            "Pick ONE value of e below."
        )

        btn_cont = tk.Frame(self.workspace, bg=BG_COLOR)
        btn_cont.place(relx=0.5, rely=0.5, anchor="center")

        for val in e_opts:
            self.styled_button(btn_cont, f"CHOOSE e = {val}", lambda v=val: self.calc_d(v)).pack(pady=6)

    def calc_d(self, chosen_e):
        self.e = chosen_e
        self.d = pow(self.e, -1, self.phi)
        self.current_stage_index = 4

        self.create_layout(
            "STAGE 2: PRIVATE KEY",
            "This is your SECRET private key (d).\nWrite it down or remember it!"
        )

        cont = tk.Frame(self.workspace, bg=BG_COLOR)
        cont.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(cont, text="PRIVATE KEY (d)", fg=ACCENT_GREEN, bg=BG_COLOR).pack()
        tk.Label(cont, text=str(self.d), fg=ACCENT_YELLOW, bg=BTN_BG, font=("Courier", 42), padx=25).pack(pady=10)

        self.styled_button(cont, "PROCEED TO ENCRYPTION", self.stage_3_encrypt).pack(pady=20)

    # ============================
    # STAGE 3: ENCRYPTION
    # ============================
    def stage_3_encrypt(self):
        self.current_stage_index = 5

        self.create_layout(
            "STAGE 3: ENCRYPTION",
            "Type a short message (e.g. HELLO).\n"
            "Your message will be converted into secret numbers."
        )

        cont = tk.Frame(self.workspace, bg=BG_COLOR)
        cont.place(relx=0.5, rely=0.5, anchor="center")

        self.msg_entry = tk.Entry(
            cont,
            font=("Courier New", 18),
            bg=BTN_BG,
            fg=ACCENT_GREEN,
            width=26,
            justify="center"  
        )
        self.msg_entry.pack(pady=20)

        self.styled_button(cont, "ENCRYPT MESSAGE", self.encrypt_action).pack()

    def encrypt_action(self):
        msg = self.msg_entry.get()
        if not msg:
            messagebox.showwarning("EMPTY", "Please type a message first.")
            return

        self.encrypted_msg = [pow(ord(c), self.e, self.n) for c in msg]
        self.stage_4_decrypt()

    # ============================
    # STAGE 4: DECRYPTION
    # ============================
    def stage_4_decrypt(self):
        self.current_stage_index = 6

        self.create_layout(
            "STAGE 4: DECRYPTION",
            "Your encrypted message is shown below.\n"
            "Scroll if needed, then enter your PRIVATE KEY (d) to unlock it."
        )

        cont = tk.Frame(self.workspace, bg=BG_COLOR)
        cont.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            cont,
            text="ENCRYPTED MESSAGE",
            fg=ACCENT_BLUE,
            bg=BG_COLOR,
            font=("Courier New", 12, "bold")
        ).pack(pady=5)

        text_frame = tk.Frame(cont, bg=BTN_BG)
        text_frame.pack(pady=10)

        text_box = tk.Text(
            text_frame,
            width=70,
            height=8,
            bg=BTN_BG,
            fg=ACCENT_GREEN,
            font=("Courier New", 10),
            wrap="word",
            relief="flat"
        )
        text_box.pack(side="left")

        scrollbar = tk.Scrollbar(text_frame, command=text_box.yview)
        scrollbar.pack(side="right", fill="y")
        text_box.config(yscrollcommand=scrollbar.set)

        formatted_msg = ", ".join(map(str, self.encrypted_msg))
        text_box.insert("1.0", formatted_msg)
        text_box.config(state="disabled") 

        tk.Label(
            cont,
            text="ENTER PRIVATE KEY (d)",
            fg=ACCENT_RED,
            bg=BG_COLOR,
            font=("Courier New", 11, "bold")
        ).pack(pady=8)

        self.d_input = tk.Entry(
            cont,
            font=("Courier New", 18),
            bg=BTN_BG,
            fg=ACCENT_RED,
            width=15,
            justify="center"
        )
        self.d_input.pack(pady=8)

        self.styled_button(cont, "UNLOCK", self.finish_game, color=ACCENT_RED).pack(pady=10)


    def finish_game(self):
        try:
            if int(self.d_input.get()) == self.d:
                decrypted = "".join([chr(pow(c, self.d, self.n)) for c in self.encrypted_msg])
                self.timer_running = False

                with open(self.leaderboard_file, "a") as f:
                    f.write(f"{self.agent_name},{self.time_spent},{self.difficulty}\n")

                self.show_access_granted(decrypted)
            else:
                messagebox.showerror("DENIED", "Incorrect Private Key.")
        except:
            messagebox.showerror("ERROR", "Please enter a valid number.")

    # ============================
    # SUCCESS SCREEN
    # ============================
    def show_access_granted(self, msg):
        self.create_layout(
            "SUCCESS",
            "Mission accomplished. The vault has been successfully decrypted."
        )

        cont = tk.Frame(self.workspace, bg=BG_COLOR)
        cont.place(relx=0.5, rely=0.5, anchor="center")

        title = tk.Label(
            cont,
            text="ACCESS GRANTED",
            fg=ACCENT_GREEN,
            bg=BG_COLOR,
            font=("Courier New", 26, "bold")
        )
        title.pack(pady=8)

        glow_state = {"level": 0}

        def animate_title_glow():
            glow_state["level"] = (glow_state["level"] + 1) % 8
            green = 200 + glow_state["level"] * 7
            color = f"#00{green:02x}66"
            title.config(fg=color)
            self.root.after(120, animate_title_glow)

        animate_title_glow()


        divider_container = tk.Frame(cont, bg=HIGHLIGHT, height=3, width=450)
        divider_container.pack(pady=8)

        divider = tk.Frame(divider_container, bg=ACCENT_GREEN, height=3, width=120)
        divider.place(x=0, y=0)

        glow = {"x": 0, "direction": 1}

        def smooth_sweep():

            new_x = glow["x"] + 8 * glow["direction"]

            if new_x > 330:
                glow["direction"] = -1
            elif new_x < 0:
                glow["direction"] = 1

            glow["x"] = new_x
            divider.place(x=new_x, y=0)

            brightness = 200 + int(20 * abs(glow["x"] / 330))
            color = f"#00{brightness:02x}66"
            divider.config(bg=color)

            self.root.after(30, smooth_sweep)

        smooth_sweep()


        tk.Label(
            cont,
            text="DECRYPTED MESSAGE",
            fg=ACCENT_BLUE,
            bg=BG_COLOR,
            font=("Courier New", 12, "bold")
        ).pack(pady=5)

        msg_box = tk.Text(
            cont,
            width=65,
            height=5,
            bg=BTN_BG,
            fg="white",
            font=("Courier New", 12),
            wrap="word",
            relief="flat",
            highlightthickness=1,
            highlightbackground=ACCENT_GREEN
        )
        msg_box.pack(pady=8)

        def type_text(i=0):
            if i < len(msg):
                msg_box.insert("end", msg[i])
                self.root.after(30, lambda: type_text(i + 1))
            else:
                msg_box.config(state="disabled")

        type_text()

        tk.Frame(cont, bg=ACCENT_GREEN, height=2, width=420).pack(pady=8)

        self.styled_button(
            cont,
            "RETURN TO MAIN TERMINAL",
            self.setup_welcome_screen,
            width=28
        ).pack(pady=10)



    # ============================
    # ✨ IMPROVED LEADERBOARD ✨
    # ============================
    def show_leaderboard(self):
        self.stop_background_music()
        self.clear_screen()

        header = tk.Label(
            self.root,
            text="🏆 TOP AGENTS — FASTEST COMPLETIONS 🏆",
            fg=ACCENT_YELLOW,
            bg=BG_COLOR,
            font=("Courier New", 20, "bold")
        )
        header.pack(pady=20)

        table_frame = tk.Frame(self.root, bg=BG_COLOR)
        table_frame.pack(expand=True, fill="both", padx=120)

        header_row = tk.Frame(table_frame, bg=HIGHLIGHT)
        header_row.pack(fill="x", pady=5)

        tk.Label(header_row, text="RANK", fg=ACCENT_BLUE, bg=HIGHLIGHT,
                font=("Courier New", 12, "bold"), width=8, anchor="center").pack(side="left")

        tk.Label(header_row, text="AGENT NAME", fg=ACCENT_BLUE, bg=HIGHLIGHT,
                font=("Courier New", 12, "bold"), width=32, anchor="w").pack(side="left")

        tk.Label(header_row, text="TIME TAKEN (s)", fg=ACCENT_BLUE, bg=HIGHLIGHT,
                font=("Courier New", 12, "bold"), width=18, anchor="center").pack(side="left")

        tk.Label(header_row, text="LEVEL", fg=ACCENT_BLUE, bg=HIGHLIGHT,
                font=("Courier New", 12, "bold"), width=12, anchor="center").pack(side="left")

        if os.path.exists(self.leaderboard_file):
            with open(self.leaderboard_file, "r") as f:
                lines = [l.strip().split(",") for l in f.readlines() if "," in l]
                scores = sorted(lines, key=lambda x: int(x[1]))[:10]

            for i, s in enumerate(scores):
                row = tk.Frame(table_frame, bg=BTN_BG)
                row.pack(fill="x", pady=3)

                tk.Label(row, text=f"#{i+1}", fg="white", bg=BTN_BG,
                        font=("Courier New", 12), width=8, anchor="center").pack(side="left")

                tk.Label(row, text=s[0], fg="white", bg=BTN_BG,
                        font=("Courier New", 12), width=30, anchor="w").pack(side="left")

                tk.Label(row, text=s[1] + " s", fg=ACCENT_GREEN, bg=BTN_BG,
                        font=("Courier New", 12), width=18, anchor="center").pack(side="left")

                tk.Label(row, text=s[2], fg=ACCENT_YELLOW, bg=BTN_BG,
                        font=("Courier New", 12), width=12, anchor="center").pack(side="left")

        else:
            tk.Label(
                table_frame,
                text="No mission data recorded yet.",
                fg=TEXT_PRIMARY,
                bg=BG_COLOR,
                font=("Courier New", 12)
            ).pack(pady=30)

        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=30)

        self.styled_button(
            btn_frame,
            "BACK TO MAIN TERMINAL",
            self.setup_welcome_screen,
            width=28
        ).pack()

    # ============================
    # UTILITIES
    # ============================
    def validate_numeric_input(self, P):
        """
        P = proposed new content of the Entry box.
        Allows typing while still enforcing:
        - numbers only
        - digit limit
        - proper range per difficulty
        """

        if P == "":
            return True

        if not P.isdigit():
            return False

        value = int(P)
        digits = len(P)

        if self.difficulty == "EASY":
            if digits > 2:
                return False
            if value > 50:   
                return False
            if value == 0:   
                return False
            return True

        elif self.difficulty == "MEDIUM":
            if digits > 3:
                return False

            if value <= 150:
                return True

            return False


        elif self.difficulty == "HARD":
            if digits > 3:
                return False

            if value <= 300:
                return True

            return False

        return True


    def validate_prime_by_difficulty(self, value: int) -> bool:
        """Check digit length + range based on difficulty."""

        digits = len(str(abs(value))) 

        if self.difficulty == "EASY":
            if digits > 2:
                messagebox.showerror("INPUT ERROR", "EASY mode: primes must be at most 2 digits (1–50).")
                return False
            if not (1 <= value <= 50):
                messagebox.showerror("INPUT ERROR", "EASY mode: primes must be between 1 and 50.")
                return False

        elif self.difficulty == "MEDIUM":
            if digits > 3:
                messagebox.showerror("INPUT ERROR", "MEDIUM mode: primes must be at most 3 digits.")
                return False
            if not (50 <= value <= 150):
                messagebox.showerror("INPUT ERROR", "MEDIUM mode: primes must be between 50 and 150.")
                return False

        elif self.difficulty == "HARD":
            if digits > 3:
                messagebox.showerror("INPUT ERROR", "HARD mode: primes must be at most 3 digits.")
                return False
            if not (150 <= value <= 300):
                messagebox.showerror("INPUT ERROR", "HARD mode: primes must be between 150 and 300.")
                return False

        return True

    def is_prime(self, n):
        if n < 2:
            return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return False
        return True

    def update_timer(self):
        if self.timer_running:
            self.time_left -= 1
            self.time_spent += 1  

            if hasattr(self, 'timer_label'):
                self.timer_label.config(text=f"⏱ {self.time_left}s")

            if self.time_left <= 0:
                self.timer_running = False
                messagebox.showerror("TIME'S UP", "Mission failed — time's out!")
                self.setup_welcome_screen()
                return

            self.root.after(1000, self.update_timer)

# ============================
# RUN GAME
# ============================
if __name__ == "__main__":
    root = tk.Tk()
    app = RSAVaultFinal(root)
    root.mainloop()
