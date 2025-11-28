import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

COLORS = {
    'bg': '#2E3440',        
    'panel': '#3B4252',     
    'fg': '#ECEFF4',        
    'accent': '#88C0D0',    
    'red_team': "#FF0019",  
    'input_bg': '#4C566A',  
    'btn_bg': '#5E81AC',    
    'btn_fg': '#FFFFFF',    
    'warning_low': '#D08770',  
    'warning_high': '#BF616A' 
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

class AddPlayerDialog(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("참가자 추가")
        self.geometry("350x450")
        self.configure(bg=COLORS['bg'])
        self.resizable(False, False)

        self.style = ttk.Style()
        self.style.configure("TLabel", background=COLORS['bg'], foreground=COLORS['fg'], font=("Malgun Gothic", 10))
        self.style.configure("TButton", font=("Malgun Gothic", 10, "bold"))

        tk.Label(self, text="소환사 이름", bg=COLORS['bg'], fg=COLORS['fg'], font=("Malgun Gothic", 11, "bold")).pack(pady=(20, 5))
        self.name_entry = tk.Entry(self, bg=COLORS['input_bg'], fg=COLORS['fg'], insertbackground='white', font=("Malgun Gothic", 10))
        self.name_entry.pack(pady=5, ipadx=5, ipady=3)


        score_frame = tk.Frame(self, bg=COLORS['bg'])
        score_frame.pack(pady=20, padx=20, fill='x')

        self.score_vars = {}
        
        for i, role in enumerate(ROLES):
            row_frame = tk.Frame(score_frame, bg=COLORS['bg'])
            row_frame.pack(fill='x', pady=5)
            
            lbl = tk.Label(row_frame, text=f"{ROLE_KOREAN[i]} (0-10)", width=10, anchor='w', bg=COLORS['bg'], fg=COLORS['fg'], font=("Malgun Gothic", 10))
            lbl.pack(side='left')
            
            var = tk.IntVar(value=5)
            self.score_vars[role] = var
            spin = tk.Spinbox(row_frame, from_=0, to=10, textvariable=var, width=5, font=("Malgun Gothic", 10))
            spin.pack(side='right')

        btn_save = tk.Button(self, text="저장 및 추가", command=self.save_player, 
                             bg=COLORS['btn_bg'], fg=COLORS['btn_fg'], 
                             activebackground=COLORS['accent'], activeforeground='white',
                             relief='flat', font=("Malgun Gothic", 11, "bold"))
        btn_save.pack(pady=20, fill='x', padx=30)

    def save_player(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("입력 오류", "이름을 입력해주세요.", parent=self)
            return

        scores = {}
        for role in ROLES:
            try:
                val = self.score_vars[role].get()
                if not (0 <= val <= 10):
                    raise ValueError
                scores[role] = val
            except:
                messagebox.showerror("입력 오류", "점수는 0에서 10 사이의 숫자여야 합니다.", parent=self)
                return

        new_player = Player(name, scores)
        self.callback(new_player)
        self.destroy()

class LaneRow(tk.Frame):
    def __init__(self, parent, role_idx, role_key, players_dict, update_callback):
        super().__init__(parent, bg=COLORS['panel'], bd=1, relief='solid')
        self.role_key = role_key
        self.role_name_kr = ROLE_KOREAN[role_idx]
        self.players_dict = players_dict
        self.update_callback = update_callback

        self.pack(fill='x', pady=5, padx=10, ipady=5)


        self.columnconfigure(0, weight=4) # Red Team Name
        self.columnconfigure(1, weight=1) # Red Score
        self.columnconfigure(2, weight=2) # Role Label
        self.columnconfigure(3, weight=1) # Blue Score
        self.columnconfigure(4, weight=4) # Blue Team Name


        self.red_var = tk.StringVar()
        self.red_combo = ttk.Combobox(self, textvariable=self.red_var, state="readonly", font=("Malgun Gothic", 10))
        self.red_combo.grid(row=0, column=0, padx=5, sticky='ew')
        self.red_combo.bind("<<ComboboxSelected>>", self.on_select)

        self.red_score_lbl = tk.Label(self, text="-", bg=COLORS['panel'], fg=COLORS['red_team'], font=("Malgun Gothic", 12, "bold"))
        self.red_score_lbl.grid(row=0, column=1)

        role_lbl = tk.Label(self, text=self.role_name_kr, bg=COLORS['panel'], fg=COLORS['fg'], font=("Malgun Gothic", 11, "bold"), width=8)
        role_lbl.grid(row=0, column=2)


        self.blue_score_lbl = tk.Label(self, text="-", bg=COLORS['panel'], fg=COLORS['accent'], font=("Malgun Gothic", 12, "bold"))
        self.blue_score_lbl.grid(row=0, column=3)

        self.blue_var = tk.StringVar()
        self.blue_combo = ttk.Combobox(self, textvariable=self.blue_var, state="readonly", font=("Malgun Gothic", 10))
        self.blue_combo.grid(row=0, column=4, padx=5, sticky='ew')
        self.blue_combo.bind("<<ComboboxSelected>>", self.on_select)

    def refresh_options(self, available_players):
        # 현재 선택된 값 유지하면서 리스트 업데이트
        current_red = self.red_var.get()
        current_blue = self.blue_var.get()
        
        options = list(self.players_dict.keys())
        self.red_combo['values'] = [""] + options
        self.blue_combo['values'] = [""] + options

    def on_select(self, event=None):
        self.update_ui()
        self.update_callback() # 메인 앱에 변경 알림 (중복 체크)

    def update_ui(self):
        # Red Score
        r_name = self.red_var.get()
        r_score = 0
        if r_name and r_name in self.players_dict:
            r_score = self.players_dict[r_name].scores[self.role_key]
            self.red_score_lbl.config(text=str(r_score))
        else:
            self.red_score_lbl.config(text="-")

        # Blue Score
        b_name = self.blue_var.get()
        b_score = 0
        if b_name and b_name in self.players_dict:
            b_score = self.players_dict[b_name].scores[self.role_key]
            self.blue_score_lbl.config(text=str(b_score))
        else:
            self.blue_score_lbl.config(text="-")

        if r_name and b_name:
            diff = abs(r_score - b_score)
            if diff >= 4:
                self.config(bg=COLORS['warning_high']) # 진한 빨강
                self.change_children_bg(COLORS['warning_high'])
            elif diff >= 2:
                self.config(bg=COLORS['warning_low']) # 연한 빨강/분홍
                self.change_children_bg(COLORS['warning_low'])
            else:
                self.config(bg=COLORS['panel'])
                self.change_children_bg(COLORS['panel'])
        else:
            self.config(bg=COLORS['panel'])
            self.change_children_bg(COLORS['panel'])

    def change_children_bg(self, color):
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=color)

class TeamBuilderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LoL Team Balance Builder")
        self.geometry("1000x700")
        self.configure(bg=COLORS['bg'])

        self.participants = {} 
        self.lanes = []

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        header_frame = tk.Frame(self, bg=COLORS['bg'])
        header_frame.pack(fill='x', pady=20)
        
        tk.Label(header_frame, text="Ballancer", font=("Malgun Gothic", 20, "bold"), bg=COLORS['bg'], fg=COLORS['fg']).pack()

        content_frame = tk.Frame(self, bg=COLORS['bg'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)

        left_panel = tk.Frame(content_frame, bg=COLORS['panel'], width=250)
        left_panel.pack(side='left', fill='y', padx=(0, 20))
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text="참가자 목록", font=("Malgun Gothic", 12, "bold"), bg=COLORS['panel'], fg=COLORS['fg']).pack(pady=10)

        self.listbox = tk.Listbox(left_panel, bg=COLORS['input_bg'], fg=COLORS['fg'], font=("Malgun Gothic", 10), bd=0, highlightthickness=0)
        self.listbox.pack(fill='both', expand=True, padx=10, pady=5)

        add_btn = tk.Button(left_panel, text="+ 참가자 추가", command=self.open_add_dialog,
                            bg=COLORS['btn_bg'], fg=COLORS['btn_fg'], relief='flat', font=("Malgun Gothic", 11))
        add_btn.pack(fill='x', padx=10, pady=10)
        
        del_btn = tk.Button(left_panel, text="- 선택 삭제", command=self.delete_player,
                            bg='#4C566A', fg=COLORS['fg'], relief='flat', font=("Malgun Gothic", 10))
        del_btn.pack(fill='x', padx=10, pady=(0, 10))


        right_panel = tk.Frame(content_frame, bg=COLORS['bg'])
        right_panel.pack(side='right', fill='both', expand=True)

        header_grid = tk.Frame(right_panel, bg=COLORS['bg'])
        header_grid.pack(fill='x', pady=(0, 10))
        header_grid.columnconfigure(0, weight=1)
        header_grid.columnconfigure(1, weight=1)

        tk.Label(header_grid, text="RED TEAM", font=("Malgun Gothic", 14, "bold"), bg=COLORS['bg'], fg=COLORS['red_team']).grid(row=0, column=0)
        tk.Label(header_grid, text="BLUE TEAM", font=("Malgun Gothic", 14, "bold"), bg=COLORS['bg'], fg=COLORS['accent']).grid(row=0, column=1)

        self.lanes_frame = tk.Frame(right_panel, bg=COLORS['bg'])
        self.lanes_frame.pack(fill='both', expand=True)

        for i, role in enumerate(ROLES):
            lane = LaneRow(self.lanes_frame, i, role, self.participants, self.check_duplicates)
            self.lanes.append(lane)

    def open_add_dialog(self):
        AddPlayerDialog(self, self.add_player)

    def add_player(self, player):
        if player.name in self.participants:
            messagebox.showerror("오류", "이미 존재하는 이름입니다.")
            return
        self.participants[player.name] = player
        self.update_listbox()
        self.refresh_combos()
        self.save_data()

    def delete_player(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        name = self.listbox.get(selection[0])
        if messagebox.askyesno("삭제 확인", f"'{name}' 참가자를 삭제하시겠습니까?"):
            del self.participants[name]
            self.update_listbox()
            self.refresh_combos()
            self.save_data()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for name in sorted(self.participants.keys()):
            self.listbox.insert(tk.END, name)

    def refresh_combos(self):
        for lane in self.lanes:
            lane.refresh_options(self.participants)

    def check_duplicates(self):
        selected = []
        for lane in self.lanes:
            r = lane.red_var.get()
            b = lane.blue_var.get()
            if r: selected.append(r)
            if b: selected.append(b)
  
        if len(selected) != len(set(selected)):
             messagebox.showwarning("중복 선택", "한 참가자가 여러 포지션에 선택되었습니다!", parent=self)

    # 데이터 저장하는 부분
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
                self.update_listbox()
                self.refresh_combos()
            except Exception as e:
                print(f"Load failed: {e}")

if __name__ == "__main__":
    app = TeamBuilderApp()
    app.mainloop()