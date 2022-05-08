from email.policy import default
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
    """
    Notes:

    Code assumes blocks are defined in squares
    """
    actions = {
        cs.KEY_UP: UP,
        cs.KEY_DOWN: DOWN,
        cs.KEY_LEFT: LEFT,
        cs.KEY_RIGHT: RIGHT,
        32: SPACE
    }

    def __init__(self, width, height):
        self.width = width
        self.height = height
        # The static items on the board, source of truth
        self.cells: list[list[int]] = [ [False] * width for _ in range(height)]
        # copy self.cells but add the current block
        self.drawing_board: list[list[int]] = [ [False] * width for _ in range(height)]
        self.upcoming_blocks: list[list[list[int]]] = [Block.random().value for _ in range(3)]
        self.new_move = True
        self.block_coord: list[int] = None # location, start top left, right then down, 0 indexed
        self.current_block: list[list[int]] = None

    def print_board(self):
        for row in self.cells:
            print(row)

    def iterate(self, action: str = None):
        #
        if (self.current_block
            and not self.new_move 
            and not self.check_block([self.block_coord[0],self.block_coord[1]+1], self.current_block)):
                self.new_move = True
        if self.new_move:
            self.current_block = self.upcoming_blocks.pop(0)
            self.upcoming_blocks.append(Block.random().value)
            self.block_coord = [int((self.width/2) - 2), 0]
            self.new_move = False
            self.draw_block()

        elif action == UP:
            # TODO: check shape against position
            test_block = Block.rotate(self.current_block)
            if self.check_block(self.block_coord, test_block):
                self.current_block = test_block
                self.draw_block()
            else: 
                x = self.block_coord[0]
                y = self.block_coord[1] - 1
                if y < 0:
                    return False
                if self.check_block((x, y), test_block):
                    self.block_coord
                self.current_block = test_block
                self.draw_block()
                
        elif action == LEFT:
            if self.block_coord[0] > 0:
                self.block_coord[0] -= 1
                self.draw_block()

        elif action == RIGHT:
            if self.block_coord[0] + len(self.current_block) < self.width:
                self.block_coord[0] += 1
                self.draw_block()

        elif action == SPACE:
            pass

        elif action in [DOWN, None]:
            self.block_coord[1] += 1        
            self.draw_block()
        else:
            return False

        return True

    def check_block(self, corner_xy, block):
        for row_idx, row in enumerate(block):
            for item_idx, item in enumerate(row):
                row_num = corner_xy[1] + row_idx
                col_num = corner_xy[0] + item_idx
                # bottom check
                if item and row_num >= self.height:
                    print("height restriction")
                    return False
                # left check
                # right check
                # overlap check
                if item and self.cells[row_num][col_num]:
                    print("overlap restriction")
                    return False
        return True

    def draw_block(self):
        for row_idx, row in enumerate(self.current_block):
            for item_idx, item in enumerate(row):
                if item:
                    row_num = self.block_coord[1] + row_idx
                    col_num = self.block_coord[0] + item_idx
                    self.cells[row_num][col_num] = item
        return True

    def clear_block(self, corner_xy, block):
        """
        
        """
        for row_idx, row in enumerate(block):
            for item_idx, item in enumerate(row):
                if item:
                    row_num = corner_xy[1] + row_idx
                    col_num = corner_xy[0] + item_idx
                    self.cells[row_num][col_num] = 0
        
class Game:

    default_wait_time = 0.8

    def __init__(self):
        self.terminating = False
        self.board = Board(10, 20)
        self.spinning_wait_time = Game.default_wait_time
        self.is_spinning = False
        self.times_spun = 0
        self.timer = None
        self.stdscr: cs._CursesWindow = None
        self.key = None

    @staticmethod
    def run(stdscr: "cs._CursesWindow", instance: "Game"):
        instance.stdscr = stdscr
        instance.setup()
        instance.loop()
        try:
            while not instance.terminating:
                instance.key = instance.stdscr.getch()
                if instance.key in Board.actions:
                    action = Board.actions[instance.key]
                    # if rotation, prevent spinning foreverd
                    if action is not UP:
                        # call loop manually to reset the wait time
                        if instance.times_spun >= 20:
                            instance.is_spinning = False
                            action = None
                        else:
                            instance.is_spinning = True
                            instance.spinning_wait_time *= 0.95
                            instance.times_spun +=1
                    instance.loop(instance.spinning_wait_time, action)
                elif instance.key == 3:
                    instance.terminating = True
        except KeyboardInterrupt:
            pass
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
        self.stdscr.clear()
        # self.stdscr.nodelay(True)

    def loop(self, wait_time = None, action = None):
        # TODO: make game go faster as time goes on
        if not self.terminating and self.board.iterate(action):
            if self.timer: self.timer.cancel()
            if wait_time is None:
                wait_time = Game.default_wait_time
            self.timer = Timer(wait_time, self.loop)
            self.timer.start()
            self.times_spun += 1
            self.draw()
            self.stdscr.refresh()
            if not self.is_spinning:
                self.spinning_wait_time = self.default_wait_time
                self.times_spun = 0

    def draw(self):
        for row_idx, row in enumerate(self.board.cells):
            for col_idx, col in enumerate(row):
                char_attr = self.stdscr.inch(row_idx, col_idx*2)
                # if cs.pair_number(char_attr & 0b1111111100000000) != 0:
                test = cs.pair_number((char_attr & cs.A_COLOR))

                # block_boundary_x = self.board.block_coord[0] + len(self.board.current_block)
                # block_boundary_y = self.board.block_coord[1] + len(self.board.current_block)
                # if (row_idx >= self.board.block_coord[1]
                #     and row_idx < block_boundary_y
                #     and col_idx >= self.board.block_coord[0]
                #     and col_idx < block_boundary_x
                #     and col):
                #     self.stdscr.addstr(row_idx, col_idx*2, "·", cs.color_pair(col))
                #     self.stdscr.addstr(row_idx, col_idx*2 + 1, "·", cs.color_pair(col))        
                # else:
                self.stdscr.addstr(row_idx, col_idx*2, "·", cs.color_pair(col))
                # self.stdscr.addstr(row_idx, col_idx*2, str(test), cs.color_pair(col))
                self.stdscr.addstr(row_idx, col_idx*2 + 1, "·", cs.color_pair(col))

    def teardown(self):
        self.timer.cancel()

if __name__ == "__main__":
    game = Game()
    # cs.noecho() # Don't write the character typed
    # cs.cbreak() # non-buffered input, react to input immediately
    # self.stdscr.keypad(True) # have arrow keys return curses values i.e. curses.KEY_cs.KEY_LEFT
    cs.wrapper(Game.run, game)