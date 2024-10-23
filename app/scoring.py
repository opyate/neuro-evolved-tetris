import numpy as np


def exponential_scale(x, N=10, base=1.0):
    """Scales the range 0 to 1.0 exponentially.

    Adjust the base for stronger/weaker scaling.

    Args:
        x: The input value in the range 0 to 1.0.
        base: The base of the exponential function.

    Returns:
        The exponentially scaled value.
    """
    if base <= 1.0:
        base = 1.0
    return (base**x - 1) / (base ** (N - 1) - 1)  # * (N - 1)


from functools import lru_cache


@lru_cache(maxsize=None)
def scaler(idx: int, N: int, base: float = 1.65) -> float:
    """Returns interpolated value based on the index in a range N

    Args:
        idx (int): the index into the range
        N (int): the range length

    Returns:
        float: the interpolated value
    """

    return np.interp(idx, np.arange(N), base ** np.arange(N) / (N - 1))


def _fill_score(grid: list[list[int]]) -> tuple[list[float], list[float]]:
    """Calculate the fill row scores and scoring factors for the grid.

    This allows us to score a board that nearly had filled lines, which would have
    been cleared and given us 100,300,500,800 points for 1,2,3,4 lines cleared.

    The scaling (base) values were tuned by hand to give us values just below a full score, e.g.
    10 filled cells in a row will be cleared by the engine and give 100 points for that row,
    but 9 filled cells in a row won't be cleared, but is still scored at 90-ish points,
    then drops off significantly for fewer filled cells, and lower row indices

    Args:
        grid (list[list[int]]): the game grid

    Returns:
        tuple[list[float], list[float]]: A tuple of row scores and scoring factors
    """
    row_length = len(grid[0])
    row_scores = []
    scoring_factors = []
    for row_idx, row in enumerate(grid):
        row_score = 0

        for cell in row:
            if isinstance(cell, str):
                row_score += 1

        # the more grid cells are filled, the higher the score
        row_score_scaled = scaler(row_score, row_length, 1.63)

        # the further down the grid the cells are filled, the higher the score
        scoring_factor = scaler(row_idx, row_length)

        scoring_factors.append(scoring_factor)
        row_scores.append(row_score_scaled * scoring_factor)

    return row_scores, scoring_factors


def fill_score(grid: list[list[int]]) -> float:
    """Returns the score for a partially-filled grid by just summing the row scores.

    Args:
        grid (list[list[int]]): the game grid

    Returns:
        float: the score
    """

    row_scores, _scoring_factors = _fill_score(grid)
    return np.sum(row_scores).item()


"""
s1, s2 = _fill_score(
    [
        ['a','a','a','a','a','a','a','a','a',0],
        ['a','a','a','a','a','a','a','a','a',0],
        ['a','a','a','a','a','a','a','a','a',0],
        ['a','a','a','a','a','a','a','a','a',0],
        ['a','a','a','a','a','a','a','a','a',0],
        ['a','a','a','a','a','a','a','a','a',0],
        ['a','a','a','a','a','a','a','a','a',0],
        ['a','a','a','a','a','a','a','a','a',0],
        ['a','a','a','a','a','a','a','a','a',0],
        ['a','a','a','a','a','a','a','a','a',0],
    ]
)
s1 # yields:

[np.float64(1.0027748214056011),
 np.float64(1.654578455319242),
 np.float64(2.7300544512767493),
 np.float64(4.504589844606636),
 np.float64(7.432573243600948),
 np.float64(12.263745851941563),
 np.float64(20.23518065570358),
 np.float64(33.3880480819109),
 np.float64(55.09027933515299),
 np.float64(90.89896090300243)]
"""
