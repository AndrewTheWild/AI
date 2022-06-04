import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword): 
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment): 
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment): 
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename): 
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)
 
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self): 
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self): 
        for var in self.domains:
            for word in self.domains[var].copy():
                if var.length != len(word):
                    self.domains[var].remove(word)
        return

    def revise(self, x, y): 
        i, j = self.crossword.overlaps[x, y]
        is_revised = False
        for word1 in self.domains[x].copy():
            found_match = False
            for word2 in self.domains[y]:
                if word1[i] == word2[j] and word1 != word2:
                    found_match = True
                    break
            if found_match == False:
                self.domains[x].remove(word1)
                is_revised = True
        return

    def ac3(self, arcs=None): 
        if arcs == None:
            arcs = []
            for v1, v2 in self.crossword.overlaps:
                if self.crossword.overlaps[v1, v2] is not None:
                    arcs.append((v1, v2))
            return arcs

        for v1, v2 in arcs:
            is_v1_revised = self.revise(v1, v2)
            if is_v1_revised == True and len(self.domains[v1]) == 0:
                return False
        return True

    def assignment_complete(self, assignment): 
        if len(assignment) == len(self.crossword.variables):
            return True
        return False

    def consistent(self, assignment): 
        if len(assignment) != len(set(assignment.values())):
            return False
        for var in assignment:
            if var.length != len(assignment[var]):
                return False
        for var in assignment:
            word1 = assignment[var]
            neighbors = self.crossword.neighbors(var)
            for var2 in neighbors:
                if var2 in assignment:
                    word2 = assignment[var2]
                    i, j = self.crossword.overlaps[var, var2]
                    if word1[i] != word2[j] or word1 == word2:
                        return False
        return True

    def order_domain_values(self, var, assignment): 
        res_dict = {}
        for word1 in self.domains[var]:
            eliminates = 0
            for var2 in self.crossword.variables:
                if var2 != var:
                    index = self.crossword.overlaps[var, var2]
                    if var2 not in assignment and index != None:
                        for word2 in self.domains[var2]:
                            if word1[index[0]] != word2[index[1]]:
                                eliminates += 1
            res_dict[word1] = eliminates
        return sorted(res_dict, key=res_dict.get)

    def select_unassigned_variable(self, assignment): 
        best_options_set1 = set() 
        lowest_remaining_options = len(self.crossword.words)
        for var in self.crossword.variables:
            if var not in assignment:
                if len(self.domains[var]) < lowest_remaining_options:
                    best_options_set1 = {var}
                    lowest_remaining_options = len(self.domains[var])
                elif len(self.domains[var]) == lowest_remaining_options:
                    best_options_set1.add(var)
        if len(best_options_set1) == 1:
            return best_options_set1.pop()

        most_neighbors = 0
        best_options_set2 = set()
        for var in best_options_set1:
            neighbors = len(self.crossword.neighbors(var))
            if neighbors > most_neighbors:
                best_options_set2 = {var}
                most_neighbors = neighbors
            elif neighbors == most_neighbors:
                best_options_set2.add(var)

        return best_options_set2.pop()

    def backtrack(self, assignment): 
        if self.assignment_complete(assignment):
            return assignment
 
        var = self.select_unassigned_variable(assignment) 
        domain = self.order_domain_values(var, assignment)
        outcome = None
        for word in domain:
            assignment[var] = word
            if self.consistent(assignment):
                outcome = self.backtrack(assignment)

            if outcome is not None:
                break   

        return outcome


def main():
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")
 
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

 
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

 
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
