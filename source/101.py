import customtkinter as ctk
from tkinter import messagebox
import json
import os

version = "v1.0.1"
ctk.set_appearance_mode("Dark")  # System, Dark, Light
ctk.set_default_color_theme("dark-blue")  # blue, dark-blue, green


COLORS = {
    "bg_main": "#36393F",       
    "bg_sec": "#2F3136",        
    "card": "#202225",          
    "accent": "#5865F2",        
    "danger": "#ED4245",        
    "success": "#57F287",      
    "text_main": "#FFFFFF",     
    "text_dim": "#B9BBBE",      
    "border_warn": "#FAA61A"    
}

ROLES = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]
ROLE_KOREAN = ["탑", "정글", "미드", "원딜", "서폿"]

class Player:
    def __init__(self, name, scores):
        self.name = name
        self.scores = scores

    def to_dict(self):
        return {'name': self.name, 'scores': self.scores}

    @staticmethod
    def from_dict(data):
        return Player(data['name'], data['scores'])

class AddPlayerDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("참가자 등록")
        self.geometry("400x650")
        self.configure(fg_color=COLORS["bg_main"])
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        self.focus_force()

        # 헤더
        title_lbl = ctk.CTkLabel(self, text="NEW PLAYER", font=("Roboto Medium", 20), text_color=COLORS["text_main"])
        title_lbl.pack(pady=(20, 10))

        self.name_entry = ctk.CTkEntry(self, placeholder_text="이름 입력", 
                                       width=300, height=40, corner_radius=10,
                                       fg_color=COLORS["card"], border_color=COLORS["bg_sec"])
        self.name_entry.pack(pady=10)


        score_frame = ctk.CTkFrame(self, fg_color="transparent")
        score_frame.pack(pady=10, padx=20, fill="x")

        self.score_vars = {}
        self.score_labels = {}

        for i, role in enumerate(ROLES):
            row = ctk.CTkFrame(score_frame, fg_color=COLORS["bg_sec"], corner_radius=8)
            row.pack(fill="x", pady=5, ipady=5)

            lbl = ctk.CTkLabel(row, text=ROLE_KOREAN[i], width=50, font=("Roboto", 12, "bold"), text_color=COLORS["text_dim"])
            lbl.pack(side="left", padx=10)

            val_lbl = ctk.CTkLabel(row, text="5", width=30, font=("Roboto", 14, "bold"), text_color=COLORS["accent"])
            val_lbl.pack(side="right", padx=10)
            self.score_labels[role] = val_lbl

            var = ctk.IntVar(value=5)
            self.score_vars[role] = var
            
            slider = ctk.CTkSlider(row, from_=0, to=10, number_of_steps=10, variable=var,
                                   command=lambda v, r=role: self.update_label(r, v),
                                   progress_color=COLORS["accent"], button_color="white", button_hover_color=COLORS["accent"])
            slider.pack(side="right", fill="x", expand=True, padx=10)

        # 저장 버튼
        btn_save = ctk.CTkButton(self, text="등록 완료", command=self.save_player,
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
        new_player = Player(name, scores)
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

        # Grid Layout
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

        self.red_score_lbl.configure(text=str(r_score) if r_name else "-")
        self.blue_score_lbl.configure(text=str(b_score) if b_name else "-")

        if r_name and b_name:
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
    def __init__(self, parent, name, delete_command):
        super().__init__(parent, fg_color=COLORS["card"], corner_radius=8)
        self.pack(fill="x", pady=2)
        
        self.name_lbl = ctk.CTkLabel(self, text=name, font=("Roboto", 12), text_color=COLORS["text_main"], anchor="w")
        self.name_lbl.pack(side="left", padx=10, pady=8)
        
        self.del_btn = ctk.CTkButton(self, text="×", width=25, height=25, 
                                     fg_color="transparent", hover_color=COLORS["danger"], text_color=COLORS["text_dim"],
                                     command=lambda: delete_command(name))
        self.del_btn.pack(side="right", padx=5)

class TeamBuilderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("5v5 Ballancer")
        self.geometry("1100x550")
        self.configure(fg_color=COLORS["bg_main"])

        self.participants = {} 
        self.lanes = []

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, fg_color=COLORS["bg_sec"], corner_radius=0, width=280)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="PARTICIPANTS", font=("Roboto", 16, "bold"), text_color=COLORS["text_dim"]).pack(pady=(30, 10))

        self.scroll_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True, padx=10, pady=5)

        btn_add = ctk.CTkButton(sidebar, text="+  Add Player", command=self.open_add_dialog,
                                height=40, corner_radius=8, fg_color=COLORS["accent"], hover_color="#4752C4",
                                font=("Roboto", 13, "bold"))
        btn_add.pack(fill="x", padx=20, pady=20)

        main_area = ctk.CTkFrame(self, fg_color="transparent")
        main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(main_area, text="MUST DO 5v5", font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]).pack(pady=(10, 5))
        ctk.CTkLabel(main_area, text=f"{version}", font=("Roboto", 12), text_color=COLORS["text_dim"]).pack(pady=(0, 20))

        header_frame = ctk.CTkFrame(main_area, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="RED", font=("Roboto", 16, "bold"), text_color=COLORS["danger"]).pack(side="left", padx=20)
        ctk.CTkLabel(header_frame, text="BLUE", font=("Roboto", 16, "bold"), text_color=COLORS["accent"]).pack(side="right", padx=20)

        self.lanes_container = ctk.CTkFrame(main_area, fg_color="transparent")
        self.lanes_container.pack(fill="both", expand=True)

        for i, role in enumerate(ROLES):
            lane = LaneRow(self.lanes_container, i, role, self.participants, self.refresh_combos)
            self.lanes.append(lane)

    def open_add_dialog(self):
        AddPlayerDialog(self, self.add_player)

    def add_player(self, player):
        if player.name in self.participants:
            messagebox.showerror("Error", "Player already exists!")
            return
        self.participants[player.name] = player
        self.update_list_ui()
        self.refresh_combos()
        self.save_data()

    def delete_player(self, name):
        if messagebox.askyesno("Delete", f"'{name}'를 세상에서 지워버려?"):
            del self.participants[name]
            self.update_list_ui()
            self.refresh_combos()
            self.save_data()

    def update_list_ui(self):
        for widget in self.scroll_list.winfo_children():
            widget.destroy()
        for name in sorted(self.participants.keys()):
            PlayerCard(self.scroll_list, name, self.delete_player)

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