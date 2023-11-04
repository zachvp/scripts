import os
import sys

# helpers
def compare_similarity(lhs : str, rhs : str) -> int :
    assert len(lhs) == len(rhs), 'expecting equal string lengths for input: {} | {}'.format(lhs, rhs)

    similarity = 0
    for i in range(len(lhs)):
        if lhs[i] == rhs[i]:
            similarity += 1
    return similarity

# state

## input
file_path = 'input.txt'

## storage
guesses = []

## main

# read file lines into guesses
# trim each guess in guesses
with open(file_path, 'r') as file:
    guesses = [guess.rstrip() for guess in file.readlines()]

# validate input
assert len(guesses) > 1, 'expecting at least 2 guesses'
for i in range(1, len(guesses)):
    assert len(guesses[i]) == len(guesses[i-1]), 'all guesses should be equal length'

while len(guesses) > 0:
    prompt = 'next guess'
    print('{}: {}'.format(prompt, guesses[0]))

    guess = guesses.pop(0)

    # read the result of the guess
    prompt = 'was the guess correct (y/n)?\n'
    result = input(prompt).lower()
    if result == 'y':
        print('SUCCESS! Exiting...')
        exit()
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
        raise Exception('InvalidInput: {}. Expect y/n'.format(result))


    