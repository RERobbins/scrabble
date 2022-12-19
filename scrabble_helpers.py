import argparse
import io
import re
import sys
from collections import Counter
from operator import itemgetter
from wordscore import score_word

# This module contains scrabble support functions.
# The two primary functions are scrabble_argparse and scrabble.
#
# Normally, score_word would be in here too, but the homework
# requirements mandate that it be in a module named wordscore.
# I realize I could have put these functions into that module,
# but that module name seemed poor for a more general collection
# of functions.


def scrabble_argparse():
    """Validate input and return rack, constraints and timer."""

    # We use the argparse package to handle rudimentary command line processing
    # and to provide a help function.  Once the input has been validated
    # we transform the tile rack to upper case.  Any constraints string
    # presented will be compiled and returned as a compiled regular expression
    # object.  Errors result in a message and then the function calls quit() to
    # terminate the program rather than raising an exception.  Since the
    # program is intended to run from the command line and not a development
    # environment it does not seem appropriate to get into stack traces.
    # A timer boolean is also returned.

    parser = argparse.ArgumentParser(description="Scrabble words from tiles.")
    parser.add_argument(
        "rack",
        help="""A valid tile rack with two to seven tiles.
        Tiles can be any upper or lower case alphabetic character.
        In addition the tiles may include up to two wildcards, a maximum
        of one '*' and a maximum of one '?'.
        """,
    )

    parser.add_argument(
        "--constraints",
        "-c",
        help="""A regular expression to constrain results.
        The constraint expression will follow Python regular expression
        formatting rules.  Expressions are run against the beginning of the
        string with Python match and not Python search.
        """,
    )
    parser.add_argument(
        "--timer",
        "-t",
        action="store_true",
        help="""If specified, add a performance timer.""",
    )

    args = parser.parse_args()
    rack = args.rack
    constraints = args.constraints
    timer = args.timer

    # This is a bit of a kludge to capture the usage string from argparse
    # so we can create consistent warning messages that argparse doesn't
    # generate for us.  We capture the first line of the help block.

    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    parser.print_help()
    stub = new_stdout.getvalue().splitlines()[0] + f"\n{parser.prog}: error:"
    sys.stdout = old_stdout

    # The following block of code is where we enforce most argument syntax
    # requirements not caught and handled by argparse directly.  Each
    # defect results in a helpful message and then a call to quit().

    if len(rack) < 2 or len(rack) > 7:
        print(f"{stub} rack must contain between 2 and 7 tiles")
        quit()

    if rack.count("*") > 1:
        print(f"{stub} rack cannot contain more than one *")
        quit()

    if rack.count("?") > 1:
        print(f"{stub} rack cannot contain more than one ?")
        quit()

    for char in rack:
        if char.isalpha() or char in "*?":
            continue
        else:
            print(f"{stub} rack limited to alphabetic characters, * and ?")
            quit()

    if constraints is not None:
        try:
            constraints = re.compile(constraints, re.IGNORECASE)
        except re.error:
            print(f"{stub} constraints is an invalid regex pattern")
            quit()

    return rack.upper(), constraints, timer


def scrabble(rack, constraint=None):
    """Print a list of tuples representing valid scrabble words that can be
    formed from the tile rack.  Results are sorted in descending score order
    and then alplhabetically.  The optional constraint parameter is a compiled
    regular expression object that can be used to limit the output.
    """

    # Our goal is to aggressively eliminate words from consideration.
    # So rather than enumerate possibilities from the tile rack and checking
    # against a list of valid words, we approach the problem by eliminating
    # dictionary words from consideration and then looking carefully at the
    # survivors.  The phases get increasingly complex, so order matters.
    # Getting rid of a word in phase[n] is better than doing so in
    # phase[n+1].
    #
    # Phase 1 -- length
    #
    # Any scrabble word that is longer than the number of tiles in the rack
    # can be excluded from consideration.  The length function on strings is
    # fast and independent of string size.
    #
    # Phase 2 -- wildcards
    #
    # With a tile rack of two to seven tiles, we have at most seven characters
    # from which we can construct words.  We have up to two wildcards though.
    # We can use a regular expression to search for characters we do not have.
    # If we have no wildcards, then a single excluded character eliminates the
    # word.  If we have a single wildcard, then any two excluded characters
    # will eliminate the word.  If we have a pair of wildcards, then it takes
    # three excluded characters to eliminate the word from consideration.
    # We use three string patterns, one for each of those scenarios and select
    # based on the number of wildcard tiles we have in our rack.  We look for
    # the exact number of excluded characters to disqualify a word rather than
    # tallying up all of the excluded characters in a word because we want to
    # have the regular expression search resolve as quickly as possible.
    #
    # Phase 3 -- user constraint
    #
    # Users are permitted to supply their own regular expression that results
    # must satisfy.  So, any word that fails to match that expression can be
    # excluded. It's not obvious whether to apply this filter before or after
    # the wildcard filter described above as a lot depends on the complexity of
    # the user constraint.
    #
    # Phase 4 -- final processing
    #
    # Words that have made it through the prior phases may not be valid.
    # This is because we may not have sufficient inventory in the rack
    # for any given character.  Here we verify if a word can, in fact,
    # be assembled from the tiles at hand.

    # Initializa result, a list of tuples: [(word score, word),...]
    result = []

    # Grab the number of tiles.
    tile_count = len(rack)

    # Count the number of wildcards and eliminate them from the rack.
    wildcard_re = re.compile("\\*|\\?")
    number_of_wildcards = len(wildcard_re.findall(rack))
    alpha_tiles = wildcard_re.sub("", rack)

    # We use rack_alpha_counter in the final filtering phase.
    rack_alpha_counter = Counter(alpha_tiles)

    # The list of unique alphabetic characters forms the basis
    # for the regular expression exclusinon strings below.
    # Those strings match on all other alphabetic characters, i.e.,
    # characters for which we must use wildcard characters.
    # A rack consisting of just two wildcard characters is a special case.
    # When that happens we don't apply phase 2 filters.  That would be
    # pointless as at that part of the process we have already isolated
    # down to all two character candidates and none would be excluded.

    alpha_tiles_str = "".join(rack_alpha_counter.keys())

    if alpha_tiles_str:
        exclude_re = (
            re.compile(".*[^" + alpha_tiles_str + "]"),
            re.compile("(.*[^" + alpha_tiles_str + "]){2}"),
            re.compile("(.*[^" + alpha_tiles_str + "]){3}"),
        )

    with open("sowpods.txt", "r") as infile:
        raw_input = infile.readlines()
        for line in raw_input:
            word = line.strip("\n")
            if len(word) > tile_count:
                continue
            if alpha_tiles_str and exclude_re[number_of_wildcards].match(word):
                continue
            if constraint and constraint.match(word) is None:
                continue
            #
            # At this point the word is a strong candidate. Iterate through
            # the candidate's characters in descending order of value and
            # draw from the alpha tiles first.  If we are able to assemble
            # the word we will deduct the value of characters satisfied by
            # relying on wildcard inventory.
            #
            wildcards_available = number_of_wildcards
            scoring_delta = 0
            valid = None
            for char, value, need in unpack_candidate(word):
                have = rack_alpha_counter[char]
                if have >= need:
                    pass
                elif have + wildcards_available >= need:
                    wildcards_available -= need - have
                    scoring_delta += (need - have) * value
                else:
                    valid = False
                    break
            if valid is not False:
                result.append((score_word(word) - scoring_delta, word))

    # The following section of code makes use of the list sort method.
    # The sort method is more efficient than the sorted function.
    # We use the itemgetter function from the operator module instead
    # of lambda functions to access the relevant tuple elements.
    # itemgetter[0] of a word tuple references the score element.
    # itemgetter[1] of a word tuple references the word element.

    # We sort in order to present the results sorted by score in descending
    # order and then in alphabetic order.  The two pass approach is needed.
    # We sort on the secondary key first.

    result.sort(key=itemgetter(1))
    result.sort(key=itemgetter(0), reverse=True)

    for word_tuple in result:
        print(f"({word_tuple[0]}, {word_tuple[1].lower()})")

    print(f"Total number of words: {len(result)}")

    return


def unpack_candidate(x):
    """Return list of tuples: (char, scoring_value, count) for each char in x,
    sorted by scoring_value in descending order.
    """
    # The code that attempts to assemble a candidate word from rack processes
    # each character in the word, sorted by descending scrabble scoring value.
    # That code also relies on the count of that character in the candidate.
    counter = Counter(x)
    result = sorted(
        [(char, score_word(char), counter[char]) for char in counter.keys()],
        key=itemgetter(1),
        reverse=True,
    )
    return result
