import json

# Load the JSON data containing AoE moves by type
with open('aoe_moves_by_type.json', 'r', encoding='utf-8') as f:
    aoe_moves_data = json.load(f)

# Load the JSON data containing Pokémon moves
with open('pokes.json', 'r', encoding='utf-8') as f:
    pokemon_moves_data = json.load(f)


def pokemons_locations(pokemon_name):
    lower_pokemon_name = pokemon_name.lower()

    matching_pokemon_keys = [key for key in pokemon_moves_data.keys() if lower_pokemon_name in key.lower()]

    if matching_pokemon_keys:
        where_to_find = pokemon_moves_data[matching_pokemon_keys[0]].get('whereToFind', [])
    else:
        where_to_find = []
    return where_to_find


def pokemon_moves(pokemon_name):
    lower_pokemon_name = pokemon_name.lower()

    matching_pokemon_keys = [key for key in pokemon_moves_data.keys() if lower_pokemon_name in key.lower()]

    if matching_pokemon_keys:
        pokemon_moves = pokemon_moves_data[matching_pokemon_keys[0]]
        if 'whereToFind' in pokemon_moves:
            del pokemon_moves['whereToFind']
    else:
        pokemon_moves = []
    return pokemon_moves


def pokemons_that_can_learn_move(move):
    formatted_move = format_move(move)
    pokemons = {}

    # Load the data from the JSON file
    with open("to_gen_6_updated.json", 'r') as file:
        data = json.load(file)

    results = data.get('results', [])

    for pokemon, moves in pokemon_moves_data.items():
        methods = []

        if formatted_move in [format_move(m) for m in moves.get('start', [])]:
            methods.append("start")

        # Fetch the level when the move is learned
        for level_move in moves.get('lv', []):
            if isinstance(level_move, dict):
                move_name = format_move(level_move[next(iter(level_move))])
                if formatted_move == move_name:
                    level = next(iter(level_move))
                    methods.append(f"level {level}")

        if formatted_move in [format_move(m) for m in moves.get('tutor', [])]:
            methods.append("tutor")

        if formatted_move in [format_move(m) for m in moves.get('tm/hm', [])]:
            methods.append("tm/hm")

        if formatted_move in [format_move(m) for m in moves.get('egg', [])]:
            methods.append("egg")

        if methods:
            for item in results:
                if item["name"].lower() in pokemon.lower():
                    pokemons[item["name"]] = methods
                    break

    return pokemons


def format_move(move):
    # Ensure the move is not None before processing
    if move is None:
        return ""

    # Replace multiple spaces with a single space
    move = ' '.join(move.split())
    # Replace space with a hyphen and convert to lowercase
    move = move.replace(' ', '-').lower()
    return move


def find_aoe_moves(pokemon_name):
    lower_pokemon_name = pokemon_name.lower()

    matching_pokemon_keys = [key for key in pokemon_moves_data.keys() if lower_pokemon_name in key.lower()]

    if matching_pokemon_keys:
        moves = pokemon_moves_data[matching_pokemon_keys[0]]
        aoe_moves = []

        for move_type, move_list in aoe_moves_data.items():
            for move in move_list:
                formatted_move = format_move(move)
                formatted_moves_start = [format_move(m) for m in moves.get('start', [])]
                formatted_moves_lv = {format_move(level_move[level]): level for level_move in moves.get('lv', []) if
                                      isinstance(level_move, dict) for level in level_move}
                formatted_moves_tutor = [format_move(m) for m in moves.get('tutor', [])]
                formatted_moves_tm_hm = [format_move(m) for m in moves.get('tm/hm', [])]
                formatted_moves_egg = [format_move(m) for m in moves.get('egg', [])]

                if formatted_move in formatted_moves_start:
                    aoe_moves.append(formatted_move + " on start")
                if formatted_move in formatted_moves_lv:
                    aoe_moves.append(f"{formatted_move} on level {formatted_moves_lv[formatted_move]}")
                if formatted_move in formatted_moves_tutor:
                    aoe_moves.append(formatted_move + " by tutor")
                if formatted_move in formatted_moves_tm_hm:
                    aoe_moves.append(formatted_move + " by tm/hm")
                if formatted_move in formatted_moves_egg:
                    aoe_moves.append(formatted_move + " as an egg")

        return aoe_moves
    else:
        return []


if __name__ == "__main__":
    pokemon_name_input = input("Enter the Pokémon name: ")

    # Find AoE moves for the input Pokémon
    aoe_moves = find_aoe_moves(pokemon_name_input)

    if not aoe_moves:
        print(f"Error: {pokemon_name_input} not found in the data.")
    else:
        if aoe_moves:
            print(f"AoE moves that {pokemon_name_input} can learn:")
            for move in aoe_moves:
                print(move)
        else:
            print(f"{pokemon_name_input} can't learn any AoE moves.")
