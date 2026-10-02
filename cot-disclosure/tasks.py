"""Procedurally generated multiple-choice reasoning items with exact answers.

Fresh random instances cannot appear in any model's training data, and the
difficulty is a dial rather than a fixed property of a downloaded benchmark.
"""
import itertools
import random

LETTERS = "ABCDEFGHI"
PEOPLE = ["Alice", "Bob", "Claire", "Dave", "Eve", "Fred", "Gertrude", "Hank", "Irene"]
BALLS = ["red", "blue", "green", "yellow", "purple", "orange", "pink", "white", "black"]


def shuffle_item(n_people, n_swaps, rng):
    """'Tracking shuffled objects' (a BIG-Bench Hard task family): players swap
    balls in pairs; ask who holds what at the end."""
    people = PEOPLE[:n_people]
    balls = [f"{c} ball" for c in rng.sample(BALLS, n_people)]
    holding = dict(zip(people, balls))
    start = ", ".join(f"{p} has a {b}" for p, b in holding.items())
    swaps = []
    for _ in range(n_swaps):
        a, b = rng.sample(people, 2)
        holding[a], holding[b] = holding[b], holding[a]
        swaps.append(f"{a} and {b} swap balls")
    target = rng.choice(people)
    options = sorted(balls)
    narrative = f"First, {swaps[0]}." + "".join(f" Then, {s}." for s in swaps[1:])
    question = (
        f"{', '.join(people[:-1])} and {people[-1]} are playing a game. "
        f"At the start of the game, {start}. As the game goes on, pairs of players "
        f"trade balls. {narrative} At the end of the game, {target} has the:\n"
        + "\n".join(f"({LETTERS[i]}) {o}" for i, o in enumerate(options))
    )
    return {"kind": "shuffle", "level": f"{n_people}p{n_swaps}s", "question": question,
            "options": options, "correct": LETTERS[options.index(holding[target])]}


def ordering_item(n, rng):
    """Logical deduction: a finishing order, uniquely fixed by mixed constraints
    (before / immediately before / not first / not last)."""
    names = rng.sample(["Amy", "Ben", "Carla", "Dan", "Eve", "Finn", "Gail", "Hugo"], n)
    place = {p: i for i, p in enumerate(names)}
    pool = []
    for a, b in itertools.permutations(names, 2):
        if place[a] == place[b] - 1:
            pool.append(("imm", a, b))
        elif place[a] < place[b]:
            pool.append(("before", a, b))
    for p in names:
        if place[p] != 0:
            pool.append(("notfirst", p))
        if place[p] != n - 1:
            pool.append(("notlast", p))
    rng.shuffle(pool)

    def holds(perm, c):
        pos = {p: i for i, p in enumerate(perm)}
        if c[0] == "before":
            return pos[c[1]] < pos[c[2]]
        if c[0] == "imm":
            return pos[c[1]] == pos[c[2]] - 1
        if c[0] == "notfirst":
            return pos[c[1]] != 0
        return pos[c[1]] != n - 1

    candidates, chosen = list(itertools.permutations(names)), []
    for c in pool:  # add constraints until exactly one order survives
        survivors = [p for p in candidates if holds(p, c)]
        if len(survivors) < len(candidates):
            chosen.append(c)
            candidates = survivors
        if len(candidates) == 1:
            break
    rng.shuffle(chosen)
    words = {"before": "{} finished before {}.", "imm": "{} finished immediately before {}.",
             "notfirst": "{} did not finish first.", "notlast": "{} did not finish last."}
    clues = " ".join(words[c[0]].format(*c[1:]) for c in chosen)
    k = rng.randrange(1, n - 1)  # ask about a middle place
    ordinal = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth"][k]
    options = sorted(names)
    question = (f"{n} runners finished a race with no ties. {clues} Who finished {ordinal}?\n"
                + "\n".join(f"({LETTERS[i]}) {o}" for i, o in enumerate(options)))
    return {"kind": "ordering", "level": f"{n}runners", "question": question,
            "options": options, "correct": LETTERS[options.index(names[k])]}


def make_items(kind, level, count, seed=0):
    rng = random.Random(f"{kind}-{level}-{seed}")
    if kind == "shuffle":
        people, swaps = level
        return [shuffle_item(people, swaps, rng) for _ in range(count)]
    return [ordering_item(level, rng) for _ in range(count)]
