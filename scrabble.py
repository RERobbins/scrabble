from scrabble_helpers import scrabble_argparse, scrabble
from time import perf_counter

timer_start = perf_counter()

# Parse command line input.
# Tiles are transformed to upper case.
#
# The function returns RACK, CONSTRAINTS and TIMER.
# RACK is an uppercase string.
# CONSTRAINTS is None or a compiled regular expression object.
# TIMER is a boolean.

rack, constraints, timer = scrabble_argparse()

# All the work is done in scrabble_helpers.scrabble.

scrabble(rack, constraints)

timer_stop = perf_counter()

if timer:
    print(f"Elapsed execution time: {timer_stop - timer_start} seconds")
