#include <iostream>
#include <deque>
#include <array>
#include <string>
#include <cstdlib>
#include <cstdint>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#endif

using Piece = char;

static constexpr Piece P_BLACK = 'o';
static constexpr Piece P_WHITE = 'x';
static constexpr Piece P_EMPTY = '.';
static constexpr Piece P_EXTRA = '#';

struct Pos {
    int32_t row;
    int32_t col;

    Pos() : row{ 0 }, col{ 0 } {}
    Pos(int32_t r, int32_t c) : row{ r }, col{ c } {}
};

class Board {
public:
    static constexpr int32_t width = 17;
    static constexpr int32_t line_begin = 1;
    static constexpr int32_t line_end = 15;

    static_assert(width < 29, "width should be less than 29");
    static_assert(line_begin == 1, "line_begin should always be 1");
    static_assert(line_end == width - 2, "line_end should always be equal to (width - 2)");

    Board() {
        for (auto& line : data) {
            line.fill(P_EXTRA);
        }

        for (int32_t r = line_begin; r <= line_end; ++r) {
            for (int32_t c = line_begin; c <= line_end; ++c) {
                data[r][c] = P_EMPTY;
            }
        }
    }

    Piece get(int32_t r, int32_t c) const noexcept {
        return data[r][c];
    }

    Piece get(Pos pos) const noexcept {
        return data[pos.row][pos.col];
    }

    void move(int32_t r, int32_t c, Piece p) noexcept {
        data[r][c] = p;
        history.emplace_back(r, c);
    }

    void move(Pos pos, Piece p) noexcept {
        move(pos.row, pos.col, p);
    }

    void undo() noexcept {
        if (!history.empty()) {
            Pos pos = history.back();
            data[pos.row][pos.col] = P_EMPTY;
            history.pop_back();
        }
    }
private:
    std::array<std::array<Piece, width>, width> data;
    std::deque<Pos> history;
};

class AI {
    Board& board;
    std::array<std::array<int32_t, Board::width>, Board::width> scoreTable;

    int32_t evaluate_score(int32_t blackNum, int32_t whiteNum) const noexcept {
        if (blackNum > 0 && whiteNum > 0) {
            return 0;
        }

        if (blackNum == 0 && whiteNum == 0) {
            return 7;
        }

        if (whiteNum > 0) {
            if (whiteNum == 1) {
                return 35;
            }
            else if (whiteNum == 2) {
                return 800;
            }
            else if (whiteNum == 3) {
                return 15000;
            }
            else if (whiteNum == 4) {
                return 80'0000;
            }
        }
        
        if (blackNum > 0) {
            if (blackNum == 1) {
                return 15;
            }
            else if (blackNum == 2) {
                return 400;
            }
            else if (blackNum == 3) {
                return 1800;
            }
            else if (blackNum == 4) {
                return 10'0000;
            }
        }

        return -1;
    }

    void reset_score_table() {
        for (auto& line : scoreTable) {
            line.fill(0);
        }
    }

    void scan(int32_t directionX, int32_t directionY) {
        for (int32_t r = Board::line_begin; r <= Board::line_end; ++r) {
            for (int32_t c = Board::line_begin; c <= Board::line_end; ++c) {
                int32_t blackNum = 0;
                int32_t whiteNum = 0;
                int32_t rr = r;
                int32_t cc = c;

                int counter = 0;
                while (counter != 5) {
                    Piece p = board.get(rr, cc);

                    if (p == P_EXTRA) {
                        break;
                    }
                    else if (p == P_BLACK) {
                        ++blackNum;
                    }
                    else if (p == P_WHITE) {
                        ++whiteNum;
                    }

                    rr += directionY;
                    cc += directionX;
                    ++counter;
                }

                if (counter != 5) {
                    continue;
                }
                else {
                    int32_t score = evaluate_score(blackNum, whiteNum);

                    counter = 0;
                    rr = r;
                    cc = c;

                    while (counter < 5) {
                        scoreTable[rr][cc] += score;

                        ++counter;
                        rr += directionY;
                        cc += directionX;
                    }
                }
            }
        }
    }
public:
    AI(Board& _bd) : board{ _bd } {
        reset_score_table();
    }

    Pos gen_best_move() noexcept {
        scan(-1, -1);
        scan(+1, +1);
        scan( 0, -1);
        scan( 0, +1);
        scan(+1, -1);
        scan(-1, +1);
        scan(+1,  0);
        scan(-1,  0);

        Pos bestPos;
        int32_t bestScore = -1;

        for (int32_t r = Board::line_begin; r <= Board::line_end; ++r) {
            for (int32_t c = Board::line_begin; c <= Board::line_end; ++c) {
                if (scoreTable[r][c] >= bestScore && board.get(r, c) == P_EMPTY) {
                    bestPos.row = r;
                    bestPos.col = c;
                    bestScore = scoreTable[r][c];
                }
            }
        }

        reset_score_table();
        return bestPos;
    }
};

class ColorPrinter {
public:
    enum color {
        black,
        red,
        green,
        yellow,
        blue,
        magenta,
        cyan,
        white,
        bold_black,
        bold_red,
        bold_green,
        bold_yellow,
        bold_blue,
        bold_magenta,
        bold_cyan,
        bold_white,
        reset
    };

    ColorPrinter() {
        #ifdef _WIN32
        CONSOLE_SCREEN_BUFFER_INFO csbiInfo;
        hOutHandle = GetStdHandle(STD_OUTPUT_HANDLE);
        GetConsoleScreenBufferInfo(hOutHandle, &csbiInfo);
        oldColorAttrs = csbiInfo.wAttributes;
        #endif
    }

    ~ColorPrinter() {
        reset_color();
    }

    template<typename T>
    ColorPrinter& operator<<(T&& printable) {
        if constexpr (std::is_same_v<T, color>) {
            if (printable == color::reset) {
                reset_color();
            }
            else {
                set_color(printable);
            }
        }
        else {
            std::cout << printable;
        }

        return *this;
    }
private:
    void set_color(color c) {
        #ifdef _WIN32
        SetConsoleTextAttribute(hOutHandle, get_windows_color_attr(c));
        #else
        switch(c) {
            case color::black:
                std::cout << "\033[30m"; break;
            case color::red:
                std::cout << "\033[31m"; break;
            case color::green:
                std::cout << "\033[32m"; break;
            case color::yellow:       
                std::cout << "\033[33m"; break;
            case color::blue:         
                std::cout << "\033[34m"; break;
            case color::magenta:      
                std::cout << "\033[35m"; break;
            case color::cyan:         
                std::cout << "\033[36m"; break;
            case color::white:        
                std::cout << "\033[37m"; break;
            case color::bold_black:    
                std::cout << "\033[1m\033[30m"; break;
            case color::bold_red:      
                std::cout << "\033[1m\033[31m"; break;
            case color::bold_green:    
                std::cout << "\033[1m\033[32m"; break;
            case color::bold_yellow:   
                std::cout << "\033[1m\033[33m"; break;
            case color::bold_blue:     
                std::cout << "\033[1m\033[34m"; break;
            case color::bold_magenta:  
                std::cout << "\033[1m\033[35m"; break;
            case color::bold_cyan:     
                std::cout << "\033[1m\033[36m"; break;
            case color::bold_white:  
            default:  
                std::cout << "\033[1m\033[37m"; break;
        }
        #endif
    }

    void reset_color() {
        #ifdef _WIN32
        SetConsoleTextAttribute(hOutHandle, oldColorAttrs);
        #else
        std::cout << "\033[0m";
        #endif
    }

#ifdef _WIN32
    WORD get_windows_color_attr(color c) {
        switch(c) {
            case color::black: 
                return 0;
            case color::blue: 
                return FOREGROUND_BLUE;
            case color::green: 
                return FOREGROUND_GREEN;
            case color::cyan: 
                return FOREGROUND_GREEN | FOREGROUND_BLUE;
            case color::red: 
                return FOREGROUND_RED;
            case color::magenta: 
                return FOREGROUND_RED | FOREGROUND_BLUE;
            case color::yellow: 
                return FOREGROUND_RED | FOREGROUND_GREEN;
            case color::white:
                return FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE;
            case color::bold_black: 
                return 0 | FOREGROUND_INTENSITY;
            case color::bold_blue: 
                return FOREGROUND_BLUE | FOREGROUND_INTENSITY;
            case color::bold_green: 
                return FOREGROUND_GREEN | FOREGROUND_INTENSITY;
            case color::bold_cyan: 
                return FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY;
            case color::bold_red: 
                return FOREGROUND_RED | FOREGROUND_INTENSITY;
            case color::bold_magenta: 
                return FOREGROUND_RED | FOREGROUND_BLUE | FOREGROUND_INTENSITY;
            case color::bold_yellow: 
                return FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_INTENSITY;
            case color::bold_white:
            default:
                return FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY;
        };
    }

    HANDLE hOutHandle;
    WORD oldColorAttrs;
#endif
};

class Game {
    Board board;
    AI ai;
    ColorPrinter cprinter;
    Piece userP;
    Piece elysiaP;

    void clear_screen() {
        #ifdef _WIN32
        system("cls");
        #else
        system("clear");
        #endif
    }

    void show_board_on_console() {
        clear_screen();
        int32_t number = Board::line_end - Board::line_begin + 1;
        int32_t counter = 0;

        cprinter << "   x";
        while (counter < number) {
            cprinter << "--";
            ++counter;
        }

        cprinter << "-x\n";
        
        counter = 0;
        for (int32_t r = Board::line_begin; r <= Board::line_end; ++r) {
            cprinter << " " << ColorPrinter::bold_yellow << static_cast<char>(counter + 'a') << ColorPrinter::reset << " | ";

            for (int32_t c = Board::line_begin; c <= Board::line_end; ++c) {
                Piece p = board.get(r, c);

                if (p == P_BLACK) {
                    cprinter << ColorPrinter::bold_blue << p << " " << ColorPrinter::reset;
                }
                else if (p == P_WHITE) {
                    cprinter << ColorPrinter::bold_red << p << " " << ColorPrinter::reset;
                }
                else {
                    cprinter << ColorPrinter::white << p << " " << ColorPrinter::reset;
                }
            }

            cprinter << "|\n";
            ++counter;
        }

        counter = 0;
        cprinter << "   x";
        while (counter < number) {
            cprinter << "--";
            ++counter;
        }

        cprinter << "-x\n";
        cprinter << "     ";
        
        counter = 0;
        cprinter << ColorPrinter::bold_green;
        while (counter < number) {
            cprinter << static_cast<char>(counter + 'a') << " ";
            ++counter;
        }

        cprinter << ColorPrinter::reset << "\n\n";
    }

    bool is_input_a_pos(const std::string& input) {
        if (input.size() < 2) {
            return false;
        }

        return (input[0] - 'a' < Board::width - 2) && 
                (input[1] - 'a' < Board::width - 2);
    }

    Pos input_to_pos(const std::string& input) {
        return Pos {
            input[1] - 'a' + Board::line_begin,
            input[0] - 'a' + Board::line_begin
        };
    }

    std::string desc_pos(Pos pos) {
        std::string desc;

        desc += pos.col - Board::line_begin + 'a';
        desc += pos.row - Board::line_begin + 'a';
        return desc;
    }

    int32_t scan(int32_t r, int32_t c, int32_t directionX, int32_t directionY, Piece p) {
        int32_t rr = r + directionY;
        int32_t cc = c + directionX;
        int32_t counter = 0;

        while (board.get(rr, cc) == p) {
            ++counter;
            rr += directionY;
            cc += directionX;
        }

        return counter;
    }

    bool is_win(Pos pos, Piece p) {
        int32_t val1 = 1 + scan(pos.row, pos.col, +1, +1, p) + scan(pos.row, pos.col, -1, -1, p);
        int32_t val2 = 1 + scan(pos.row, pos.col, +1,  0, p) + scan(pos.row, pos.col, -1,  0, p);
        int32_t val3 = 1 + scan(pos.row, pos.col,  0, +1, p) + scan(pos.row, pos.col,  0, -1, p);
        int32_t val4 = 1 + scan(pos.row, pos.col, +1, -1, p) + scan(pos.row, pos.col, -1, +1, p);

        return val1 >= 5 || val2 >= 5 || val3 >= 5 || val4 >= 5;
    }
public:
    Game() 
        : board{}, ai{ board }, cprinter{}, userP{ P_BLACK }, elysiaP{ P_WHITE } 
    {}

    void run() {
        std::string input;
        show_board_on_console();

        while (true) {
            cprinter << ColorPrinter::bold_cyan << "Your turn: " << ColorPrinter::reset;
            std::getline(std::cin, input);

            if (input == "exit" || input == "quit") {
                cprinter << "Bye.\n\n";
                return;
            }

            if (input == "undo") {
                board.undo();
                board.undo();
                show_board_on_console();
                continue;
            }

            if (!is_input_a_pos(input)) {
                cprinter << "invalid move\n\n";
                continue;
            }

            Pos pos = input_to_pos(input);
            if (board.get(pos) != P_EMPTY) {
                cprinter << "this place is not empty\n\n";
                continue;
            }

            board.move(pos, userP);
            show_board_on_console();

            if (is_win(pos, userP)) {
                cprinter << ColorPrinter::bold_blue << "Congradulations! You win!\n" << ColorPrinter::reset;
                return;
            }

            Pos elysiaPos = ai.gen_best_move();
            board.move(elysiaPos, elysiaP);
            show_board_on_console();
            cprinter << ColorPrinter::bold_magenta << "Elysia" << ColorPrinter::reset << " moves at " << desc_pos(elysiaPos) << "\n\n";

            if (is_win(elysiaPos, elysiaP)) {
                cprinter << ColorPrinter::bold_red << "Sorry, You lose!\n" << ColorPrinter::reset;
                return;
            }
        }
    }
};

int main() {
    Game game;
    game.run();
    return 0;
}
