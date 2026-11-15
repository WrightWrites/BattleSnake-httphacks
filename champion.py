"""champion.py - main.py with its tested strengths kept and its weaknesses changed.

Built after a round of testing main.py, snake_a to snake_e and trapper.py
against each other on 7x7, 11x11 and 19x19 boards.

Kept from main.py (testing showed these help):
  - Territory scoring (Step 9).
  - The trapped check and space-filling escape search (Step 14).
  - No growth cap once a single opponent is left.
  - The lookahead (Step 10) and pin check (Step 11), which had no measurable
    effect either way and are kept for the specific deaths they were written for.

Changed from main.py:
  - Step 12, food race check. main.py always backs away from nearby food that
    a same-size or bigger snake reaches as soon as it does. This file commits
    to the food when the move still leaves a safe, roomy way to back out, and
    only backs off when it would not. When every piece of food is contested it
    targets the closest one again instead of giving up on food.
  - Tail squares. main.py treats every tail as a wall. This file may move onto
    a tail square when the tail is certain to move away this turn: it is not
    doubled up from eating, and for another snake there is no food next to its
    head.
  - Step 13, hunting (new). HUNT_STYLE picks the kind:
      "trapper"  trapper.py's hunt, repaired so that it fires. It picks one
                 vulnerable opponent and rewards the moves that leave it less
                 space than our other moves would, only when the move keeps our
                 own space safe. trapper.py compared the target's space before
                 and after our move, which almost never showed a gain.
      "duel"     snake_c_hunter's hunt: with one opponent left and a lead of
                 HUNT_LEAD or more, close in on its head and take its space.
      "off"      no hunting.
  - A "champion.py settings" block holds VARIANT_NAME, DEFAULT_PORT,
    SNAKE_COLOR and the hunting settings. info() returns SNAKE_COLOR, and the
    file listens on DEFAULT_PORT unless the PORT environment variable is set.

Left out on purpose (testing showed these hurt): the "lead by 2" food rule from
snake_a, snake_b, snake_d and snake_e, and STAY_LONGEST = True from trapper.py.
"""

# Welcome to
# __________         __    __  .__                               __
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | __ ____
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\\_____>
#
# This file can be a nice home for your Battlesnake logic and helper functions.
#
# To get you started we've included code to prevent your Battlesnake from moving backwards.
# For more info see docs.battlesnake.com

import collections
import os
import random
import typing
from datetime import datetime
# from waitress import serve
# serve(app, host=host, port=port, threads=8)


# Settings you can tune
GROWTH_CAP_FRACTION = 0.125   # stop growing at this share of the board's squares
MIN_GROWTH_CAP = 4            # never cap growth below this length
STAY_LONGEST = False          # keep growing past the cap if an opponent is as long as us
HUNGRY_HEALTH = 40            # below this health, eating becomes urgent
HUNGRY_FOOD_WEIGHT = 40       # pull toward food when hungry
GROWING_FOOD_WEIGHT = 10      # pull toward food when still growing
AVOID_FOOD_PENALTY = 60       # push away from food when at the growth cap
TERRITORY_WEIGHT = 1.0        # value of each square we can reach before opponents
NO_SAFE_EXIT_PENALTY = 350    # cost of a move whose every way out a bigger snake could contest
SEALED_CORRIDOR_PENALTY = 600 # cost of entering a corridor an opponent can seal before we get out
CORRIDOR_LOOKAHEAD = 8        # how many squares along a corridor to check
FOOD_RACE_RANGE = 3           # how close a contested piece of food must be to back away from it
FOOD_RACE_PENALTY = 150       # cost of closing in on food a same-size or bigger snake reaches first
TRAPPED_PENALTY = 400         # cost of a move into a tight space with no path that lasts until it opens
ESCAPE_DEPTH_CAP = 24         # a path this long counts as survived
ESCAPE_SEARCH_NODES = 3000    # limit on the escape search, to stay well inside the time budget
STARVING_MARGIN = 10          # starving = health no more than this above the distance to the nearest food
RETREAT_TERRITORY_WEIGHT = 5.0  # value of each square we reach first while retreating from a lost food race

# champion.py settings
VARIANT_NAME = "champion"
DEFAULT_PORT = "8010"         # port this file listens on unless PORT is set
SNAKE_COLOR = "#00C2A8"
HUNT_STYLE = "trapper"        # "trapper": hunt one vulnerable snake at any stage; "duel": chase and squeeze only with one opponent left; "off"
HUNT_LEAD = 2                 # "duel" style: only hunt a snake we out-length by at least this much
DUEL_HUNT_WEIGHT = 8          # "duel" style: pull toward the squares next to the opponent's head
DUEL_SQUEEZE_WEIGHT = 2       # "duel" style: cost per square the opponent can still reach before us
TRAPPER_HUNT_WEIGHT = 8       # "trapper" style: reward per square of territory this move denies the hunted snake
HUNT_CAP = 200                # "trapper" style: most a hunt can add - kept below every survival penalty
CORNERED_TERRITORY_FACTOR = 2 # "trapper" style: a snake is vulnerable when its territory is under this many times its length
FLANK_DISTANCE = 3            # "trapper" style: a same-size or bigger snake this close halves the hunt reward


# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    print("INFO")

    return {
        "apiversion": "1",
        "author": "wright",  # TODO: Your Battlesnake Username
        "color": SNAKE_COLOR,
        "head": "orca",  # TODO: Choose head
        "tail": "small-rattle",  # TODO: Choose tail
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    print("GAME START")


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")


# flood_fill counts how many open squares can be reached from a starting square
def flood_fill(start_square, blocked, board_width, board_height) -> int:
    seen = {start_square}
    to_visit = [start_square]
    while to_visit:
        x, y = to_visit.pop()
        for neighbour in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            nx, ny = neighbour
            if nx < 0 or nx >= board_width or ny < 0 or ny >= board_height:
                continue
            if neighbour in blocked or neighbour in seen:
                continue
            seen.add(neighbour)
            to_visit.append(neighbour)
    return len(seen)


# open_neighbours lists the squares next to a square that are on the board and not blocked
def open_neighbours(square, blocked, board_width, board_height) -> typing.List:
    x, y = square
    result = []
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= nx < board_width and 0 <= ny < board_height and (nx, ny) not in blocked:
            result.append((nx, ny))
    return result


# distances_from works out how many moves away each reachable square is from a start square
def distances_from(start_square, blocked, board_width, board_height) -> typing.Dict:
    distances = {start_square: 0}
    queue = collections.deque([start_square])
    while queue:
        square = queue.popleft()
        for neighbour in open_neighbours(square, blocked, board_width, board_height):
            if neighbour not in distances:
                distances[neighbour] = distances[square] + 1
                queue.append(neighbour)
    return distances


# escape_search looks for a way to stay alive inside a tight space. It tries
# paths from start_square that use the space as fully as possible, and counts a
# path as an escape when it reaches a square that a snake's body will have left
# by the time we get there (usually our own tail area opening up).
# Returns 1.0 when an escape exists, otherwise the share of the needed moves the
# longest path survives.
def escape_search(start_square, region, free_at, own_squares, food_squares,
                  my_length, board_width, board_height) -> float:
    target_depth = min(ESCAPE_DEPTH_CAP, my_length)
    best = [1]
    nodes = [0]
    visited = {start_square}

    def explore(square, move_number, eaten):
        # move_number is the move that put us on `square` (1 = the move being scored)
        if move_number > best[0]:
            best[0] = move_number
        if best[0] >= target_depth:
            return True
        nodes[0] += 1
        if nodes[0] > ESCAPE_SEARCH_NODES:
            return False
        x, y = square
        options = []
        for neighbour in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            nx, ny = neighbour
            if nx < 0 or nx >= board_width or ny < 0 or ny >= board_height:
                continue
            if neighbour in visited:
                continue
            if neighbour in free_at:
                # A body square: we can only step in once that snake has moved off it.
                # Our own body clears one move later for each piece of food we eat.
                opens = free_at[neighbour] + (eaten if neighbour in own_squares else 0)
                if move_number + 1 >= opens:
                    return True   # the space has opened up - we are out
                continue
            if neighbour not in region:
                continue
            options.append(neighbour)
        # Try the tightest squares first, so the path hugs the edges and wastes no space
        def tightness(option):
            ox, oy = option
            free_sides = 0
            for side in ((ox + 1, oy), (ox - 1, oy), (ox, oy + 1), (ox, oy - 1)):
                if side in region and side not in visited and side not in free_at:
                    free_sides += 1
            return free_sides
        options.sort(key=tightness)
        for option in options:
            visited.add(option)
            escaped = explore(option, move_number + 1, eaten + (1 if option in food_squares else 0))
            visited.discard(option)
            if escaped:
                return True
        return False

    if explore(start_square, 1, 1 if start_square in food_squares else 0):
        return 1.0
    return best[0] / target_depth


# territory_counts works out how many squares each snake would reach first.
# offsets[i] is a head-start penalty (1 for us after a move, 0 for opponents).
# A longer snake wins a tie; a tie between equal-length snakes belongs to nobody.
def territory_counts(heads, lengths, offsets, blocked, board_width, board_height) -> typing.List[int]:
    maps = [distances_from(head, blocked, board_width, board_height) for head in heads]
    counts = [0] * len(heads)
    for square in set().union(*maps):
        ranked = sorted(
            (distance_map.get(square, 9999) + offsets[i], -lengths[i], i)
            for i, distance_map in enumerate(maps)
        )
        if len(ranked) > 1 and ranked[0][:2] == ranked[1][:2]:
            continue
        counts[ranked[0][2]] += 1
    return counts


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:

    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    # We've included code to prevent your Battlesnake from moving backwards
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_neck = game_state["you"]["body"][1]  # Coordinates of your "neck"

    if my_neck["x"] < my_head["x"]:  # Neck is left of head, don't move left
        is_move_safe["left"] = False

    elif my_neck["x"] > my_head["x"]:  # Neck is right of head, don't move right
        is_move_safe["right"] = False

    elif my_neck["y"] < my_head["y"]:  # Neck is below head, don't move down
        is_move_safe["down"] = False

    elif my_neck["y"] > my_head["y"]:  # Neck is above head, don't move up
        is_move_safe["up"] = False

    # TODO: Step 1 - Prevent your Battlesnake from moving out of bounds
    # board_width = game_state['board']['width']
    # board_height = game_state['board']['height']
        # Step 1 - stay inside the board
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']

    if my_head["x"] == 0:
        is_move_safe["left"] = False
    if my_head["x"] == board_width - 1:
        is_move_safe["right"] = False
    if my_head["y"] == 0:
        is_move_safe["down"] = False
    if my_head["y"] == board_height - 1:
        is_move_safe["up"] = False

    
    # TODO: Step 2 - Prevent your Battlesnake from colliding with itself
    # my_body = game_state['you']['body']
    # Steps 2 and 3 - don't run into any snake's body (including your own)
    next_squares = {
        "up":    {"x": my_head["x"],     "y": my_head["y"] + 1},
        "down":  {"x": my_head["x"],     "y": my_head["y"] - 1},
        "left":  {"x": my_head["x"] - 1, "y": my_head["y"]},
        "right": {"x": my_head["x"] + 1, "y": my_head["y"]},
    }
    # A tail square is safe to move onto when the tail is certain to move away
    # this turn: it isn't doubled up from eating last turn, and (for another
    # snake) there is no food next to its head that it could eat this turn.
    for snake in game_state['board']['snakes']:
        body = snake["body"]
        tail_moves_away = len(body) >= 2 and body[-1] != body[-2]
        if tail_moves_away and snake["id"] != game_state["you"]["id"]:
            head = body[0]
            for piece in game_state['board']['food']:
                if abs(piece["x"] - head["x"]) + abs(piece["y"] - head["y"]) == 1:
                    tail_moves_away = False
        solid = body[:-1] if tail_moves_away else body
        for direction, square in next_squares.items():
            if square in solid:
                is_move_safe[direction] = False



    # TODO: Step 3 - Prevent your Battlesnake from colliding with other Battlesnakes
    # opponents = game_state['board']['snakes']

    # Are there any safe moves left?
    safe_moves = []
    for move, isSafe in is_move_safe.items():
        if isSafe:
            safe_moves.append(move)

    if len(safe_moves) == 0:
        print(f"MOVE {game_state['turn']}: No safe moves detected! Moving left")
        return {"move": "left"}

    you = game_state["you"]
    my_length = len(you["body"])
    my_head_square = (my_head["x"], my_head["y"])
    opponents = [s for s in game_state['board']['snakes'] if s["id"] != you["id"]]

    # Squares occupied by snake bodies
    blocked = set()
    for snake in game_state['board']['snakes']:
        # A snake's tail square frees up next turn, so it doesn't count as blocked
        # (after eating, the tail is doubled up and the square stays blocked)
        for segment in snake["body"][:-1]:
            blocked.add((segment["x"], segment["y"]))

    # What each opponent can do next: where its head could go, how much room it has,
    # and how far it is from every square
    opponent_info = []
    for opponent in opponents:
        head = (opponent["body"][0]["x"], opponent["body"][0]["y"])
        options = open_neighbours(head, blocked, board_width, board_height)
        room = max((flood_fill(o, blocked, board_width, board_height) for o in options), default=0)
        opponent_info.append({
            "head": head,
            "length": len(opponent["body"]),
            "options": options,
            "room": room,
            "distances": distances_from(head, blocked, board_width, board_height),
        })

    # Step 4 - choose which food to go for, skipping food another snake would win.
    # A snake wins a piece of food if it gets there first, or arrives at the same
    # time and is at least as long as us (it would win the head-to-head).
    my_distances = distances_from(my_head_square, blocked, board_width, board_height)
    reachable_food = []
    winnable_food = []
    dangerous_food = []   # food a same-size or bigger snake reaches as soon as we do
    for piece in game_state['board']['food']:
        square = (piece["x"], piece["y"])
        if square not in my_distances:
            continue
        reachable_food.append(square)
        beaten = False
        for info in opponent_info:
            their_distance = info["distances"].get(square)
            if their_distance is None:
                continue
            if their_distance < my_distances[square]:
                beaten = True
            elif their_distance == my_distances[square] and info["length"] >= my_length:
                beaten = True
        if not beaten:
            winnable_food.append(square)
        # Racing a same-size or bigger snake to food ends in a head-to-head we lose
        if any(
            info["length"] >= my_length
            and info["distances"].get(square, 9999) <= my_distances[square]
            for info in opponent_info
        ):
            dangerous_food.append(square)

    # Step 8 - growth plan: how long we want to get depends on the board size.
    # Small boards get a low cap so we don't outgrow the space and coil into
    # ourselves; big boards get a high cap so we grow fast early on.
    board_area = board_width * board_height
    growth_cap = max(MIN_GROWTH_CAP, int(board_area * GROWTH_CAP_FRACTION))
    if STAY_LONGEST:
        # Never settle for being shorter than an opponent - a shorter snake loses
        # head-to-heads, so keep at least one segment ahead of the longest one
        longest_opponent = max((info["length"] for info in opponent_info), default=0)
        growth_cap = max(growth_cap, longest_opponent + 1)
    at_growth_cap = my_length >= growth_cap
    if len(opponents) == 1:
        # Down to one opponent: lift the cap, since the board has room again and
        # the longer snake wins the head-to-heads that decide a duel
        at_growth_cap = False

    # "Hungry" means health is low enough that we must eat now, allowing for the
    # time it takes to travel to the nearest food
    nearest_food_distance = min((my_distances[square] for square in reachable_food), default=0)
    hungry = you["health"] < max(HUNGRY_HEALTH, nearest_food_distance * 2 + 10)

    # "Starving" means backing off from the nearest food now would mean dying
    # before we could come back for it
    starving = bool(reachable_food) and you["health"] <= nearest_food_distance + STARVING_MARGIN

    # Only go after food when we still want to grow, or when we need the health
    target_food = None
    if hungry or not at_growth_cap:
        if winnable_food:
            target_food = min(winnable_food, key=lambda square: my_distances[square])
        else:
            # Every piece is contested - prefer the closest one that isn't a race
            # against a same-size or bigger snake, but commit to a race if that is
            # all there is. Step 12 backs us off, move by move, whenever closing in
            # would leave no way to back out.
            fallback_food = [f for f in reachable_food if f not in dangerous_food]
            if not fallback_food:
                fallback_food = reachable_food
            if fallback_food:
                target_food = min(fallback_food, key=lambda square: my_distances[square])

    # Retreat: we want food, but the only food on offer is a race we would lose.
    # Back off into the emptiest part of the board and gamble on food spawning
    # there, by valuing the squares we can reach before any opponent much more.
    retreating = (
        target_food is None
        and bool(dangerous_food)
        and not starving
        and (hungry or not at_growth_cap)
    )

    food_weight = HUNGRY_FOOD_WEIGHT if hungry else GROWING_FOOD_WEIGHT
    avoid_food = at_growth_cap and not hungry
    food_squares = {(piece["x"], piece["y"]) for piece in game_state['board']['food']}

    # For the trapped check: the move number on which each body square opens up
    # (1 = this turn's move), and the squares an opponent's head could reach
    # within two moves, which we assume it could close off
    free_at = {}
    own_squares = set()
    for snake in game_state['board']['snakes']:
        snake_length = len(snake["body"])
        for index, segment in enumerate(snake["body"]):
            body_square = (segment["x"], segment["y"])
            free_at[body_square] = max(free_at.get(body_square, 0), snake_length - index)
            if snake["id"] == you["id"]:
                own_squares.add(body_square)
    closable = set()
    for info in opponent_info:
        for reachable_square, their_distance in info["distances"].items():
            if 0 < their_distance <= 2:
                closable.add(reachable_square)

    in_duel = len(opponents) == 1

    # Hunting, "trapper" style: pick one vulnerable opponent to go after this turn.
    # A snake is vulnerable when it has at most one open move, or when the space
    # it would reach first is small compared with its length. If several are
    # vulnerable, hunt the one with the least space.
    hunt_target = None
    opponent_heads = [info["head"] for info in opponent_info]
    opponent_lengths = [info["length"] for info in opponent_info]
    no_offsets = [0] * len(opponent_info)
    if HUNT_STYLE == "trapper" and opponent_info:
        territory_now = territory_counts(
            [my_head_square] + opponent_heads, [my_length] + opponent_lengths,
            [0] + no_offsets, blocked, board_width, board_height,
        )
        for i, info in enumerate(opponent_info):
            cornered = (len(info["options"]) <= 1
                        or territory_now[i + 1] < info["length"] * CORNERED_TERRITORY_FACTOR)
            if cornered and (hunt_target is None or territory_now[i + 1] < territory_now[hunt_target + 1]):
                hunt_target = i
    target_space_after = {}   # move -> squares the hunted snake would still reach first
    hunt_allowed = {}         # move -> 1.0 (safe to hunt), 0.5 (safe but flanked) or 0 (not safe)

    # Score every safe move and pick the best
    scores = {}
    for candidate in safe_moves:
        square = (next_squares[candidate]["x"], next_squares[candidate]["y"])
        score = 0.0

        # Step 5 - flood fill: avoid moves into a space too small to fit our body
        room = flood_fill(square, blocked, board_width, board_height)
        roomy = room >= my_length
        if not roomy:
            score -= 1000 * (1 - room / my_length)
        score += room * 0.05

        # Step 6 - head-to-head: stay away from squares a same-size or bigger snake
        # could move its head into; go for squares a smaller snake could move into,
        # but only when the move leaves us enough room to not get stuck
        for info in opponent_info:
            if square in info["options"]:
                if info["length"] >= my_length:
                    score -= 500
                elif roomy:
                    # The fewer choices the smaller snake has, the more likely the kill
                    score += 300 / len(info["options"])

        # Step 7 - trapping: reward moves that put our body across an opponent's
        # way out, leaving it less room than its own length
        if roomy:
            blocked_after = blocked | {square}
            for info in opponent_info:
                room_after = max(
                    (flood_fill(o, blocked_after, board_width, board_height)
                     for o in info["options"] if o != square),
                    default=0,
                )
                if room_after < info["length"] and room_after < info["room"]:
                    score += 120 + (info["room"] - room_after)

        # Step 14 - trapped check: if the space we would be left in (assuming nearby
        # opponents close the gaps they can reach) is smaller than our body, search
        # for a path that uses that space fully and lasts until our tail area opens
        # up. Moves with no such path are penalised by how soon they run out.
        escape_found = False
        sealed_region = set(distances_from(square, blocked | closable, board_width, board_height))
        if len(sealed_region) < my_length:
            survival = escape_search(square, sealed_region, free_at, own_squares, food_squares,
                                     my_length, board_width, board_height)
            score -= TRAPPED_PENALTY * (1 - survival)
            # With a sure way out through our own space, being sealed in is survivable,
            # so the two checks below don't need to warn us off this move
            escape_found = survival >= 1.0

        # Step 10 - look one turn further: after this move, will we have at least
        # one way out that a same-size or bigger snake could not also reach in time?
        # (A snake two or fewer moves from a square can contest it on our next turn.)
        length_after = my_length + (1 if square in food_squares else 0)
        exits = open_neighbours(square, blocked | {square}, board_width, board_height)
        safe_exits = 0
        for exit_square in exits:
            contested = any(
                info["length"] >= length_after
                and info["distances"].get(exit_square, 9999) <= 2
                for info in opponent_info
            )
            if not contested:
                safe_exits += 1
        if safe_exits == 0 and not escape_found:
            score -= NO_SAFE_EXIT_PENALTY

        # Step 11 - pin check: if this move starts down a one-square-wide corridor
        # (for example between a wall and another snake's body), follow it to where
        # it opens out. If an opponent can get into the corridor ahead of us, it can
        # seal us in, so take another way out while we still have one.
        walked = {square}
        current = square
        sealed_in = False
        for steps in range(1, CORRIDOR_LOOKAHEAD + 1):
            onward = [
                n for n in open_neighbours(current, blocked | walked, board_width, board_height)
                if flood_fill(n, blocked | walked, board_width, board_height) >= my_length
            ]
            if len(onward) != 1:
                break   # it opens out (or dead-ends, which the flood fill already punishes)
            current = onward[0]
            walked.add(current)
            our_arrival = steps + 1
            for info in opponent_info:
                their_arrival = info["distances"].get(current)
                if their_arrival is None:
                    continue
                if their_arrival < our_arrival or (
                    their_arrival == our_arrival and info["length"] > length_after
                ):
                    sealed_in = True
            if sealed_in:
                break
        if sealed_in and not escape_found:
            score -= SEALED_CORRIDOR_PENALTY

        distances = distances_from(square, blocked, board_width, board_height)

        # Step 9 - territory: count the squares we would reach before any opponent,
        # so we spread into open space and wall opponents out of it
        territory = 0
        for reachable_square, distance in distances.items():
            if all(distance + 1 < info["distances"].get(reachable_square, 9999)
                   for info in opponent_info):
                territory += 1
        score += (RETREAT_TERRITORY_WEIGHT if retreating else TERRITORY_WEIGHT) * territory

        # Move toward the chosen food, or steer around food when we're at the cap
        if target_food is not None:
            score -= food_weight * distances.get(target_food, board_width + board_height)
        elif avoid_food and square in food_squares:
            score -= AVOID_FOOD_PENALTY

        # Step 12 - food race check: when a same-size or bigger snake will reach a
        # nearby piece of food as soon as we would, closing in is only worth it if
        # we could still back out. Commit when this move leaves a safe, roomy way
        # out other than the food itself; otherwise back off.
        if not starving:
            for food_square in dangerous_food:
                if (my_distances[food_square] <= FOOD_RACE_RANGE
                        and distances.get(food_square, 9999) < my_distances[food_square]):
                    can_back_out = False
                    for exit_square in exits:
                        if exit_square == food_square:
                            continue
                        exit_contested = any(
                            info["length"] >= length_after
                            and info["distances"].get(exit_square, 9999) <= 2
                            for info in opponent_info
                        )
                        if not exit_contested and flood_fill(
                                exit_square, blocked | {square}, board_width, board_height) >= my_length:
                            can_back_out = True
                            break
                    if not can_back_out:
                        score -= FOOD_RACE_PENALTY
                    break

        # Step 13 - hunting
        if HUNT_STYLE == "duel" and in_duel and not hungry:
            # Chase and squeeze the last opponent once we clearly out-length it
            for info in opponent_info:
                if my_length < info["length"] + HUNT_LEAD:
                    continue
                chase = min((distances[o] for o in info["options"] if o in distances), default=None)
                if chase is not None:
                    score -= DUEL_HUNT_WEIGHT * chase
                their_squares = 0
                for their_square, their_distance in info["distances"].items():
                    if their_distance < distances.get(their_square, 9999) + 1:
                        their_squares += 1
                score -= DUEL_SQUEEZE_WEIGHT * their_squares
        elif HUNT_STYLE == "trapper" and hunt_target is not None:
            # Work out how much space this move would leave the hunted snake. The
            # reward is applied after the loop, by comparing our moves with each
            # other. Only moves that keep our own space safe from every snake count.
            territory_after = territory_counts(
                [square] + opponent_heads, [length_after] + opponent_lengths,
                [1] + no_offsets, blocked | {square}, board_width, board_height,
            )
            target_space_after[candidate] = territory_after[hunt_target + 1]
            if roomy and safe_exits >= 1 and territory_after[0] >= my_length:
                flanked = any(
                    info["length"] >= length_after
                    and info["distances"].get(square, 9999) <= FLANK_DISTANCE
                    for i, info in enumerate(opponent_info) if i != hunt_target
                )
                hunt_allowed[candidate] = 0.5 if flanked else 1.0
            else:
                hunt_allowed[candidate] = 0

        scores[candidate] = score

    # "trapper" hunting reward: a move earns it by leaving the hunted snake less
    # space than our least squeezing move would
    if len(target_space_after) > 1:
        most_space_left = max(target_space_after.values())
        for candidate in safe_moves:
            squeeze = most_space_left - target_space_after[candidate]
            scores[candidate] += hunt_allowed[candidate] * min(HUNT_CAP, TRAPPER_HUNT_WEIGHT * squeeze)

    best_score = max(scores.values())
    next_move = random.choice([m for m in safe_moves if scores[m] >= best_score - 0.001])

    print(f"{datetime.now():%H:%M:%S} {game_state['game']['id'][:8]} MOVE {game_state['turn']}: {next_move}")
    
    return {"move": next_move}


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    os.environ.setdefault("PORT", DEFAULT_PORT)
    print(f"Variant: {VARIANT_NAME}")
    run_server({"info": info, "start": start, "move": move, "end": end})
