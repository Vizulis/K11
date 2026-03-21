from random import randint
from time import time

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


def human_move(tree, node):
    children = tree.get_children(node, 1)

    if not children:
        return None

    legal_moves = sorted(set(move for move, child in children))
    print("Legal moves:", legal_moves)

    while True:
        try:
            move = int(input("Enter your move: "))
            if move in legal_moves:
                for child_move, child in children:
                    if child_move == move:
                        return move, child
            else:
                print("Invalid move.")
        except ValueError:
            print("Invalid move.")


def get_sequence():
    while True:
        try:
            length = int(input("Enter sequence length (15-50): "))
            if 15 <= length <= 50:
                sequence = [randint(1, 5) for _ in range(length)]
                print("Generated sequence:", sequence)
                return sequence
            print("Invalid input.")
        except ValueError:
            print("Invalid input.")


def get_first_player():
    while True:
        try:
            first_player = int(input("Who starts first? 1 for Player, 2 for Computer: "))
            if first_player in [1, 2]:
                return first_player
            print("Invalid input.")
        except ValueError:
            print("Invalid input.")


def get_game_mode():
    while True:
        try:
            mode = int(input("Choose mode: 1 for Computer vs Computer, 2 for Computer vs Human: "))
            if mode in [1, 2]:
                return mode
            print("Invalid input.")
        except ValueError:
            print("Invalid input.")


def get_algorithm():
    while True:
        algorithm = input("Which algorithm should the computer use? Choices: [minimax, alpha-beta]: ")
        if algorithm in ["minimax", "alpha-beta"]:
            return algorithm
        print("Invalid input.")

def play_game(tree, mode, node, current_player, max_depth, algorithm):
    """
    Izspēlē partiju līdz beigām.
    """
    global NODE_COUNT
    match mode:
        case 1:  # Computer vs Computer
            current_player = 1 # mode = 1, current_player tiek iestatīts kā parasti, vai nu 1 vai nu 2

            memo = {} # atmiņa priekš jau aprēķinātām heiristiskām vērtībām virsotnēm, lai tās netiktu pārrēķinātas vairākas reizes
            while node.sequence:
                NODE_COUNT = 0
                start = time()
                result = best_move(tree, node, current_player, max_depth, algorithm, memo)
                if result is None:
                    break

                move, node = result

                print(f"AI {current_player} made a move: removed {move}, the AI generated {NODE_COUNT} nodes, move took {time() - start} seconds")
                print(f"New sequence: {node}")
                print("-------------------------------------------------------")

                current_player = 2 if current_player == 1 else 1

        case 2:  # Computer vs Human
            turn = "human" if current_player else "ai" # current_player tiek lietots kā boolean, lai noteiktu gājienu secību
            player_mapping = {"human": 1, "ai": 2} if current_player else {"ai": 1, "human": 2}

            memo = {} # atmiņa priekš jau aprēķinātām heiristiskām vērtībām virsotnēm, lai tās netiktu pārrēķinātas vairākas reizes
            while node.sequence:
                player = player_mapping[turn] # tiek izmantots player_mapping, lai noteiktu pareizo spēlētāju, kurš veic gājienu

                if turn == "human":
                    result = human_move(tree, node)
                    if result is None:
                        break
                    move, node = result
                    print(f"Human made a move: removed {move}")
                    print(node)
                    print("-------------------------------------------------------")
                    turn = "ai"

                else:
                    NODE_COUNT = 0
                    start = time()
                    result = best_move(tree, node, player, max_depth, algorithm, memo)
                    if result is None:
                        break
                    move, node = result
                    print(f"AI made a move: removed {move}, the AI generated {NODE_COUNT} nodes, move took {time() - start} seconds")
                    print(node)
                    print("-------------------------------------------------------")
                    turn = "human"
                
    print("\nGame over")
    print("P1 score:", node.p1)
    print("P2 score:", node.p2)

    if node.p1 > node.p2:
        print("Player 1 wins")
    elif node.p2 > node.p1:
        print("Player 2 wins")
    else:
        print("Draw")


def main():
    play = "Y"
    while play == "Y":
        MAX_SEARCH_DEPTH = 10

        sequence = get_sequence()
        mode = get_game_mode()

        if mode == 2:
            first_player = get_first_player() == 1 # pašreiz first_player ir bool, pēc tam tiek iestatīts, atkarībā no mode
        else:
            first_player = False

        algorithm = get_algorithm()

        tree = GameTree()
        root = Node('A1', sequence, 150, 150, 1)
        tree.add_node(root)

        play_game(tree, mode, root, first_player, MAX_SEARCH_DEPTH, algorithm)

        play = input("Play again? Y/N: ")


if __name__ == "__main__":
    main()
