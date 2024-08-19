'''
Given an input text file of newline-separated words, this script
assists a user in guessing Fallout terminal hacking puzzle.
'''

import sys

# helpers
def compare_similarity(lhs : str, rhs : str) -> int:
    '''
    Given two strings, returns the number of overlapping letters between the two.
    '''
    assert len(lhs) == len(rhs), f"expecting equal string lengths for input: [{lhs} | {rhs}]"

    similarity = 0
    for i in range(len(lhs)):
        if lhs[i] == rhs[i]:
            similarity += 1
    return similarity

## main
def script(path: str) -> None:
    '''
    The main script function.
    '''

    guesses = []
    # read file lines into guesses
    # trim each guess in guesses
    with open(path, 'r', encoding='utf-8') as file:
        guesses = [guess.rstrip() for guess in file.readlines()]

    # validate input
    assert len(guesses) > 1, 'expect at least 2 guesses'
    for i in range(1, len(guesses)):
        assert len(guesses[i]) == len(guesses[i-1]), 'all guesses should be equal length'

    while len(guesses) > 0:
        prompt = 'next guess'
        print(f"{prompt}: {guesses[0]}")

        guess = guesses.pop(0)

        # read the result of the guess
        prompt = 'was the guess correct (y/n)?\n'
        result = input(prompt).lower()
        if result == 'y':
            print('SUCCESS!\nExiting...')
            sys.exit()
        elif result == 'n':
            # input
            prompt = 'guess hint (integer)?\n'
            hint = int(input(prompt))
            possibilities = []

            # compare remaining guesses with recent guess + hint
            for possibility in guesses:
                similarity = compare_similarity(guess, possibility)

                if similarity == hint:
                    possibilities.append(possibility)

            guesses = possibilities
        else:
            raise Exception("InvalidInput: {result}. Expect y/n")


if __name__ == '__main__':
    print('run hack helper...')
    ## input
    file_path = sys.argv[1]
    script(file_path)
    