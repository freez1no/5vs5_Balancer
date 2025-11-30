import customtkinter as ctk
from tkinter import messagebox
import json
import os

version = "v1.2.0"
ctk.set_appearance_mode("Dark")  # System, Dark, Light
ctk.set_default_color_theme("dark-blue")  # blue, dark-blue, green


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

ROLES = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]
ROLE_KOREAN = ["탑", "정글", "미드", "원딜", "서폿"]
ROLE_OPTIONS = ["선택 안함"] + ROLE_KOREAN

class Player:
    def __init__(self, name, scores, main_role="선택 안함", sub_role="선택 안함"):
        self.name = name
        self.scores = scores
        self.main_role = main_role
        self.sub_role = sub_role

    def to_dict(self):
        return {
            'name': self.name, 
            'scores': self.scores,
            'main_role': self.main_role,
            'sub_role': self.sub_role
        }

    @staticmethod
    def from_dict(data):
        return Player(
            data['name'], 
            data['scores'], 
            data.get('main_role', "선택 안함"), 
            data.get('sub_role', "선택 안함")
        )

class PlayerDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback, player_to_edit=None, original_name=None):
        super().__init__(parent)
        self.callback = callback
        self.player_to_edit = player_to_edit
        self.original_name = original_name

        title_text = "참가자 수정" if player_to_edit else "참가자 등록"
        btn_text = "수정 완료" if player_to_edit else "등록 완료"
        
        self.title(title_text)
        self.geometry("400x550")
        self.configure(fg_color=COLORS["bg_main"])
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        self.focus_force()

        title_lbl = ctk.CTkLabel(self, text=title_text, font=("Roboto Medium", 20), text_color=COLORS["text_main"])
        title_lbl.pack(pady=(20, 10))

        # 이름
        self.name_entry = ctk.CTkEntry(self, placeholder_text="이름 입력", 
                                       width=300, height=40, corner_radius=10,
                                       fg_color=COLORS["card"], border_color=COLORS["bg_sec"])
        self.name_entry.pack(pady=10)
        
        if player_to_edit:
            self.name_entry.insert(0, player_to_edit.name)

        # 역할 선택하는 부분
        role_frame = ctk.CTkFrame(self, fg_color="transparent")
        role_frame.pack(pady=5, padx=50, fill="x")

        # 주 역할
        ctk.CTkLabel(role_frame, text="주 역할", font=("Roboto", 12), text_color=COLORS["text_dim"]).grid(row=0, column=0, padx=5, sticky="w")
        self.main_role_combo = ctk.CTkComboBox(role_frame, values=ROLE_OPTIONS, width=140, state="readonly")
        self.main_role_combo.grid(row=1, column=0, padx=5, pady=(0, 10))
        
        # 부 역할
        ctk.CTkLabel(role_frame, text="부 역할", font=("Roboto", 12), text_color=COLORS["text_dim"]).grid(row=0, column=1, padx=5, sticky="w")
        self.sub_role_combo = ctk.CTkComboBox(role_frame, values=ROLE_OPTIONS, width=140, state="readonly")
        self.sub_role_combo.grid(row=1, column=1, padx=5, pady=(0, 10))

        # 초기값 설정
        if player_to_edit:
            self.main_role_combo.set(player_to_edit.main_role)
            self.sub_role_combo.set(player_to_edit.sub_role)
        else:
            self.main_role_combo.set("선택 안함")
            self.sub_role_combo.set("선택 안함")


        # 점수 슬라이더
        score_container = ctk.CTkFrame(self, fg_color="transparent")
        score_container.pack(pady=10, padx=20, fill="x")

        self.score_vars = {}
        self.score_labels = {}

        for i, role in enumerate(ROLES):
            row = ctk.CTkFrame(score_container, fg_color=COLORS["bg_sec"], corner_radius=8)
            row.pack(fill="x", pady=5, ipady=5)

            lbl = ctk.CTkLabel(row, text=ROLE_KOREAN[i], width=50, font=("Roboto", 12, "bold"), text_color=COLORS["text_dim"])
            lbl.pack(side="left", padx=10)

            initial_val = 5
            if player_to_edit:
                initial_val = player_to_edit.scores.get(role, 5)

            val_lbl = ctk.CTkLabel(row, text=str(initial_val), width=30, font=("Roboto", 14, "bold"), text_color=COLORS["accent"])
            val_lbl.pack(side="right", padx=10)
            self.score_labels[role] = val_lbl

            var = ctk.IntVar(value=initial_val)
            self.score_vars[role] = var
            
            slider = ctk.CTkSlider(row, from_=0, to=10, number_of_steps=10, variable=var,
                                   command=lambda v, r=role: self.update_label(r, v),
                                   progress_color=COLORS["accent"], button_color="white", button_hover_color=COLORS["accent"])
            slider.pack(side="right", fill="x", expand=True, padx=10)

        # 저장 버튼
        btn_save = ctk.CTkButton(self, text=btn_text, command=self.save_player,
                                 width=300, height=45, corner_radius=10,
                                 fg_color=COLORS["success"], hover_color="#43b581",
                                 font=("Roboto", 14, "bold"))
        btn_save.pack(pady=20, side="bottom")

    def update_label(self, role, value):
        self.score_labels[role].configure(text=str(int(value)))

    def save_player(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("입력 오류", "이름을 입력해주세요.")
            return

        scores = {role: self.score_vars[role].get() for role in ROLES}
        main_role = self.main_role_combo.get()
        sub_role = self.sub_role_combo.get()

        new_player = Player(name, scores, main_role, sub_role)
        
        if self.original_name:
            self.callback(new_player, self.original_name)
        else:
            self.callback(new_player)
            
        self.destroy()

class LaneRow(ctk.CTkFrame):
    def __init__(self, parent, role_idx, role_key, players_dict, update_callback):
        super().__init__(parent, fg_color=COLORS["card"], corner_radius=15, border_width=2, border_color=COLORS["bg_sec"])
        self.role_key = role_key
        self.role_name_kr = ROLE_KOREAN[role_idx]
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

        role_badge = ctk.CTkFrame(self, fg_color=COLORS["bg_main"], corner_radius=8, width=80, height=30)
        role_badge.grid(row=0, column=2, padx=10)
        ctk.CTkLabel(role_badge, text=self.role_name_kr, font=("Roboto", 12, "bold"), text_color=COLORS["text_dim"]).place(relx=0.5, rely=0.5, anchor="center")

        self.blue_score_lbl = ctk.CTkLabel(self, text="-", font=("Roboto", 18, "bold"), text_color=COLORS["accent"], width=40)
        self.blue_score_lbl.grid(row=0, column=3, padx=5)

        self.blue_var = ctk.StringVar()
        self.blue_combo = ctk.CTkComboBox(self, variable=self.blue_var, state="readonly",
                                          fg_color=COLORS["bg_sec"], border_color=COLORS["bg_sec"], button_color=COLORS["accent"],
                                          text_color=COLORS["text_main"], dropdown_fg_color=COLORS["bg_sec"],
                                          command=self.on_select)
        self.blue_combo.grid(row=0, column=4, padx=15, pady=15, sticky="ew")

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
        
        # 이름과 역할 표시 로직
        display_text = player.name
        roles = []
        if player.main_role != "선택 안함":
            roles.append(player.main_role)
        if player.sub_role != "선택 안함":
            roles.append(player.sub_role)
            
        if roles:
            display_text += f" ({', '.join(roles)})"

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
        self.geometry("1100x550") # 메인창 크기
        self.configure(fg_color=COLORS["bg_main"])

        self.participants = {} 
        self.lanes = []

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
        btn_add.pack(fill="x", padx=15, pady=20)

        # 메인 영역
        main_area = ctk.CTkFrame(self, fg_color="transparent")
        main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(main_area, text="MUST DO 5v5", font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]).pack(pady=(5, 0)) #프로그램 타이틀
        ctk.CTkLabel(main_area, text=f"{version}", font=("Roboto", 12), text_color=COLORS["text_dim"]).pack(pady=(0, 15))

        # 팀 헤더
        header_frame = ctk.CTkFrame(main_area, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=5)
        
        # Red Header
        self.red_header_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        self.red_header_frame.pack(side="left", padx=20)
        ctk.CTkLabel(self.red_header_frame, text="RED TEAM", font=("Roboto", 18, "bold"), text_color=COLORS["danger"]).pack(side="left")
        self.red_total_lbl = ctk.CTkLabel(self.red_header_frame, text="Total: 0", font=("Roboto", 14), text_color=COLORS["danger"])
        self.red_total_lbl.pack(side="left", padx=(10, 0))

        # Blue Header
        self.blue_header_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        self.blue_header_frame.pack(side="right", padx=20)
        self.blue_total_lbl = ctk.CTkLabel(self.blue_header_frame, text="Total: 0", font=("Roboto", 14), text_color=COLORS["accent"])
        self.blue_total_lbl.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(self.blue_header_frame, text="BLUE TEAM", font=("Roboto", 18, "bold"), text_color=COLORS["accent"]).pack(side="left")

        # Lanes
        self.lanes_container = ctk.CTkFrame(main_area, fg_color="transparent")
        self.lanes_container.pack(fill="both", expand=True)

        for i, role in enumerate(ROLES):
            lane = LaneRow(self.lanes_container, i, role, self.participants, self.refresh_combos)
            self.lanes.append(lane)

    def open_add_dialog(self):
        PlayerDialog(self, self.add_player_callback)

    def open_edit_dialog(self, name):
        if name in self.participants:
            player = self.participants[name]
            PlayerDialog(self, self.edit_player_callback, player_to_edit=player, original_name=name)

    def add_player_callback(self, player):
        if player.name in self.participants:
            messagebox.showerror("Error", "이미 존재하는 이름입니다!")
            return
        self.participants[player.name] = player
        self.update_list_ui()
        self.refresh_combos()
        self.save_data()

    def edit_player_callback(self, new_player, original_name):
        if new_player.name != original_name and new_player.name in self.participants:
             messagebox.showerror("Error", "변경된 이름이 이미 존재합니다!")
             return

        if original_name in self.participants:
            del self.participants[original_name]
        
        self.participants[new_player.name] = new_player
        self.update_list_ui()
        self.refresh_combos()
        self.save_data()

    def delete_player(self, name):
        if messagebox.askyesno("Delete", f"'{name}' 참가자를 삭제하시겠습니까?"):
            del self.participants[name]
            self.update_list_ui()
            self.refresh_combos()
            self.save_data()

    def update_list_ui(self):
        for widget in self.scroll_list.winfo_children():
            widget.destroy()
        for name in sorted(self.participants.keys()):
            # Player 객체를 직접 전달하여 내부에서 역할 정보를 사용할 수 있게 함
            player = self.participants[name]
            PlayerCard(self.scroll_list, player, self.open_edit_dialog, self.delete_player)

    def refresh_combos(self, event=None):
        selected_set = set()
        for lane in self.lanes:
            r = lane.red_var.get()
            b = lane.blue_var.get()
            if r: selected_set.add(r)
            if b: selected_set.add(b)
            
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

    def save_data(self):
        data = {name: p.to_dict() for name, p in self.participants.items()}
        try:
            with open("participants.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Save failed: {e}")

    def load_data(self):
        if os.path.exists("participants.json"):
            try:
                with open("participants.json", "r", encoding="utf-8") as f:
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