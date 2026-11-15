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
import random
import typing


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


# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    print("INFO")

    return {
        "apiversion": "1",
        "author": "wright",  # TODO: Your Battlesnake Username
        "color": "#D01A1A",  # TODO: Choose color
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
    for snake in game_state['board']['snakes']:
        for direction, square in next_squares.items():
            if square in snake["body"]:
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

    # "Hungry" means health is low enough that we must eat now, allowing for the
    # time it takes to travel to the nearest food
    nearest_food_distance = min((my_distances[square] for square in reachable_food), default=0)
    hungry = you["health"] < max(HUNGRY_HEALTH, nearest_food_distance * 2 + 10)

    # Only go after food when we still want to grow, or when we need the health
    target_food = None
    if hungry or not at_growth_cap:
        if winnable_food:
            target_food = min(winnable_food, key=lambda square: my_distances[square])
        elif reachable_food:
            # Every piece is contested - go for the closest anyway
            target_food = min(reachable_food, key=lambda square: my_distances[square])

    food_weight = HUNGRY_FOOD_WEIGHT if hungry else GROWING_FOOD_WEIGHT
    avoid_food = at_growth_cap and not hungry
    food_squares = {(piece["x"], piece["y"]) for piece in game_state['board']['food']}

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
        if safe_exits == 0:
            score -= NO_SAFE_EXIT_PENALTY

        distances = distances_from(square, blocked, board_width, board_height)

        # Step 9 - territory: count the squares we would reach before any opponent,
        # so we spread into open space and wall opponents out of it
        territory = 0
        for reachable_square, distance in distances.items():
            if all(distance + 1 < info["distances"].get(reachable_square, 9999)
                   for info in opponent_info):
                territory += 1
        score += TERRITORY_WEIGHT * territory

        # Move toward the chosen food, or steer around food when we're at the cap
        if target_food is not None:
            score -= food_weight * distances.get(target_food, board_width + board_height)
        elif avoid_food and square in food_squares:
            score -= AVOID_FOOD_PENALTY

        scores[candidate] = score

    best_score = max(scores.values())
    next_move = random.choice([m for m in safe_moves if scores[m] >= best_score - 0.001])

    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
