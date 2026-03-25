import tkinter as tk
from tkinter import ttk
from random import randint
import time


# --- BACKEND LOĢIKA ---

NODE_COUNT = 0 # datora apskatīto virsotņu skaitītājs

class Node:
    """
    Klase, kas glabā spēles stāvokli konkrētā virsotnē.

    id [str]         Virsotnes unikālais identifikators
    sequence [list]  Pašreizējā skaitļu virkne
    p1 [int]         1. spēlētāja punkti
    p2 [int]         2. spēlētāja punkti
    depth [int]      Virsotnes dziļums/līmenis kokā
    """

    def __init__(self, id, sequence, p1, p2, depth):
        self.id = id
        self.sequence = sequence.copy()
        self.p1 = p1
        self.p2 = p2
        self.depth = depth

    def __str__(self):
        return (
            f"{self.id}, {self.sequence}\n"
            f"Player 1 score: {self.p1}\n"
            f"Player 2 score: {self.p2}"
        )

    __repr__ = __str__

    def key(self):
        """
        Unikāla atslēga stāvokļa identificēšanai.
        Depth netiek izmantots, jo svarīgs ir pats stāvoklis.
        """
        return (tuple(self.sequence), self.p1, self.p2)

    def heuristic_value(self):
        """
        Stabilā heiristiskā funkcija:
        jo lielāks p1 - p2, jo stāvoklis labāks Player 1.
        """
        return self.p1 - self.p2


class GameTree:
    """
    Klase, kas glabā visu spēles koku.

    node_set   - visu virsotņu saraksts
    edge_set   - loki formā: parent -> [(move, child), ...]
    node_count - virsotņu skaitītājs ID ģenerēšanai
    node_dict  - unikālu stāvokļu vārdnīca
    """

    def __init__(self):
        self.node_set = []
        self.edge_set = {}
        self.node_count = 2
        self.node_dict = {}

    def add_node(self, node, parent=None, move=None):
        key = node.key()

        if key not in self.node_dict:
            self.node_set.append(node)
            self.node_dict[key] = node

            if parent is not None:
                self.add_edge(parent, move, node)

            self.node_count += 1
            return node
        else:
            existing_node = self.node_dict[key]

            if parent is not None:
                self.add_edge(parent, move, existing_node)

            return existing_node

    def add_edge(self, parent, move, child):
        self.edge_set.setdefault(parent, []).append((move, child))

    def generate_children(self, node, player):
        """
        Izveido visus iespējamos bērnus dotajai virsotnei.
        Katrs bērns ir pāreja (move, child), nevis move glabāšana pašā virsotnē.
        """
        children = []

        for move in [1, 2, 3, 4, 5]:
            if move in node.sequence:
                new_sequence = node.sequence.copy()
                new_sequence.remove(move)

                if player == 1:
                    p1_new = node.p1 - move
                    p2_new = node.p2
                else:
                    p1_new = node.p1
                    p2_new = node.p2 - move

                new_node = Node(
                    f"A{self.node_count}",
                    new_sequence,
                    p1_new,
                    p2_new,
                    node.depth + 1
                )

                added_node = self.add_node(new_node, node, move)
                children.append((move, added_node))

        return children
    
    def get_children(self, node, player): # tiek izmantots priekš on-demand koka ģenerēšanas, kuru izsauc minimax un alpha-beta funkcijas
        if node not in self.edge_set:
            return self.generate_children(node, player)

        return self.edge_set.get(node, [])


def minimax(tree, node, depth, player, memo):
    global NODE_COUNT
    NODE_COUNT += 1
    key = (node.key(), depth, player)

    if key in memo:
        return memo[key]

    if depth == 0 or not node.sequence:
        value = node.heuristic_value()
        memo[key] = value
        return value
    
    children = tree.get_children(node, player)

    if not children:
        value = node.heuristic_value()
        memo[key] = value
        return value

    next_player = 2 if player == 1 else 1

    if player == 1:
        best = -float('inf')
        for _, child in children:
            val = minimax(tree, child, depth - 1, next_player, memo)
            best = max(best, val)
    else:
        best = float('inf')
        for _, child in children:
            val = minimax(tree, child, depth - 1, next_player, memo)
            best = min(best, val)

    memo[key] = best
    return best


def alpha_beta(tree, node, depth, player, memo, alpha=-float('inf'), beta=float('inf')):
    global NODE_COUNT
    NODE_COUNT += 1
    key = (node.key(), depth, player)

    if key in memo:
        return memo[key]

    if depth == 0 or not node.sequence:
        value = node.heuristic_value()
        memo[key] = value
        return value

    children = tree.get_children(node, player)

    if not children:
        value =  node.heuristic_value()
        memo[key] = value
        return value

    next_player = 2 if player == 1 else 1

    if player == 1:
        best = -float('inf')
        for _, child in children:
            val = alpha_beta(tree, child, depth - 1, next_player, memo, alpha, beta)
            best = max(best, val)
            alpha = max(alpha, best)

            if alpha >= beta:
                break
    else:
        best = float('inf')
        for _, child in children:
            val = alpha_beta(tree, child, depth - 1, next_player, memo, alpha, beta)
            best = min(best, val)
            beta = min(beta, best)

            if alpha >= beta:
                break
    
    memo[key] = best
    return best


def best_move(tree, node, player, depth, algorithm, memo):
    children = tree.get_children(node, player)
    children.sort(key=lambda x: x[0])

    best_child = None
    next_player = 2 if player == 1 else 1

    if player == 1:
        best_score = -float('inf')
        for move, child in children:
            if algorithm == "minimax":
                value = minimax(tree, child, depth, next_player, memo) # depth - 1 uz depth
            else:
                value = alpha_beta(tree, child, depth, next_player, memo) # depth - 1 uz depth

            if value > best_score:
                best_score = value
                best_child = (move, child)
    else:
        best_score = float('inf')
        for move, child in children:
            if algorithm == "minimax":
                value = minimax(tree, child, depth, next_player, memo) # depth - 1 uz depth
            else:
                value = alpha_beta(tree, child, depth, next_player, memo) # depth - 1 uz depth

            if value < best_score:
                best_score = value
                best_child = (move, child)

    return best_child

# --- GUI LOĢIKA ---

class GameApp: # jauna klase grafiskajam interfeisam
    def __init__(self, root): 
        self.root = root 
        self.root.title("Sequence game")
        self.root.attributes('-fullscreen', True) # Loga defaults ir fullscreen
        self.root.geometry("1200x600+60+50") 
        self.root.bind("<Escape>", lambda event: self.root.attributes("-fullscreen", False)) # escape poga fullscreen iziesanai
        
        # Šeit "aktivizē" spēles mainīgos
        self.tree = None 
        self.current_node = None 
        self.mode = 1 
        self.player_mapping = {} 
        self.turn = "" 
        self.algo = "alpha-beta" 
        self.max_depth = 10 
        self.game_running = False 
        self.total_ai_time = 0.0 # laika skaitīšanai
        self.games_count = 0 
        self.ai_wins_count = 0

        self.setup_ui() 

    def setup_ui(self): 
        ########  SĀKAS "START MENU" IZVEIDE 
    
        self.l_length = tk.Label(text="Enter sequence length (15-50)", width=80)
        self.l_mode_dropdown = tk.Label(text="Choose game mode:", width=80) 
        self.mode_options = [
            "AI vs AI",
            "AI vs Human (Human starts)",
            "AI vs Human (AI starts)"
        ]
        self.l_algo_dropdown = tk.Label(text="Choose Algorithm:")
        
        self.get_choice_length = tk.IntVar(value=15)
        self.e_choice_length = tk.Entry(textvariable=self.get_choice_length, width=40)
        self.e_choice_mode = ttk.Combobox(values=self.mode_options, state="readonly", width=40)
        self.e_choice_mode.current(1)

        algo_options = ["minimax", "alpha-beta"]
        self.e_choice_algorithm = ttk.Combobox(values=algo_options, state="readonly", width=40)
        self.e_choice_algorithm.current(1)

        self.b_start_game = tk.Button(text="Start", command=self.start_game)

        self.l_stats = tk.Label(text="Games played: 0 | AI wins: 0", font=("Helvetica", 10, "bold"))

        # Speles izvades logi
        self.l_player1_points = tk.Label(text="Player_1 points:") 
        self.l_player2_points = tk.Label(text="Player_2 points:") 
        self.l_player1_move = tk.Label(text="Player_1 removed:") 
        self.l_player2_move = tk.Label(text="Player_2 removed:") 
        self.l_virkne = tk.Message(text="", width=800) # Nomainiju uz tk.message jo tas wrapojas pats
        self.l_nodes_generated = tk.Label(text="") 

        # Pogas Cilveka gajieniem
        self.num_buttons = [] 
        self.b_one = tk.Button(text="1", width=5, command=lambda: self.human_move(1))
        self.b_two = tk.Button(text="2", width=5, command=lambda: self.human_move(2))
        self.b_three = tk.Button(text="3", width=5, command=lambda: self.human_move(3))
        self.b_four = tk.Button(text="4", width=5, command=lambda: self.human_move(4))
        self.b_five = tk.Button(text="5", width=5, command=lambda: self.human_move(5))
        self.num_buttons = [self.b_one, self.b_two, self.b_three, self.b_four, self.b_five] 

        #teksta lauki visai informacijai
        self.l_length.grid(row=1, column=6, pady=5)
        self.e_choice_length.grid(row=2, column=6, pady=5)
        self.l_mode_dropdown.grid(row=3, column=6, pady=5)
        self.e_choice_mode.grid(row=4, column=6, pady=5)
        self.l_algo_dropdown.grid(row=5, column=6, pady=5)
        self.e_choice_algorithm.grid(row=6, column=6, pady=5)
        self.b_start_game.grid(row=7, column=7, pady=20)
        
        self.l_stats.grid(row=7, column=6, pady=20)

        self.l_player1_points.grid(row=8, column=1, pady=20)
        self.l_player2_points.grid(row=8, column=7, pady=20)
        self.l_player1_move.grid(row=9, column=1, pady=20)
        self.l_player2_move.grid(row=9, column=7, pady=20)
        self.b_one.grid(row=10, column=1, padx=10, pady=10)
        self.b_two.grid(row=10, column=2, padx=10, pady=10)
        self.b_three.grid(row=10, column=3, padx=10, pady=10)
        self.b_four.grid(row=10, column=4, padx=10, pady=10)
        self.b_five.grid(row=10, column=5, padx=10, pady=10)
        self.l_virkne.grid(row=12, column=6, pady=20)
        self.l_nodes_generated.grid(row=13, column=6, pady=20)
        
        self.toggle_buttons(False) 

    def toggle_buttons(self, state): 
        s = tk.NORMAL if state else tk.DISABLED # Šī palīgfunkcija  deaktivizē visas aktīvās pogas, lai ir vieglāk ar tam darboties
        for b in self.num_buttons: 
            b.config(state=s) 

    def start_game(self):
        self.games_count += 1
        self.l_stats.config(text=f"Games played: {self.games_count} | AI wins: {self.ai_wins_count}")

        sequence_length = self.get_choice_length.get()
        mode_text = self.e_choice_mode.get()
        self.algo = self.e_choice_algorithm.get()
        self.total_ai_time = 0.0 #spēles sākumā laiks ir 0

        # Loģika, lai pārvērstu dropdown tekstu atpakaļ skaitļos dzinējam
        if mode_text == "AI vs AI":
            self.mode = 1
            self.turn = "ai1"
        elif mode_text == "AI vs Human (Human starts)":
            self.mode = 2
            self.player_mapping = {"human": 1, "ai": 2}
            self.turn = "human"
        elif mode_text == "AI vs Human (AI starts)":
            self.mode = 2
            self.player_mapping = {"ai": 1, "human": 2}
            self.turn = "ai"

        # Spēles inicializācija 
        sequence = [randint(1, 5) for _ in range(sequence_length)] 
        self.tree = GameTree()  
        self.current_node = Node('A1', sequence, 150, 150, 1)  
        self.tree.add_node(self.current_node) 
        self.game_running = True  
        self.update_ui() 
        self.process_turn()
    # funkcija grafiskas vides atjauninašanai pec karta gajiena 
    def update_ui(self, last_move=None, mover=None): 
        self.l_virkne.config(text=f"Sequence: {self.current_node.sequence}") 
        self.l_player1_points.config(text=f"Player_1 points: {self.current_node.p1}") 
        self.l_player2_points.config(text=f"Player_2 points: {self.current_node.p2}") 
        if last_move: 
            if mover == 1: self.l_player1_move.config(text=f"Player_1 removed: {last_move}") 
            else: self.l_player2_move.config(text=f"Player_2 removed: {last_move}") 

    def process_turn(self): 
        if not self.current_node.sequence: 
            self.end_of_game() 
            return 

        if self.mode == 1: # AI vs AI
            self.root.after(600, self.ai_move) 
        elif self.mode == 2: # AI vs Human
            if self.turn == "ai": 
                self.root.after(600, self.ai_move) 
            else: 
                self.toggle_buttons(True) 

    def human_move(self, value): 
        if not self.game_running or self.turn != "human": return 
        if value not in self.current_node.sequence: return 

        player_idx = self.player_mapping["human"] 
        children = self.tree.get_children(self.current_node, player_idx) 
        # Atrod gājienu un nomaina spēles stāvokli
        for move, child in children: 
            if move == value: 
                self.current_node = child 
                self.update_ui(value, player_idx) 
                self.turn = "ai" 
                self.toggle_buttons(False) 
                self.process_turn() 
                break 

    def ai_move(self):
        global NODE_COUNT 
        if not self.game_running: return 
        
        NODE_COUNT = 0 
        player_idx = 1 if self.turn == "ai1" else (2 if self.turn == "ai2" else self.player_mapping["ai"]) 

        memo = {} 
# Aprēķina labāko gājienu un mēra patērēto laiku
        start_time = time.time()
        result = best_move(self.tree, self.current_node, player_idx, self.max_depth, self.algo, memo) 
        self.total_ai_time += (time.time() - start_time)
        # Ja gājiens atrasts, atjauno informāciju un turpina spēli
        if result: 
            move, node = result 
            self.current_node = node 
            self.l_nodes_generated.config(text=f"Generated Nodes: {NODE_COUNT}") 
            self.update_ui(move, player_idx) 
            
            if self.mode == 1: 
                self.turn = "ai2" if self.turn == "ai1" else "ai1" 
            else: 
                self.turn = "human" 
            self.process_turn() 
        else: 
            self.end_of_game() 
# Ja gājienu vairs nav, spēle beidzas
    def end_of_game(self): # Šī funkcija tiek izsaukta spēles beigās.
        self.game_running = False 
        end_window = tk.Toplevel()
        end_window.title("Game is over")
        end_window.geometry("600x600")

        p1_score = self.current_node.p1 
        p2_score = self.current_node.p2 
        winner_name = "Draw" 
        
        if p1_score > p2_score: 
            winner_name = "Player 1"
            if self.mode == 1: self.ai_wins_count += 1 # AI vs AI (viens no tiem ir AI)
            elif self.mode == 2 and self.player_mapping["ai"] == 1: self.ai_wins_count += 1
        elif p2_score > p1_score: 
            winner_name = "Player 2" 
            if self.mode == 1: self.ai_wins_count += 1
            elif self.mode == 2 and self.player_mapping["ai"] == 2: self.ai_wins_count += 1

        # Atjaunojam galveno statistikas rindu
        self.l_stats.config(text=f"Games played: {self.games_count} | AI wins: {self.ai_wins_count}")

        tk.Label(end_window, text=f"Player_1 score: {p1_score}", width=40).grid(row=1, column=1, pady=10)
        tk.Label(end_window, text=f"Player_2 score: {p2_score}", width=40).grid(row=2, column=1, pady=10)
        tk.Label(end_window, text=f"Winner: {winner_name}", width=40, font=("Helvetica", 12, "bold")).grid(row=3, column=1, pady=10)
        
        tk.Label(end_window, text=f"Algorithm used: {self.algo.upper()}", width=40).grid(row=4, column=1, pady=10)
        
        tk.Label(end_window, text=f"Total Algorithm Time: {self.total_ai_time:.4f} seconds", width=40).grid(row=5, column=1, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()
