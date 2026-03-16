from random import randint
from collections import deque

class Node:
    '''
    Klase, kas glabā informāciju par katru spēles koka virsotni

    id [str]        Katras virsotnes unikālais identifikators
    sequence [list]   Pašreizējā virkne dotajā virsotnē
    p1 [int]        Pirmā spēlētāja punkti dotajā virsotnē
    p2 [int]        Otrā spēlētāja punkti dotajā virsotnē
    depth [int]   Virsotnes līmenis spēles kokā
    move [int]   Gājiens, kas tika veikts, lai tiktu pie šīs virsotnes
    '''

    def __init__(self, id, sequence, p1, p2, depth, move):
        self.id = id
        self.sequence = sequence.copy()
        self.p1 = p1
        self.p2 = p2
        self.depth = depth
        self.move = move

    def __str__(self):
        # Pamainīju __str__, lai būtu labāk salasāms, kad tiek printēts
        string = f"{self.id}, {self.sequence} \n Player 1 score: {self.p1} \n Player 2 score: {self.p2}"
        return string
    
    __repr__ = __str__

    def key(self):
        # Noņēmu līmeni, jo tas nav svarīgs
        return (tuple(self.sequence), self.p1, self.p2)

    def heuristic_value(self, maximizing):
        # Jābūt izvēlei, kurš sāk pirmais(dators vai cilvēks),
        # tāpēc vērtība, kuru atgriezīs funckija ir atkarīga no tā, kurš sāka

        if maximizing:
            return self.p1 - self.p2
        else:
            return self.p2 - self.p1
    
                     
class GameTree:
    '''
    Klase, kas glabā visu spēles koku
    '''
    
    def __init__(self):
        self.node_set = []
        self.edge_set = {}
        self.node_count = 2
        self.node_dict = {}
    
    def add_node(self, node, parent = None):
        key = node.key()

        if key not in self.node_dict:
            self.node_set.append(node)
            self.node_dict[key] = node

            if parent is not None:
                self.add_edge(parent, node)

            self.node_count += 1
            return node
        else:
            existing_node = self.node_dict[key]

            if parent is not None:
                self.add_edge(parent, existing_node)

            return existing_node
    
    def add_edge(self, parent, child):
        self.edge_set.setdefault(parent, []).append(child)

    def generate_children(self, node, player):
        # gajiena_parbaude() ar citu nosaukumu
        children = []
        for move in [1, 2, 3]:
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
                    f'A{self.node_count}',
                    new_sequence,
                    p1_new,
                    p2_new,
                    node.depth + 1,
                    move
                )

                added_node = self.add_node(new_node, node)
                children.append(added_node)

        return children

def minimax(tree, node, maximizing, depth):
    # Pievienoju dziļumu(depth) pēc prakstiskā darba vajadzībām
    # Tas rekursīvi tiek samazināts līdz 0, tad beidz darbību
    children = tree.edge_set.get(node, [])
    
    if not children or depth == 0:
        return node.heuristic_value(maximizing)
    
    if maximizing:
        best = -float('inf')
        for child in children:
            best = max(best, minimax(tree, child, False, depth - 1))
    else:
        best = float('inf')
        for child in children:
            best = min(best, minimax(tree, child, True, depth - 1))

    return best
    
def alpha_beta(tree, node, maximizing, depth, alpha = -float('inf'), beta = float('inf')):
    # Gandrīz identisks minimax algoritmam, pie tā pievienoti ir alpha un beta parametri
    # alpha ir labākais, ko maksimizētājs var garantēt, beta ir labākais, ko minimizētājs var garantēt
    # Ja alpha jebkurā gadījumā ir lielāks par beta, tad veic nogriešanu(virsotni izlaiž, tādējādi netiek skatīti virsotnes bērni)
    children = tree.edge_set.get(node, [])

    if not children or depth == 0:
        return node.heuristic_value(maximizing)
    
    if maximizing:
        best = -float('inf')
        for child in children:
            value = alpha_beta(tree, child, False, depth - 1, alpha, beta)
            best = max(value, best)
            alpha = max(alpha, best)

            if beta <= alpha:
                break
    else:
        best = float('inf')
        for child in children:
            value = alpha_beta(tree, child, True, depth - 1, alpha, beta)
            best = min(value, best)
            beta = min(beta, best)

            if beta <= alpha:
                break

    return best

def best_move(tree, node, player, depth, algorithm):
    # Jauns arguments: algorithm
    # Tas norāda, vai izmanto minimax vai alpha-beta algoritmu
    best_score = -float('inf')
    best_child = None
    
    children = tree.edge_set.get(node, [])
    children.sort(key = lambda x: x.move)
    
    for child in children:
        if player == 1:
            if algorithm == "minimax":
                value = minimax(tree, child, False, depth - 1)
            else:
                value = alpha_beta(tree, child, False, depth - 1)
        else:
            if algorithm == "minimax":
                value = minimax(tree, child, True, depth - 1)
            else:
                value = alpha_beta(tree, child, True, depth - 1)
        
        if value > best_score:
            best_score = value
            best_child = child

    return best_child


def human_move(tree, node):
    if not node.sequence:
        return None

    legal_moves = sorted(set(node.sequence))
    print("Legal moves:", legal_moves)

    while True:
        try:
            move = int(input("Enter your move: "))
            if move in legal_moves:
                # Find the child node that corresponds to this move
                children = tree.edge_set.get(node, [])
                for child in children:
                    if child.move == move:
                        return child
                print("Move not available, try again.")
            else:
                print("Invalid move.")
        except ValueError:
            print("Invalid move.")


def get_sequence():
    # Ģenerē visu virkni funkcijā, nevis tikai iegūst tās garumu
    while True:
        try:
            length = int(input("Enter sequence length (15-25): "))
            if 15 <= length <= 25:
                sequence = [randint(1, 3) for _ in range(length)]
                print("Generated sequence: ", sequence)
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
    # Režīms starp Dators vs Dators un Cilvēks vs Dators
    while True:
        try:
            mode = int(input("Choose mode: 1 for Computer vs Computer, 2 for Computer vs Human: "))
            if mode in [1, 2]:
                return mode
        except ValueError:
            print("Invalid input")

def get_algorithm():
    # Praktiskā darba prasībās ir rakstīts, ka ir nepieciešams realizēt 2 algoritmus
    # Šeit lietotājs izvēlas, kuru izmantot priekš datora
    while True:
        algorithm = input("Which algorithm should the computer use? Choices: [minimax, alpha-beta]: ")
        if algorithm in ["minimax", "alpha-beta"]:
            return algorithm
       
        print("Invalid input")

def build_tree(tree, root, first_player):
    # Funkcija, kas izveido visu spēles koku, tika darīts main() funkcijā iepriekš
    # Ģenerēt daļu no koka(ar dziļumu n), kad tas bija nepieciešams minimax funkcijai ir šausmīgi neefektīvs
    queue = deque([root])
    processed = set()
    
    while queue:
        node = queue.popleft()
        
        if node.key() in processed:
            continue
            
        processed.add(node.key())
        
        if node.depth % 2 == 1:
            player = first_player
        else:
            player = 2 if first_player == 1 else 1

        
        children = tree.generate_children(node, player)
        
        for child in children:
            if child.sequence:
                queue.append(child)

def play_game(tree, mode, node, current_player, max_depth, algorithm):
    # Funkcija, kas izpilda spēles gaitu un izziņo rezultātu
    # case 1 ir Dators vs Dators, case 2 ir Cilvēks vs Dators
    match mode:
        case 1:
            while node and node.sequence:
                node = best_move(tree, node, current_player, max_depth, algorithm)
                if node is None:
                    break
                print(f"AI {current_player} made a move: removed {node.move} from the sequence")
                print(f"New sequence: {node}")
                print("-------------------------------------------------------")
                current_player = 2 if current_player == 1 else 1
        case 2:
            while node and node.sequence:
                if current_player == 1:
                    node = human_move(tree, node)
                    if node is None:
                        break
                    print(f"Human made a move: removed {node.move} from the sequence")
                    print(f"New sequence: {node}")
                    print("-------------------------------------------------------")
                    current_player = 2
                else:
                    node = best_move(tree, node, current_player, max_depth, algorithm)
                    if node is None:
                        break
                    print(f"AI made a move: removed {node.move} from the sequence")
                    print(f"New sequence: {node}")
                    print("-------------------------------------------------------")
                    current_player = 1

    print("\nGame over")
    if node is not None:
        print("P1 score: ", node.p1)
        print("P2 score: ", node.p2)

        if node.p1 > node.p2:
            print("Player 1 wins")
        elif node.p2 > node.p1:
            print("Player 2 wins")
        else:
            print("Draw")
    else:
        print("No winner: node is None.")

def main():
    # minimax/alpha-beta funkciju meklēšanas dziļums
    MAX_SEARCH_DEPTH = 10

    # Iegūst režīmu un virkni, pēc režīma nosaka pirmo spēlētāju(Dators vs Dators gadījumā tam nav starpības, tāpēc iestatīts kā 1)
    sequence = get_sequence()
    mode = get_game_mode()

    if mode == 2:
        first_player = get_first_player()
    else:
        first_player = 1

    algorithm = get_algorithm()

    # Izveido root virsotni un uzbūvē no tā visu pārējo koku
    tree = GameTree()
    root = Node('A1', sequence, 80, 80, 1, None)
    tree.add_node(root)

    build_tree(tree, root, first_player)
    play_game(tree, mode, root, first_player, MAX_SEARCH_DEPTH, algorithm)

if __name__ == "__main__":
    main()