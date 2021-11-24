from enum import Enum
import random
from threading import Timer
import curses as cs

UP = "UP"
DOWN = "DOWN"
LEFT = "LEFT"
RIGHT = "RIGHT"
SPACE = "SPACE"

class Block(Enum):
    L = [
        [0, 3, 0],
        [0, 3, 0],
        [0, 3, 3]]
    J = [
        [0, 2, 0],
        [0, 2, 0],
        [2, 2, 0]]
    I = [
        [0, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 0, 0]]
    O = [
        [4, 4],
        [4, 4]]
    T = [
        [0, 6, 0],
        [6, 6, 6],
        [0, 0, 0]]
    S = [
        [0, 5, 5],
        [5, 5, 0],
        [0, 0, 0]]
    Z = [
        [7, 7, 0],
        [0, 7, 7],
        [0, 0, 0]]

    def random():
        return random.choice(list(Block))

    def rotate(block: "list[list[int]]", counter_clockwise: bool = False):
        return list(zip(*block))[::-1] if counter_clockwise else list(zip(*block[::-1]))


class Board:

    actions = {
        450: UP,
        452: LEFT,
        454: RIGHT,
        456: DOWN
    }

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells: list[list[int]] = [ [False] * width for _ in range(height)]
        self.upcoming_blocks: list[list[list[int]]] = [Block.random().value for i in range(3)]
        self.new_move = True
        self.current_block_location: list[int] = None # location, start top left, right then down, 0 indexed
        self.current_block: list[tuple[bool]] = None

    def print_board(self):
        for row in self.cells:
            print(row)

    def iterate(self, stdscr, action: str = None):
        if self.new_move:
            self.current_block = self.upcoming_blocks.pop(0)
            self.upcoming_blocks.append(Block.random().value)
            self.current_block_location = [3, 0]
            self.new_move = False
            return True

        elif action == UP:
            # TODO: check shape against position
            test_block = Block.rotate(self.current_block)
            if self.check_block(self.current_block_location, test_block):
                self.clear_block(self.current_block_location, self.current_block)
                self.current_block = test_block
                self.draw_block()
            else: 
                x = self.current_block_location[0]
                y = self.current_block_location[1] - 1
                if y < 0:
                    return False
                if self.check_block((x, y), test_block):
                    self.current_block_location
                self.clear_block(self.current_block_location, self.current_block)
                self.current_block = test_block
                self.draw_block()
                
        elif action == LEFT:
            if self.current_block_location[0] > 0:
                self.clear_block(self.current_block_location, self.current_block)
                self.current_block_location[0] -= 1
                self.draw_block()

        elif action == RIGHT:
            if self.current_block_location[0] + len(self.current_block) < self.width:
                self.clear_block(self.current_block_location, self.current_block)
                self.current_block_location[0] += 1
                self.draw_block()

        elif action == SPACE:
            pass
        elif action == DOWN:
            # TODO: go down faster
            pass
        else: # push down
            self.clear_block(self.current_block_location, self.current_block)
            self.current_block_location[1] += 1        
            retval = self.draw_block()
            if not retval:
                self.new_move = True 
            return retval

    def check_block(self, corner_xy, block):
        for row_idx, row in enumerate(block):
            for item_idx, item in enumerate(row):
                row_num = corner_xy[1] + row_idx
                col_num = corner_xy[0] + item_idx
                # bottom check
                if row_num == self.height:
                    return False
                # left check
                # right check
                # overlap check
                if self.cells[row_num][col_num] and item:
                    return False

    def draw_block(self):
        for row_idx, row in enumerate(self.current_block):
            for item_idx, item in enumerate(row):
                row_num = self.current_block_location[1] + row_idx
                col_num = self.current_block_location[0] + item_idx
                self.cells[row_num][col_num] = item

        return True

    def clear_block(self, corner_xy, block):
        for row_idx, row in enumerate(block):
            for item_idx in range(len(row)):
                row_num = corner_xy[1] + row_idx
                col_num = corner_xy[0] + item_idx
                self.cells[row_num][col_num] = 0
        
class Game:
    def __init__(self):
        self.terminating = False
        self.board = Board(10, 20)
        self.wait_time = 0.8
        self.timer = None
        self.iterations = 0
        self.stdscr: cs._CursesWindow = None
        self.key = None

    @staticmethod
    def run(stdscr, instance: "Game"):
        instance.stdscr = stdscr
        instance.setup()
        instance.loop()
        while not instance.terminating:
            instance.key = instance.stdscr.getch()
            if instance.key in Board.actions:
                instance.board.iterate(instance.stdscr, Board.actions[instance.key])
                instance.draw()
            if instance.key == 3:
                instance.terminating = True
        instance.teardown()
        
    def setup(self):
        cs.start_color()
        cs.init_pair(1, cs.COLOR_BLACK, cs.COLOR_CYAN)
        cs.init_pair(2, cs.COLOR_BLACK, cs.COLOR_BLUE)
        cs.init_pair(3, cs.COLOR_BLACK, cs.COLOR_WHITE)
        cs.init_pair(4, cs.COLOR_BLACK, cs.COLOR_YELLOW)
        cs.init_pair(5, cs.COLOR_BLACK, cs.COLOR_GREEN)
        cs.init_pair(6, cs.COLOR_BLACK, cs.COLOR_MAGENTA)
        cs.init_pair(7, cs.COLOR_BLACK, cs.COLOR_RED)
        cs.curs_set(0)
        self.stdscr.keypad(True)
        self.stdscr.clear()
        self.stdscr.nodelay(True)

    def loop(self):
        # TODO: make game go faster as time goes one
        # TODO: add keyboard interrupt to allow for player movement
        if self.board.iterate(self.stdscr):
            self.timer = Timer(self.wait_time, self.loop)
            self.timer.start()
            self.iterations += 1
            self.draw()
            self.stdscr.refresh()
        else:
            self.terminating = True

    def draw(self):
        for row_idx, row in enumerate(self.board.cells):
            for col_idx, col in enumerate(row):
                self.stdscr.addstr(row_idx, col_idx*2, "·", cs.color_pair(col))
                self.stdscr.addstr(row_idx, col_idx*2 + 1, "·", cs.color_pair(col))
    
    def teardown(self):
        self.timer.cancel()


if __name__ == "__main__":
    game = Game()
    # cs.noecho() # Don't write the character typed
    # cs.cbreak() # non-buffered input, react to input immediately
    # self.stdscr.keypad(True) # have arrow keys return curses values i.e. curses.KEY_LEFT
    cs.wrapper(Game.run, game)
    # Game.run(None, game)
    #print("exited")