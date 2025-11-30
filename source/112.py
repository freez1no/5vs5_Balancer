import customtkinter as ctk
from tkinter import messagebox, filedialog
import json
import os

version = "v1.1.2"
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

COLORS = {
    "bg_main": "#36393F",       
    "bg_sec": "#2F3136",        
    "card": "#202225",          
    "accent": "#5865F2",        
    "danger": "#ED4245",        
    "success": "#57F287",      
    "edit": "#FAA61A",          
    "text_main": "#FFFFFF",     
    "text_dim": "#B9BBBE",      
    "border_warn": "#FAA61A"    
}

# 로케일 데이터
ROLES_KEY = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]
LOCALE = {
    "KR": {
        "roles": ["탑", "정글", "미드", "원딜", "서폿"],
        "role_opts": ["선택 안함", "탑", "정글", "미드", "원딜", "서폿"]
    },
    "EN": {
        "roles": ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"],
        "role_opts": ["None", "TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]
    }
}

class Player:
    def __init__(self, name, scores, main_role="선택 안함", sub_role="선택 안함", wins=0, losses=0):
        self.name = name
        self.scores = scores
        self.main_role = main_role
        self.sub_role = sub_role
        self.wins = wins
        self.losses = losses

    def to_dict(self):
        return {
            'name': self.name, 
            'scores': self.scores,
            'main_role': self.main_role,
            'sub_role': self.sub_role,
            'wins': self.wins,
            'losses': self.losses
        }

    @staticmethod
    def from_dict(data):
        return Player(
            data['name'], 
            data['scores'], 
            data.get('main_role', "선택 안함"), 
            data.get('sub_role', "선택 안함"),
            data.get('wins', 0),    # 하위 호환성 (기존 데이터 없을 시 0)
            data.get('losses', 0)
        )

class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, parent, participants):
        super().__init__(parent)
        self.title("Match History")
        self.geometry("600x600")
        self.configure(fg_color=COLORS["bg_main"])
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text="HALL OF FAME", font=("Roboto Medium", 20), text_color=COLORS["text_main"]).pack(pady=20)

        # 헤더
        header_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_sec"], height=40)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Matches(총 경기 수) 컬럼
        headers = ["Name", "Matches", "Wins", "Losses", "Win Rate"]
        widths = [140, 70, 70, 70, 90]
        
        for i, h in enumerate(headers):
            lbl = ctk.CTkLabel(header_frame, text=h, font=("Roboto", 12, "bold"), width=widths[i], text_color=COLORS["text_dim"])
            lbl.pack(side="left", padx=5)

        # 리스트 (총 경기 수 순 정렬)
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        sorted_players = sorted(participants.values(), key=lambda p: (p.wins + p.losses, p.wins / (p.wins + p.losses) if (p.wins + p.losses) > 0 else 0), reverse=True)

        for p in sorted_players:
            row = ctk.CTkFrame(scroll, fg_color=COLORS["card"])
            row.pack(fill="x", pady=2)
            
            total = p.wins + p.losses
            rate = f"{(p.wins/total)*100:.1f}%" if total > 0 else "-"
            
            ctk.CTkLabel(row, text=p.name, width=140, anchor="w", text_color=COLORS["text_main"]).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(total), width=70, text_color=COLORS["text_main"]).pack(side="left", padx=5) # Matches 표시
            ctk.CTkLabel(row, text=str(p.wins), width=70, text_color=COLORS["success"]).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(p.losses), width=70, text_color=COLORS["danger"]).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=rate, width=90, text_color=COLORS["accent"]).pack(side="left", padx=5)

class PlayerDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback, current_lang="KR", player_to_edit=None, original_name=None):
        super().__init__(parent)
        self.callback = callback
        self.current_lang = current_lang
        self.player_to_edit = player_to_edit
        self.original_name = original_name

        self.role_names = LOCALE[self.current_lang]["roles"]
        self.role_opts = LOCALE[self.current_lang]["role_opts"]

        title_text = "Edit Player" if player_to_edit else "Add Player"
        btn_text = "Save" if player_to_edit else "Register"
        
        self.title(title_text)
        self.geometry("400x550")
        self.configure(fg_color=COLORS["bg_main"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text=title_text, font=("Roboto Medium", 20), text_color=COLORS["text_main"]).pack(pady=(20, 10))

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Name", width=300, height=40, fg_color=COLORS["card"])
        self.name_entry.pack(pady=10)
        
        if player_to_edit:
            self.name_entry.insert(0, player_to_edit.name)

        # 역할 선택
        role_frame = ctk.CTkFrame(self, fg_color="transparent")
        role_frame.pack(pady=5, padx=50, fill="x")

        ctk.CTkLabel(role_frame, text="Main Role", font=("Roboto", 12), text_color=COLORS["text_dim"]).grid(row=0, column=0, padx=5, sticky="w")
        self.main_role_combo = ctk.CTkComboBox(role_frame, values=self.role_opts, width=140, state="readonly")
        self.main_role_combo.grid(row=1, column=0, padx=5, pady=(0, 10))
        
        ctk.CTkLabel(role_frame, text="Sub Role", font=("Roboto", 12), text_color=COLORS["text_dim"]).grid(row=0, column=1, padx=5, sticky="w")
        self.sub_role_combo = ctk.CTkComboBox(role_frame, values=self.role_opts, width=140, state="readonly")
        self.sub_role_combo.grid(row=1, column=1, padx=5, pady=(0, 10))

        if player_to_edit:
            # 기존 데이터가 로케일 옵션에 없을 수 있으므로(언어 변경 시), 값 체크 후 설정
            m_role = player_to_edit.main_role if player_to_edit.main_role in self.role_opts else self.role_opts[0]
            s_role = player_to_edit.sub_role if player_to_edit.sub_role in self.role_opts else self.role_opts[0]
            self.main_role_combo.set(m_role)
            self.sub_role_combo.set(s_role)
        else:
            self.main_role_combo.set(self.role_opts[0])
            self.sub_role_combo.set(self.role_opts[0])

        # 점수 슬라이더
        score_container = ctk.CTkFrame(self, fg_color="transparent")
        score_container.pack(pady=10, padx=20, fill="x")

        self.score_vars = {}
        self.score_labels = {}

        for i, role_key in enumerate(ROLES_KEY):
            row = ctk.CTkFrame(score_container, fg_color=COLORS["bg_sec"], corner_radius=8)
            row.pack(fill="x", pady=5, ipady=5)

            lbl = ctk.CTkLabel(row, text=self.role_names[i], width=60, font=("Roboto", 12, "bold"), text_color=COLORS["text_dim"])
            lbl.pack(side="left", padx=10)

            initial_val = 5
            if player_to_edit:
                initial_val = player_to_edit.scores.get(role_key, 5)

            val_lbl = ctk.CTkLabel(row, text=str(initial_val), width=30, font=("Roboto", 14, "bold"), text_color=COLORS["accent"])
            val_lbl.pack(side="right", padx=10)
            self.score_labels[role_key] = val_lbl

            var = ctk.IntVar(value=initial_val)
            self.score_vars[role_key] = var
            
            slider = ctk.CTkSlider(row, from_=0, to=10, number_of_steps=10, variable=var,
                                   command=lambda v, r=role_key: self.update_label(r, v),
                                   progress_color=COLORS["accent"], button_color="white", button_hover_color=COLORS["accent"])
            slider.pack(side="right", fill="x", expand=True, padx=10)

        ctk.CTkButton(self, text=btn_text, command=self.save_player, width=300, height=45, fg_color=COLORS["success"], font=("Roboto", 14, "bold")).pack(pady=20, side="bottom")

    def update_label(self, role, value):
        self.score_labels[role].configure(text=str(int(value)))

    def save_player(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Error", "Name required.")
            return

        scores = {role: self.score_vars[role].get() for role in ROLES_KEY}
        
        # 기존 승/패 정보 유지
        wins = 0
        losses = 0
        if self.player_to_edit:
            wins = self.player_to_edit.wins
            losses = self.player_to_edit.losses

        new_player = Player(name, scores, self.main_role_combo.get(), self.sub_role_combo.get(), wins, losses)
        
        if self.original_name:
            self.callback(new_player, self.original_name)
        else:
            self.callback(new_player)
        self.destroy()

class LaneRow(ctk.CTkFrame):
    def __init__(self, parent, role_idx, role_key, players_dict, update_callback):
        super().__init__(parent, fg_color=COLORS["card"], corner_radius=15, border_width=2, border_color=COLORS["bg_sec"])
        self.role_key = role_key
        self.role_idx = role_idx
        self.players_dict = players_dict
        self.update_callback = update_callback 
        self.pack(fill='x', pady=8, padx=10)

        self.columnconfigure(0, weight=1) 
        self.columnconfigure(1, weight=0) 
        self.columnconfigure(2, weight=0) 
        self.columnconfigure(3, weight=0) 
        self.columnconfigure(4, weight=1) 

        self.red_var = ctk.StringVar()
        self.red_combo = ctk.CTkComboBox(self, variable=self.red_var, state="readonly", 
                                         fg_color=COLORS["bg_sec"], border_color=COLORS["bg_sec"], button_color=COLORS["danger"],
                                         text_color=COLORS["text_main"], dropdown_fg_color=COLORS["bg_sec"],
                                         command=self.on_select)
        self.red_combo.grid(row=0, column=0, padx=15, pady=15, sticky="ew")

        self.red_score_lbl = ctk.CTkLabel(self, text="-", font=("Roboto", 18, "bold"), text_color=COLORS["danger"], width=40)
        self.red_score_lbl.grid(row=0, column=1, padx=5)

        # 역할 뱃지
        self.role_badge_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_main"], corner_radius=8, width=80, height=30)
        self.role_badge_frame.grid(row=0, column=2, padx=10)
        self.role_lbl = ctk.CTkLabel(self.role_badge_frame, text="", font=("Roboto", 12, "bold"), text_color=COLORS["text_dim"])
        self.role_lbl.place(relx=0.5, rely=0.5, anchor="center")

        self.blue_score_lbl = ctk.CTkLabel(self, text="-", font=("Roboto", 18, "bold"), text_color=COLORS["accent"], width=40)
        self.blue_score_lbl.grid(row=0, column=3, padx=5)

        self.blue_var = ctk.StringVar()
        self.blue_combo = ctk.CTkComboBox(self, variable=self.blue_var, state="readonly",
                                          fg_color=COLORS["bg_sec"], border_color=COLORS["bg_sec"], button_color=COLORS["accent"],
                                          text_color=COLORS["text_main"], dropdown_fg_color=COLORS["bg_sec"],
                                          command=self.on_select)
        self.blue_combo.grid(row=0, column=4, padx=15, pady=15, sticky="ew")
        
        self.update_role_text("KR") # 초기값

    def update_role_text(self, lang_code):
        text = LOCALE[lang_code]["roles"][self.role_idx]
        self.role_lbl.configure(text=text)

    def on_select(self, choice):
        self.update_ui()
        self.update_callback()

    def update_dropdown_options(self, all_players_list, global_selected_set):
        current_red = self.red_var.get()
        red_options = [""] + [name for name in all_players_list if name not in global_selected_set or name == current_red]
        self.red_combo.configure(values=red_options)

        current_blue = self.blue_var.get()
        blue_options = [""] + [name for name in all_players_list if name not in global_selected_set or name == current_blue]
        self.blue_combo.configure(values=blue_options)

    def update_ui(self):
        r_name = self.red_var.get()
        b_name = self.blue_var.get()
        
        r_score = self.players_dict[r_name].scores[self.role_key] if r_name and r_name in self.players_dict else 0
        b_score = self.players_dict[b_name].scores[self.role_key] if b_name and b_name in self.players_dict else 0

        self.red_score_lbl.configure(text=str(r_score) if r_name and r_name in self.players_dict else "-")
        self.blue_score_lbl.configure(text=str(b_score) if b_name and b_name in self.players_dict else "-")

        if r_name and b_name and r_name in self.players_dict and b_name in self.players_dict:
            diff = abs(r_score - b_score)
            if diff >= 4:
                self.configure(border_color=COLORS["danger"])
            elif diff >= 2:
                self.configure(border_color=COLORS["border_warn"])
            else:
                self.configure(border_color=COLORS["bg_sec"])
        else:
            self.configure(border_color=COLORS["bg_sec"])

class PlayerCard(ctk.CTkFrame):
    def __init__(self, parent, player, edit_command, delete_command):
        super().__init__(parent, fg_color=COLORS["card"], corner_radius=6)
        self.pack(fill="x", pady=1) 
        
        display_text = player.name
        roles = []
        if player.main_role not in ["선택 안함", "None"]: roles.append(player.main_role)
        if player.sub_role not in ["선택 안함", "None"]: roles.append(player.sub_role)
        if roles: display_text += f" ({', '.join(roles)})"

        self.name_lbl = ctk.CTkLabel(self, text=display_text, font=("Roboto", 13), text_color=COLORS["text_main"], anchor="w")
        self.name_lbl.pack(side="left", padx=10, pady=5)
        
        self.del_btn = ctk.CTkButton(self, text="×", width=24, height=24, 
                                     fg_color="transparent", hover_color=COLORS["danger"], text_color=COLORS["text_dim"],
                                     font=("Roboto", 14, "bold"),
                                     command=lambda: delete_command(player.name))
        self.del_btn.pack(side="right", padx=(2, 5))

        self.edit_btn = ctk.CTkButton(self, text="✎", width=24, height=24,
                                      fg_color="transparent", hover_color=COLORS["edit"], text_color=COLORS["text_dim"],
                                      font=("Roboto", 14, "bold"),
                                      command=lambda: edit_command(player.name))
        self.edit_btn.pack(side="right", padx=(0, 2))

class TeamBuilderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("5v5 Ballancer")
        self.geometry("1100x650")
        self.configure(fg_color=COLORS["bg_main"])

        self.participants = {} 
        self.lanes = []
        self.current_lang = "KR"
        self.current_file_path = "participants.json"

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 사이드바
        sidebar = ctk.CTkFrame(self, fg_color=COLORS["bg_sec"], corner_radius=0, width=280)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="PARTICIPANTS", font=("Roboto", 16, "bold"), text_color=COLORS["text_dim"]).pack(pady=(20, 10))

        self.scroll_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True, padx=5, pady=5)

        btn_add = ctk.CTkButton(sidebar, text="+  Add Player", command=self.open_add_dialog,
                                height=40, corner_radius=8, fg_color=COLORS["accent"], hover_color="#4752C4",
                                font=("Roboto", 13, "bold"))
        btn_add.pack(fill="x", padx=15, pady=(20, 10))

        btn_load = ctk.CTkButton(sidebar, text="📂  Load Data", command=self.load_external_data,
                                height=40, corner_radius=8, fg_color=COLORS["card"], hover_color=COLORS["bg_main"],
                                font=("Roboto", 13, "bold"), text_color=COLORS["text_dim"])
        btn_load.pack(fill="x", padx=15, pady=(0, 10))

        btn_history = ctk.CTkButton(sidebar, text="📜  History", command=self.open_history,
                                height=40, corner_radius=8, fg_color=COLORS["card"], hover_color=COLORS["bg_main"],
                                font=("Roboto", 13, "bold"), text_color=COLORS["text_dim"])
        btn_history.pack(fill="x", padx=15, pady=(0, 10))

        # 언어선택
        self.btn_lang = ctk.CTkButton(sidebar, text="Language: KR", command=self.toggle_language,
                                height=40, corner_radius=8, fg_color=COLORS["card"], hover_color=COLORS["bg_main"],
                                font=("Roboto", 13, "bold"), text_color=COLORS["text_dim"])
        self.btn_lang.pack(fill="x", padx=15, pady=(0, 20))


        # 메인창
        main_area = ctk.CTkFrame(self, fg_color="transparent")
        main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(main_area, text="MUST DO 5vs5", font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]).pack(pady=(5, 0))
        ctk.CTkLabel(main_area, text=f"{version}", font=("Roboto", 12), text_color=COLORS["text_dim"]).pack(pady=(0, 15))

        header_frame = ctk.CTkFrame(main_area, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=5)
        
        self.red_header_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        self.red_header_frame.pack(side="left", padx=20)
        ctk.CTkLabel(self.red_header_frame, text="RED TEAM", font=("Roboto", 18, "bold"), text_color=COLORS["danger"]).pack(side="left")
        self.red_total_lbl = ctk.CTkLabel(self.red_header_frame, text="Total: 0", font=("Roboto", 14), text_color=COLORS["danger"])
        self.red_total_lbl.pack(side="left", padx=(10, 0))

        self.blue_header_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        self.blue_header_frame.pack(side="right", padx=20)
        self.blue_total_lbl = ctk.CTkLabel(self.blue_header_frame, text="Total: 0", font=("Roboto", 14), text_color=COLORS["accent"])
        self.blue_total_lbl.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(self.blue_header_frame, text="BLUE TEAM", font=("Roboto", 18, "bold"), text_color=COLORS["accent"]).pack(side="left")

        self.lanes_container = ctk.CTkFrame(main_area, fg_color="transparent")
        self.lanes_container.pack(fill="both", expand=True)

        for i, role in enumerate(ROLES_KEY):
            lane = LaneRow(self.lanes_container, i, role, self.participants, self.refresh_combos)
            self.lanes.append(lane)

        # 결과 기록 버튼 (조건부 활성화)
        self.btn_record = ctk.CTkButton(main_area, text="Record Game Result", command=self.record_match,
                                        height=50, corner_radius=10, fg_color=COLORS["success"], 
                                        font=("Roboto", 16, "bold"), state="disabled")
        self.btn_record.pack(fill="x", padx=50, pady=20)

    def toggle_language(self):
        if self.current_lang == "KR":
            self.current_lang = "EN"
        else:
            self.current_lang = "KR"
        
        self.btn_lang.configure(text=f"Language: {self.current_lang}")
        
        # 모든 라인의 역할 텍스트 업데이트
        for lane in self.lanes:
            lane.update_role_text(self.current_lang)

    def open_add_dialog(self):
        PlayerDialog(self, self.add_player_callback, self.current_lang)

    def open_edit_dialog(self, name):
        if name in self.participants:
            player = self.participants[name]
            PlayerDialog(self, self.edit_player_callback, self.current_lang, player_to_edit=player, original_name=name)

    def open_history(self):
        HistoryWindow(self, self.participants)
    
    def load_external_data(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                new_participants = {}
                for name, p_data in data.items():
                    new_participants[name] = Player.from_dict(p_data)
                
                self.participants = new_participants
                
                self.current_file_path = file_path
                self.title(f"5v5 Ballancer - {os.path.basename(file_path)}")

                self.update_list_ui()
                self.refresh_combos()
                messagebox.showinfo("Success", f"Loaded and switched to: {os.path.basename(file_path)}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def add_player_callback(self, player):
        if player.name in self.participants:
            messagebox.showerror("Error", "Name exists.")
            return
        self.participants[player.name] = player
        self.update_list_ui()
        self.refresh_combos()
        self.save_data()

    def edit_player_callback(self, new_player, original_name):
        if new_player.name != original_name and new_player.name in self.participants:
             messagebox.showerror("Error", "Name exists.")
             return

        if original_name in self.participants:
            del self.participants[original_name]
        
        self.participants[new_player.name] = new_player
        self.update_list_ui()
        self.refresh_combos()
        self.save_data()

    def delete_player(self, name):
        if messagebox.askyesno("Delete", f"Remove '{name}'?"):
            del self.participants[name]
            self.update_list_ui()
            self.refresh_combos()
            self.save_data()

    def update_list_ui(self):
        for widget in self.scroll_list.winfo_children():
            widget.destroy()
        for name in sorted(self.participants.keys()):
            player = self.participants[name]
            PlayerCard(self.scroll_list, player, self.open_edit_dialog, self.delete_player)

    def refresh_combos(self, event=None):
        selected_set = set()
        
        red_players = []
        blue_players = []

        for lane in self.lanes:
            r = lane.red_var.get()
            b = lane.blue_var.get()
            if r: 
                selected_set.add(r)
                red_players.append(r)
            if b: 
                selected_set.add(b)
                blue_players.append(b)
            
        all_players_list = sorted(list(self.participants.keys()))

        for lane in self.lanes:
            lane.update_dropdown_options(all_players_list, selected_set)

        red_total = 0
        blue_total = 0
        
        for lane in self.lanes:
            r_name = lane.red_var.get()
            b_name = lane.blue_var.get()
            
            if r_name and r_name in self.participants:
                red_total += self.participants[r_name].scores[lane.role_key]
            
            if b_name and b_name in self.participants:
                blue_total += self.participants[b_name].scores[lane.role_key]
                
        self.red_total_lbl.configure(text=f"Power: {red_total}")
        self.blue_total_lbl.configure(text=f"Power: {blue_total}")

        # 기록 버튼 활성화 체크
        if len(red_players) == 5 and len(blue_players) == 5:
            self.btn_record.configure(state="normal", text="Record Game Result")
        else:
            self.btn_record.configure(state="disabled", text="Fill all 10 slots to record")

    def record_match(self): #전적기록 팝업
        result_dialog = ctk.CTkToplevel(self)
        result_dialog.title("Who Won?")
        result_dialog.geometry("300x150")
        result_dialog.transient(self)
        result_dialog.grab_set()
        
        ctk.CTkLabel(result_dialog, text="Select Winning Team", font=("Roboto", 16, "bold")).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(result_dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)
        
        def commit_result(winner):
            # 점수 반영
            for lane in self.lanes:
                r_name = lane.red_var.get()
                b_name = lane.blue_var.get()
                
                if winner == "RED":
                    self.participants[r_name].wins += 1
                    self.participants[b_name].losses += 1
                else:
                    self.participants[r_name].losses += 1
                    self.participants[b_name].wins += 1
            
            self.save_data()
            messagebox.showinfo("Success", f"{winner} Team Victory recorded!")
            result_dialog.destroy()
            
        ctk.CTkButton(btn_frame, text="RED WIN", fg_color=COLORS["danger"], command=lambda: commit_result("RED")).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(btn_frame, text="BLUE WIN", fg_color=COLORS["accent"], command=lambda: commit_result("BLUE")).pack(side="right", padx=10, expand=True)

    def save_data(self):
        data = {name: p.to_dict() for name, p in self.participants.items()}
        try:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Save failed: {e}")

    def load_data(self):
        if os.path.exists(self.current_file_path):
            try:
                with open(self.current_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for name, p_data in data.items():
                        self.participants[name] = Player.from_dict(p_data)
                self.update_list_ui()
                self.refresh_combos()
            except Exception as e:
                print(f"Load failed: {e}")

if __name__ == "__main__":
    app = TeamBuilderApp()
    app.mainloop()