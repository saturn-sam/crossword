import copy
import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }
        # print(self.crossword.variables)
    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
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
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
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
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # raise NotImplementedError
        # print(self.domains)
        copy_domain = copy.deepcopy(self.domains)
        for variable in copy_domain:
            var_length = variable.length
            for word in copy_domain[variable]:
                if len(word) != var_length:
                    self.domains[variable].remove(word)
        # print(self.domains)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        overlap= self.crossword.overlaps[x, y]
        revised= False
        copy_domains = copy.deepcopy(self.domains)
        if overlap:
            x_overlap, y_overlap= self.crossword.overlaps[x, y]
            for x_word in copy_domains[x]:
                matched_value = False
                for y_word in self.domains[y]:
                    if x_word[x_overlap] == y_word[y_overlap]:
                        matched_value = True
                        break
                if matched_value:
                    continue
                else:
                    self.domains[x].remove(x_word)
                    revised = True
        return revised
        



    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if not arcs:
            queue = []
            for v1 in self.domains:
                for v2 in self.crossword.neighbors(v1):
                    if self.crossword.overlaps[v1, v2]:
                        queue.append((v1, v2))
                        
        while len(queue) > 0:
            x, y = queue.pop(0)
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for neighbour in self.crossword.neighbors(x):
                    if neighbour != y:
                        queue.append((neighbour, x))
            return True
                        

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for variable in self.crossword.variables:
            if variable not in assignment.keys():
                return False
            if assignment[variable] not in self.crossword.words:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        for x_variable, x_word in assignment.items():
            if x_variable.length != len(x_word):
                return False

            for y_variable, y_word in assignment.items():
                if x_variable != y_variable:
                    if x_word == y_word:
                        return False

                    overlap_pos = self.crossword.overlaps[x_variable, y_variable]
                    if overlap_pos:
                        a, b = overlap_pos
                        if x_word[a] != y_word[b]:
                            return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        re_dict = {}

        var_neighbours = self.crossword.neighbors(var)

        for word in self.domains[var]:
            eliminated = 0
            for neighbour in var_neighbours:
                if neighbour in assignment:
                    continue
                else:
                    x_overlap, y_overlap = self.crossword.overlaps[var, neighbour]
                    for neighbour_word in self.domains[neighbour]:
                        if word[x_overlap] != neighbour_word[y_overlap]:
                            eliminated += 1
            re_dict[word] = eliminated

        sorted_dict = {k: v for k, v in sorted(re_dict.items(), key=lambda item: item[1])}

        return [*sorted_dict]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        selected_variables = []
        for variable in self.crossword.variables:
            if variable not in assignment:
                selected_variables.append([variable, len(self.domains[variable]), len(self.crossword.neighbors(variable))])
        print(selected_variables)
        if selected_variables:
            selected_variables.sort(key=lambda x: (x[1], -x[2]))
            return selected_variables[0][0]

        # If there are no potential variables, simply return None
        return None

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment): 
            return assignment
        variable = self.select_unassigned_variable(assignment)
        
        for var in self.order_domain_values(variable, assignment):
            assignment[variable] = var
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result:
                    return result
                assignment.pop(variable, None)

        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
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
