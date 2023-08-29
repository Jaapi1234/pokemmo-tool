import tkinter as tk
from tkinter import ttk, Toplevel
import json
import requests
import os
import pickle
import threading
from check_which_aoe_moves_pokemon_can_learn import find_aoe_moves, pokemons_that_can_learn_move, aoe_moves_data, \
    format_move, pokemons_locations, pokemon_moves
from PIL import Image, ImageTk, ImageOps

IMAGE_FOLDER = "poke_images"
ITEMS_PER_PAGE = 10
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

with open('to_gen_6_updated.json', 'r') as file:
    data = json.load(file)


def on_closing():
    """Function to run when the window is closing."""
    # Save the current window size and position
    with open("window_size.pkl", "wb") as f:
        size_and_position = root.geometry()
        pickle.dump(size_and_position, f)
    root.destroy()


def get_local_image(name, url):
    filename = os.path.join(IMAGE_FOLDER, f"{name}.png")
    if not os.path.exists(filename):
        with open(filename, 'wb') as f:
            f.write(requests.get(url).content)
    return filename


def padded_image(image_path, target_size=(100, 100), bg_color=(255, 255, 255)):
    img = Image.open(image_path)
    img = ImageOps.pad(img, target_size, color=bg_color)
    return img


def download_all_images(data, progress, status_var, percentage_var):
    total_pokemon = len(data["results"])
    for index, item in enumerate(data["results"], start=1):
        get_local_image(item["name"], item["image"])
        progress["value"] += 1
        status_var.set(f"Downloading {index}/{total_pokemon}")
        percent = (index / total_pokemon) * 100
        percentage_var.set(f"{percent:.2f}%")
        download_root.update_idletasks()
    download_root.quit()


def on_pokemon_click(event):
    clicked_item = canvas.find_withtag(tk.CURRENT)
    if "text" in canvas.gettags(clicked_item):
        pokemon_name = canvas.itemcget(clicked_item, "text")
        aoe_moves = find_aoe_moves(pokemon_name)
        display_aoe_moves_and_occurrences(pokemon_name, aoe_moves)


def on_aoe_move_click(event):
    clicked_item = aoe_moves_canvas.find_withtag(tk.CURRENT)
    if "text" in aoe_moves_canvas.gettags(clicked_item):
        move_name = aoe_moves_canvas.itemcget(clicked_item, "text")
        matching_pokemons = pokemons_that_can_learn_move(move_name)  # Use the function from the previous answer
        display_pokemons_for_aoe_move(move_name, matching_pokemons)


def display_aoe_moves_and_occurrences(pokemon_name, aoe_moves):
    moves_window = Toplevel(root)
    moves_window.title(f"Details for {pokemon_name}")

    # Get the saved window size and position
    window_size_filename = "pokemon_window_size.pkl"
    if os.path.exists(window_size_filename):
        with open(window_size_filename, "rb") as f:
            size_and_position = pickle.load(f)
            moves_window.geometry(size_and_position)

    notebook = ttk.Notebook(moves_window)

    # Tab1: Where to find Pokémon
    find_tab = ttk.Frame(notebook)
    notebook.add(find_tab, text="Where to Find")
    display_pokemon_location(pokemon_name, find_tab)  # Call the function to display location
    moves_tab = ttk.Frame(notebook)
    notebook.add(moves_tab, text="Moves list")
    display_moves_for_pokemon(pokemon_name, moves_tab)
    # Tab2: AoE Moves
    aoe_tab = ttk.Frame(notebook)
    notebook.add(aoe_tab, text="AoE Moves")

    if not aoe_moves:
        label = tk.Label(aoe_tab, text=f"{pokemon_name} can't learn any AoE moves.")
        label.pack(pady=10)
    else:
        label = tk.Label(aoe_tab, text=f"AoE moves that {pokemon_name} can learn:")
        label.pack(pady=10)

        def load_page(page_number):
            for widget in aoe_tab.winfo_children():
                widget.destroy()

            start_index = page_number * ITEMS_PER_PAGE
            end_index = start_index + ITEMS_PER_PAGE
            sorted_moves = sorted(aoe_moves)
            for move in sorted_moves[start_index:end_index]:
                move_label = tk.Label(aoe_tab, text=move)
                move_label.pack()

            if start_index > 0:
                prev_button = tk.Button(aoe_tab, text="Previous", command=lambda: load_page(page_number - 1))
                prev_button.pack(side=tk.LEFT)

            if end_index < len(sorted_moves):
                next_button = tk.Button(aoe_tab, text="Next", command=lambda: load_page(page_number + 1))
                next_button.pack(side=tk.RIGHT)

            page_label = tk.Label(aoe_tab, text=f"Page {page_number + 1}")
            page_label.pack()

        load_page(0)

    def on_moves_window_closing():
        with open(window_size_filename, "wb") as f:
            size_and_position = moves_window.geometry()
            pickle.dump(size_and_position, f)
        moves_window.destroy()

    moves_window.protocol("WM_DELETE_WINDOW", on_moves_window_closing)
    notebook.pack(expand=True, fill=tk.BOTH)


def display_pokemon_location(pokemon_name, parent_tab):
    locations = pokemons_locations(pokemon_name)

    if not locations:
        label = tk.Label(parent_tab, text=f"{pokemon_name} can't be found in any known location.")
        label.pack(pady=10)
    else:
        label = tk.Label(parent_tab, text=f"{pokemon_name} can be found in:")
        label.pack(pady=10)

        # Create a frame to hold the Treeview and Scrollbar
        tree_frame = tk.Frame(parent_tab)
        tree_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Create the Treeview with columns
        tree = ttk.Treeview(tree_frame, columns=('Region', 'Type', 'Location', 'Level', 'Rarity'), show='headings')

        # Set the column headings with initial sorting order
        tree.heading('Region', text='Region', anchor='w', command=lambda col='Region': sort_treeview(tree, col, False))
        tree.heading('Type', text='Type', anchor='w', command=lambda col='Type': sort_treeview(tree, col, False))
        tree.heading('Location', text='Location', anchor='w',
                     command=lambda col='Location': sort_treeview(tree, col, False))
        tree.heading('Level', text='Level', anchor='w', command=lambda col='Level': sort_treeview(tree, col, False))
        tree.heading('Rarity', text='Rarity', anchor='w', command=lambda col='Rarity': sort_treeview(tree, col, False))

        # Set the column widths
        for column in ('Region', 'Type', 'Location', 'Level', 'Rarity'):
            tree.column(column, width=100)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for column in ('Region', 'Type', 'Location', 'Level', 'Rarity'):
            tree.column(column, width=100)

        for region, region_data in locations.items():
            for loc_data in region_data:
                tree.insert("", "end", values=(
                    region, loc_data["Type"], loc_data["Location"], loc_data["Level"], loc_data["Rarity"]))

        # Create the Scrollbar for the Treeview
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scrollbar.set)

        # Use the place geometry manager to position the scrollbar to the right
        tree_scrollbar.place(relx=1.0, rely=0, relheight=1.0, anchor=tk.NE)


def sort_treeview(tree, col, reverse):
    """Function to sort treeview columns."""

    def level_sort_key(item):
        level = item[0].replace("Lv.", "")
        if "-" in level:
            left, right = level.split("-")
            return int(left), int(right)
        else:
            return int(level), int(level)

    items = [(tree.set(child, col), child) for child in tree.get_children('')]

    if col == "Level":
        items.sort(key=level_sort_key, reverse=reverse)
    else:
        items.sort(key=lambda item: item[0].lower(), reverse=reverse)

    for index, (val, child) in enumerate(items):
        tree.move(child, '', index)

    tree.heading(col, command=lambda: sort_treeview(tree, col, not reverse))


def display_pokemons_for_aoe_move(move_name, pokemons):
    moves_window = Toplevel(root)
    moves_window.title(f"Pokémons for {move_name}")

    filtered_pokemons = sorted(pokemons.items(), key=lambda x: x[0].lower())  # Sorting pokemons alphabetically

    def load_page(page_number):
        start_index = page_number * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE

        for widget in moves_window.winfo_children():
            widget.destroy()

        for pokemon, methods in filtered_pokemons[start_index:end_index]:
            methods_str = ", ".join(methods)
            move_frame = tk.Frame(moves_window)
            move_frame.pack(pady=10, padx=10, fill=tk.X)

            image_url = [result["image"] for result in data['results'] if result["name"] == pokemon][0]
            local_image_path = get_local_image(pokemon, image_url)
            poke_image = padded_image(local_image_path, target_size=(50, 50))
            poke_photo = ImageTk.PhotoImage(poke_image)
            image_label = tk.Label(move_frame, image=poke_photo)
            image_label.photo = poke_photo
            image_label.pack(side=tk.LEFT, padx=10)

            move_label = tk.Label(move_frame, text=f"{pokemon} can learn it through: {methods_str}")
            move_label.pack(side=tk.LEFT)

        if start_index > 0:
            prev_button = tk.Button(moves_window, text="Previous", command=lambda: load_page(page_number - 1))
            prev_button.pack(side=tk.LEFT)

        if end_index < len(filtered_pokemons):
            next_button = tk.Button(moves_window, text="Next", command=lambda: load_page(page_number + 1))
            next_button.pack(side=tk.RIGHT)

        page_label = tk.Label(moves_window, text=f"Page {page_number + 1}")
        page_label.pack()

    label = tk.Label(moves_window, text=f"Pokémons that can learn {move_name}:")
    label.pack(pady=10)

    search_frame = ttk.Frame(moves_window)
    search_frame.pack(pady=5)
    search_label = ttk.Label(search_frame, text="Search Pokémon:")
    search_label.pack(side=tk.LEFT)
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var)
    search_entry.pack(side=tk.LEFT, padx=5)

    def filter_pokemons_by_search(search_text):
        nonlocal filtered_pokemons
        filtered_pokemons = [(pokemon, methods) for pokemon, methods in pokemons.items() if
                             search_text.lower() in pokemon.lower()]
        load_page(0)

    search_entry.bind('<KeyRelease>', lambda event: filter_pokemons_by_search(search_var.get()))

    load_page(0)


def list_all_aoe_moves():
    """Lists all AoE moves in the second tab"""
    y_pos = 10
    for move_type, move_list in aoe_moves_data.items():
        for move_name in move_list:
            formatted_move_name = format_move(move_name)
            aoe_moves_canvas.create_text(150, y_pos, text=formatted_move_name, font=("Arial", 12), tags="text")
            y_pos += 50


def filter_pokemons(search_text):
    canvas.delete("all")
    canvas.yview_moveto(0.0)
    y_pos = 10
    for item in data["results"]:
        name = item["name"]
        if search_text.lower() in name.lower():
            local_image_path = get_local_image(name, item["image"])
            poke_image = padded_image(local_image_path)
            poke_photo = ImageTk.PhotoImage(poke_image)
            canvas.create_image(60, y_pos, image=poke_photo, anchor=tk.N)
            canvas.create_text(150, y_pos + 50, text=name, font=("Arial", 12), tags="text")
            y_pos += 120

            if not hasattr(canvas, 'image_list'):
                canvas.image_list = []
            canvas.image_list.append(poke_photo)


def get_initial_geometry():
    """Function to get the saved window geometry."""
    if os.path.exists("window_size.pkl"):
        with open("window_size.pkl", "rb") as f:
            geometry = pickle.load(f)
        return geometry
    return None


# Initial Setup for Image Downloading
if not all(os.path.exists(os.path.join(IMAGE_FOLDER, f"{item['name']}.png")) for item in data["results"]):
    download_root = tk.Tk()
    download_root.title("Downloading Pokémon Images...")
    progress_label = tk.Label(download_root, text="Downloading Pokémon images...")
    progress_label.pack(pady=10)
    progress = ttk.Progressbar(download_root, orient=tk.HORIZONTAL, length=300, mode='determinate')
    progress.pack(pady=20)
    progress["maximum"] = len(data["results"])
    status_var = tk.StringVar()
    status_label = tk.Label(download_root, textvariable=status_var)
    status_label.pack(pady=10)
    percentage_var = tk.StringVar()
    percentage_label = tk.Label(download_root, textvariable=percentage_var)
    percentage_label.pack(pady=10)
    threading.Thread(target=download_all_images, args=(data, progress, status_var, percentage_var)).start()
    download_root.mainloop()
    download_root.destroy()


# Scroll canvas with mousewheel
def _on_canvas_scroll(event):
    canvas.yview_scroll(-1 * (event.delta // 120), "units")  # Scroll the canvas vertically


def display_moves_for_pokemon(pokemon_name, parent_tab):
    def fill_tree(data):
        for move in data["start"]:
            tree.insert("", "end", values=('', 'Start', move))
        for level_move in data["lv"]:
            for level, move in level_move.items():
                tree.insert("", "end", values=(level, 'Level Up', move))
        for move in data["tutor"]:
            tree.insert("", "end", values=('', 'Tutor', move))
        for move in data["tm/hm"]:
            tree.insert("", "end", values=('', 'TM/HM', move))
        for move in data["egg"]:
            tree.insert("", "end", values=('', 'Egg', move))

    def filter_moves(*args):  # added *args to handle the arguments passed by trace
        move_name = filter_var.get()
        # Clear the tree view
        for item in tree.get_children():
            tree.delete(item)

        filtered_data = {}
        for key, value in moves_data.items():
            if key == "lv":  # handle "lv" differently
                filtered_moves = []
                for level_move in value:
                    for level, move in level_move.items():
                        if move_name.lower() in move.lower():
                            filtered_moves.append({level: move})
                filtered_data[key] = filtered_moves
            else:  # for other move types
                filtered_moves = [move for move in value if move_name.lower() in move.lower()]
                filtered_data[key] = filtered_moves

        # Fill the tree with filtered data
        fill_tree(filtered_data)

        # Scroll to the top
        tree.yview_moveto(0)

    # Create a frame to hold the tree and scrollbar
    frame = tk.Frame(parent_tab)
    frame.pack(pady=20, fill=tk.BOTH, expand=True)  # Added pady=20 for empty space above

    # Create a frame for filter input to the right of the tree
    filter_frame = tk.Frame(frame)
    filter_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)  # Added padx for space to the right

    filter_label = tk.Label(filter_frame, text="Filter Moves:")
    filter_label.pack(pady=5)

    filter_var = tk.StringVar()
    filter_entry = tk.Entry(filter_frame, textvariable=filter_var)
    filter_var.trace("w", filter_moves)  # bind filter_moves function to variable updates
    filter_entry.pack(pady=5)
    filter_entry.focus_set()

    tree = ttk.Treeview(frame, columns=('Level', 'Method', 'Move Name'), show='headings')
    tree.pack(fill=tk.BOTH, expand=True)

    # For sorting
    tree["displaycolumns"] = ("Level", "Method", "Move Name")
    for col in tree["displaycolumns"]:
        tree.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tree, _col, False))

    # Create the vertical scrollbar
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Link the scrollbar to the treeview
    tree.configure(yscrollcommand=scrollbar.set)

    moves_data = pokemon_moves(pokemon_name)
    fill_tree(moves_data)

    tree.column('Level', width=100)
    tree.column('Method', width=100)
    tree.column('Move Name', width=150)

    tree.pack(fill=tk.BOTH, expand=True)


def treeview_sort_column(tree, col, reverse):
    # Grab the data in the Treeview
    l = [(tree.set(k, col), k) for k in tree.get_children('')]

    # If the column is 'Level', then customize the sorting
    if col == "Level":
        l.sort(key=lambda t: (t[0] == "", int(t[0]) if t[0].isdigit() else 0), reverse=reverse)
    else:
        l.sort(reverse=reverse)

    # Rearrange items in sorted positions
    for index, (val, k) in enumerate(l):
        tree.move(k, '', index)

    # Reverse sort next time
    tree.heading(col, command=lambda: treeview_sort_column(tree, col, not reverse))


# Main application UI
root = tk.Tk()
root.title("Pokémon Tool")
saved_geometry = get_initial_geometry()
if saved_geometry:
    root.geometry(saved_geometry)
notebook = ttk.Notebook(root)
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
notebook.add(tab1, text="Search Pokémon")
notebook.add(tab2, text="Search by AoE Move")
notebook.pack(expand=True, fill=tk.BOTH)
root.protocol("WM_DELETE_WINDOW", on_closing)

# Tab1 (Search Pokémon)
search_frame = ttk.Frame(tab1)
search_frame.pack(pady=10)
search_label = ttk.Label(search_frame, text="Search Pokémon:")
search_label.pack(side=tk.LEFT)
search_var = tk.StringVar()
search_entry = ttk.Entry(search_frame, textvariable=search_var)
search_entry.pack(side=tk.LEFT, padx=5)
search_entry.bind('<KeyRelease>', lambda event: filter_pokemons(search_var.get()))

# Canvas and Scrollbar for Tab1
canvas = tk.Canvas(tab1, bg='white', scrollregion=(0, 0, 400, len(data["results"]) * 120))
scrollbar = ttk.Scrollbar(tab1, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
canvas.bind('<Button-1>', on_pokemon_click)
canvas.bind('<MouseWheel>', _on_canvas_scroll)

# Tab2 (Search AoE Move)
aoe_moves_canvas = tk.Canvas(tab2, bg='white', scrollregion=(
    0, 0, 400, len(aoe_moves_data) * 50))
aoe_scrollbar = ttk.Scrollbar(tab2, orient="vertical", command=aoe_moves_canvas.yview)
aoe_moves_canvas.configure(yscrollcommand=aoe_scrollbar.set)
aoe_moves_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
aoe_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
aoe_moves_canvas.bind('<Button-1>', on_aoe_move_click)

# Initially load all pokemons and AoE moves
filter_pokemons("")
list_all_aoe_moves()  # Populate the AoE moves list

root.mainloop()
