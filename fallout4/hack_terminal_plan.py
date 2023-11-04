# fallout 4 terminal hack utility

# state guesses : word array

# read file lines into guesses
# trim each guess in guesses

# while guesses are not empty
#   guess = guesses[0]
#   output guesses[0]
#   remove guesses[0]

#   read result : guess result bool

#   if result is SUCCESS
#       return

#   read hint : integer of letters in guess in the correct location

#   state possibilities : possible future guesses array

#   for each possibility in guesses
#       compare guess and possibility : returns similarity integer
#       if similarity == hint
#           possibilities += guess
#   write possibilities into guesses
