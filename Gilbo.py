# Gilbo RPG API -- Version 0.8.0 #

from abc import ABC, abstractmethod
from random import randint
from enum import IntEnum, auto

# Allow Gilbo to see Dependencies
import sys
sys.path.append('.deps')

# 3rd Party Libraries
import numpy as np
from dispatcher import Signal

# ascii-table.com/ansi-escape-sequences.php
# https://docs.djangoproject.com/en/2.0/topics/signals/#django.contrib.auth.signals.Signal

#
# Events #
#

# Inventory-related
pub_item_obtained = Signal(providing_args=["itms"])

# Entity-position-related
pub_chk_pos = Signal()

#
# Common Enumerators #
#


class Enumerators(IntEnum):
    # Stat enums
    base_carry_cap = 100
    carry_cap_modifier = 2
    # Inventory enums
    items_to_modify = 1
    # Attack enums
    base_ammo_cost = 1
    times_attacking = 1


#
# Functions #
#


def write(phrase, type_speed=.040, line_delay=.5):
    from time import sleep
    for i in range(len(phrase)):
        print(phrase[i], end="", flush=True)
        sleep(type_speed)

    sleep(line_delay)
    print('', end=' ')

def clr_console():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


#
# Abstract class from which all enemies, NPCs, and players are derived. #
#


class Locate_Entity(IntEnum):
    mapid = 0
    coordinates = 1
    x_cord = 1
    y_cord = 0


class entity(ABC):
    def __init__(self, name, location, x, y):
        self.entity_dict = {'location': []}
        self.entity_dict['name'] = name
        self.entity_dict.update({'location': [location]})
        self.entity_dict['location'].append([y, x])

    @property
    def name(self):
        return self.entity_dict['name']

    @name.setter
    def name(self, value):
        self.entity_dict['name'] = value

    @property
    def location(self):
        return self.entity_dict['location']

    def set_loc(self, cord, location=None):
        if location is None:
            location = self.location[Locate_Entity.mapid.value]

        self.entity_dict['location'][Locate_Entity.mapid.value] = location
        self.entity_dict['location'][Locate_Entity.coordinates.value] = cord


class NPC(entity):
    def __init__(self, name, location, x, y):
        super().__init__(name, location, x, y)
        self.dialogue_dict = {}

    def add_dialogue(self, diag_name, diag_content):
        self.dialogue_dict[diag_name] = diag_content

    def type_dialogue(self, diag_name):
        for i in range(len(self.dialogue_dict[diag_name])):
            type(self.dialogue_dict[diag_name][i])


class vendor(entity):
    def __init__(self, name, location, x, y, inv, coin):
        super().__init__(name, location, x, y)
        self.entity_dict['inventory'] = inv
        self.entity_dict['currency'] = coin

    @property
    def coin(self):
        return self.entity_dict['currency']

    @coin.setter
    def coin(self, value):
        self.entity_dict['currency'] += value

    @property
    def collection(self):
        return self.entity_dict['inventory']


class battler(vendor):
    def __init__(self, name, location, x, y, inv, coin, stats):
        super().__init__(name, location, x, y, inv, coin)
        self.entity_dict['stats'] = stats
        self.Error_Incorrect_Inventory = 'Incorrect inventory class.'

    @property
    def stats(self):
        return self.entity_dict['stats']

    @property
    def attacks(self):
        try:
            for i in range(len(self.collection.equipped)):
                if isinstance(self.collection.equipped[i], weapon):
                    return self.collection.equipped[i]
        except AttributeError:
            print(self.Error_Incorrect_Inventory)


class player(battler):
    def __init__(self, name, location, x, y, inv, coin, stats):
        super().__init__(name, location, x, y, inv, coin, stats)

        def handle_chk_pos(sender, **kwargs):
            self.sub_chk_pos(sender, **kwargs)
        self.handle_chk_pos = handle_chk_pos
        pub_chk_pos.connect(handle_chk_pos)

    # @receiver(pub_chk_pos)
    def sub_chk_pos(self, sender, **kwargs):
        sender.player_pos = self.location

#
# Items/Weapons in the game #
#


class Item_Types(IntEnum):
    basic_item = auto()
    basic_equippable = auto()
    weapon = auto()
    armor = auto()


class item_unweighted:
    def __init__(self, name, dscrpt):
        self.item_dict = {}
        self.item_dict['type'] = Item_Types.basic_item
        self.item_dict['name'] = name
        self.item_dict['description'] = dscrpt

    @property
    def type(self):
        return self.item_dict['type']

    @property
    def name(self):
        return self.item_dict['name']

    @property
    def dscrpt(self):
        return self.item_dict['description']


class item_weighted(item_unweighted):
    def __init__(self, name, dscrpt, weight, val):
        super().__init__(name, dscrpt)
        self.item_dict['type'] = Item_Types.basic_item
        self.item_dict['carry_weight'] = weight
        self.item_dict['value'] = val

    @property
    def weight(self):
        return self.item_dict['carry_weight']

    @property
    def value(self):
        return self.item_dict['value']


class equippable(item_weighted):
    def __init__(self, name, dscrpt, weight, val):
        super().__init__(name, dscrpt, weight, val)
        self.item_dict['type'] = Item_Types.basic_equippable

    # The API users will have to define their own equip effect


class weapon(equippable):
    def __init__(self, name, dscrpt, weight, val, dmg, linked_attacks=list()):
        super().__init__(name, dscrpt, weight, val)
        self.item_dict['type'] = Item_Types.weapon
        self.item_dict['wpn_dmg'] = dmg
        self.item_dict['linked_attack_list'] = linked_attacks

        @property
        def attacks(self):
            return self.item_dict['linked_attack_list']


class armor(equippable):
    def __init__(self, name, dscrpt, weight, val, armr):
        super().__init__(name, dscrpt, weight, val)
        self.item_dict['type'] = Item_Types.armor
        self.item_dict['wpn_dmg'] = armr


class heal_item(item_weighted):
    def __init__(self, name, dscrpt, weight, val, heal_amnt):
        super().__init__(name, dscrpt, weight, val)
        self.item_dict['heal_amount'] = heal_amnt
        self.item_dict['type'] = Item_Types.basic_item

#
# Entity Stats #
#


class battler_stats:
    def __init__(self, hp, stren, armr, agil, pwr):
        self.stat_dict = {}
        self.stat_dict['hp'] = hp
        self.stat_dict['strength'] = stren
        self.stat_dict['armor'] = armr
        self.stat_dict['agility'] = agil
        self.stat_dict['power'] = pwr

    @property
    def health(self):
        return self.stat_dict['hp']

    @health.setter
    def health(self, value):
        self.stat_dict['hp'] = value

    @property
    def stren(self):
        return self.stat_dict['strength']

    @stren.setter
    def stren(self, value):
        self.stat_dict['strength'] = value

    @property
    def armor(self):
        return self.stat_dict['armor']

    @armor.setter
    def armor(self, value):
        self.stat_dict['armor'] = value

    @property
    def agility(self):
        return self.stat_dict['agility']

    @agility.setter
    def agility(self, value):
        self.stat_dict['agility'] = value

    @property
    def power(self):
        return self.stat_dict['power']

    @power.setter
    def power(self, value):
        self.stat_dict['power'] = value


class player_stats(battler_stats):
    def __init__(self, hp, stren, armr, agil, pwr):
        super().__init__(hp, stren, armr, agil, pwr)
        self.calc_carry_cap()
        self.stat_dict['overencumbered'] = False

        def handle_item_obtained(sender, **kwargs):
            self.sub_item_obtained(sender, **kwargs)
        self.handle_item_obtained = handle_item_obtained
        pub_item_obtained.connect(handle_item_obtained)

    def calc_carry_cap(self):
        self.stat_dict['carry_capacity'] = Enumerators.base_carry_cap + self.stat_dict['strength'] * Enumerators.carry_cap_modifier

    @property
    def encumbered(self):
        return self.stat_dict['overencumbered']

    @encumbered.setter
    def encumbered(self, value):
        self.stat_dict['overencumbered'] = value
        # WRITE MORE HERE FOR WHAT OVERENCUMBENCE AFFECTS

    @property
    def stren(self):
        return self.stat_dict['strength']

    @stren.setter
    def stren(self, value):
        self.stat_dict['strength'] = value
        self.calc_carry_cap()

    def sub_item_obtained(self, sender, **kwargs):
        total_weight = 0

        for i in range(len(kwargs['items'])):
            total_weight += kwargs['items'][i].weight

        self.calc_carry_cap()

        if total_weight > self.stat_dict['carry_capacity']:
            self.encumbered = True

        del total_weight

#
# Locations #
#


class Directions(IntEnum):
    Up = 11
    Up_Left = 12
    Up_Right = 13
    Left = 22
    Right = 33
    Down = 41
    Down_Left = 42
    Down_Right = 43


class Location_Errors(IntEnum):
    no_exist = 0
    encumbered = 1
    invalid_direction = 2


class Tiles(IntEnum):
    Player = auto()
    Grass = auto()
    Wall = auto()
    Mountain = auto()
    Cave = auto()
    Water = auto()
    Building = auto()
    Lava = auto()
    Dirt = auto()
    Ice = auto()
    Pit = auto()


class location_manager:
    def __init__(self):
        self.xy_dict = {'Errors': []}
        self.xy_dict['Errors'].append("That place doesn't exist.")
        self.xy_dict['Errors'].append("You're carrying too much.")
        self.xy_dict['Errors'].append("You cannot go that way.")
        self.xy_dict['player_location'] = []
        self.xy_dict['auto_load'] = True
        self.xy_dict['current_map'] = None

    @property
    def auto_load_map(self):
        return self.xy_dict['auto_load']

    @auto_load_map.setter
    def auto_load_map(self, value):
        # Allows user to turn off map loading for certain sections of the game
        if value is True or value is False:
            self.xy_dict['auto_load'] = value
        else:
            raise TypeError('Value must be True or False.')

    @property
    def player_pos(self):
        return self.xy_dict['player_location']

    @player_pos.setter
    def player_pos(self, val):
        self.xy_dict['player_location'] = val

    def load_if_player(self, thing):
        if self.auto_load_map is True:
            pub_chk_pos.send(sender=self)
            if isinstance(thing, player):
                self.load_map(self.player_pos[Locate_Entity.mapid])
        else:
            clr_console()

    def move(self, thing, direction):
        # Test for encumberence
        if isinstance(thing.stats, player_collection) and thing.stats.encumbered is True:
            return print(self.xy_dict['Errors'][Location_Errors.encumbered])
        # Insert data collection from map
        if self.chk_boundary(thing.location[Locate_Entity.mapid], direction.value, thing.location[Locate_Entity.coordinates], False) is not False:
            thing.set_loc(self.chk_boundary(thing.location[Locate_Entity.mapid], direction.value, thing.location[Locate_Entity.coordinates], True if isinstance(thing, player) else False, True))
            # Check to see if the map needs to be reloaded
            self.load_if_player(thing)

    def teleport(self, thing, mapid, x, y):
        # Wrap around try just in case the map is mispelled or does not yet exist
        try:
            if isinstance(thing, player) and thing.stats.encumbered is True:
                # Print error if the player is encumbered
                return print(self.xy_dict['Errors'][Location_Errors.encumbered])
            # Insert data collection from map
            # Writeout extra details because the entity is a player
            if mapid.send_data((y, x), True if isinstance(thing, player) else False) is True:
                thing.set_loc([y, x], mapid)
                self.load_if_player(thing)

        except NameError:
            raise NameError('That map does not exist.')

    def chk_boundary(self, mapid, direction, start_loc, is_player, print_errors=False):
        # Update coordinates for direction
        if direction is Directions.Up.value:
            new_loc = [start_loc[Locate_Entity.y_cord] - 1, start_loc[Locate_Entity.x_cord]]
        elif direction is Directions.Down.value:
            new_loc = [start_loc[Locate_Entity.y_cord] + 1, start_loc[Locate_Entity.x_cord]]
        elif direction is Directions.Left.value:
            new_loc = [start_loc[Locate_Entity.y_cord], start_loc[Locate_Entity.x_cord] - 1]
        elif direction is Directions.Right.value:
            new_loc = [start_loc[Locate_Entity.y_cord], start_loc[Locate_Entity.x_cord] + 1]

        try:
            # Test if new coordinate is out of bounds
            mapid.layout[new_loc[Locate_Entity.y_cord], new_loc[Locate_Entity.x_cord]]

            # Check if new coordinate is negative
            for i in new_loc:
                if i < 0:
                    if print_errors is True:
                        print(self.xy_dict['Errors'][Location_Errors.invalid_direction])

                    return start_loc

            # Check against the mapid's send_data method to see what it wants the location manager to do
            if mapid.send_data(tuple(new_loc), True if is_player is True else False) is True:
                return new_loc
            else:
                return False

        except IndexError:
            if print_errors is True:
                # Tell the user that it cannot move that way
                print(self.xy_dict['Errors'][Location_Errors.invalid_direction])

            return start_loc

    def detect_tile(self, til, player_til=False):
            from colorama import Fore, Back, Style
            value = ''

            # Set the background color to magenta to signify that the player is there
            if player_til is True:
                value += Back.MAGENTA

            # Set unicode value of character based on Enum value
            if til == Tiles.Grass.value:
                value += Fore.GREEN + Style.BRIGHT + '\u26B6' + Style.RESET_ALL
            elif til == Tiles.Wall.value:
                value += Fore.WHITE + Style.DIM + '\u26DD' + Style.RESET_ALL
            elif til == Tiles.Mountain.value:
                value += Fore.YELLOW + '\u1A12' + Style.RESET_ALL
            elif til == Tiles.Cave.value:
                value += Fore.YELLOW + '\u1A0A' + Style.RESET_ALL
            elif til == Tiles.Water.value:
                value += Fore.CYAN + '\u2307' + Style.RESET_ALL
            elif til == Tiles.Building.value:
                value += Fore.WHITE + '\u16A5' + Style.RESET_ALL
            elif til == Tiles.Lava.value:
                value += Fore.RED + Style.BRIGHT + '\u26C6' + Style.RESET_ALL
            elif til == Tiles.Dirt.value:
                value += Fore.YELLOW + Style.BRIGHT + '\u26C6' + Style.RESET_ALL
            elif til == Tiles.Ice.value:
                value += Fore.CYAN + Style.BRIGHT + '\u26C6' + Style.RESET_ALL
            elif til == Tiles.Pit.value:
                value += Fore.BLACK + Style.DIM + '\u25CF' + Style.RESET_ALL

            return value

    def load_map(self, mapid, rows=None, clmns=None):
        clr_console()

        # Get player position through event
        pub_chk_pos.send(sender=self)

        # Auto generate columns and rows if they are not provided
        if clmns is None:
            clmns = mapid.layout.shape[1]

        if rows is None:
            rows = mapid.layout.shape[0]

        # Loop through rows and columns to send each one to the detect_tile method
        for y in range(rows):
            for x in range(clmns):
                # Test for player position against tile
                if ([y, x] == self.player_pos[Locate_Entity.coordinates]) and (mapid is self.player_pos[Locate_Entity.mapid]):
                    print(self.detect_tile(mapid.layout[y, x], True), end=' ')
                else:
                    print(self.detect_tile(mapid.layout[y, x]), end=' ')

            print()

        # Update the current mapid
        self.xy_dict['current_map'] = mapid


class matrix_map:
    def __init__(self, name):
        self.map_dict = {}
        self.map_dict['map_id'] = name
        self.map_dict['map_layout'] = None

    @abstractmethod
    def send_data(self, til, plyr=False):
        raise NotImplementedError('Please define this method.')
        # TEMPLATE #
        #
        # import os
        # os.system('cls' if os.name == 'nt' else 'clear')
        #
        # if til == [0, 1]:
        #     if plyr is True:
        #         print('You walk forward, and see a massive tree. You step closer.')
        #     return True
        # elif til == [0, 2]:
        #     if player is True:
        #         print('A wide river halts your progress down this path.')
        #     return False

    def chk_tile_val(self, tile, to_match):
            if self.layout[tile[Locate_Entity.y_cord], tile[Locate_Entity.x_cord]] == to_match:
                return True
            else:
                return False


    @property
    def id(self):
        return self.map_dict['map_id']

    @property
    def layout(self):
        return self.map_dict['map_layout']

    @layout.setter
    def layout(self, value):
        assert isinstance(value, np.ndarray)
        self.map_dict['map_layout'] = value

#
# Battle Backend #
#


class attack:
    def __init__(self, dmg, dscrpt, count=Enumerators.times_attacking):
        self.attack_dict = {}
        self.attack_dict['dmg'] = dmg
        self.attack_dict['description'] = dscrpt
        self.attack_dict['hit_count'] = count

    @property
    def dmg(self):
        return self.attack_dict['dmg']

    @property
    def dscrpt(self):
        return self.attack_dict['description']

    @property
    def count(self):
        return self.attack_dict['hit_count']


class ranged_attack(attack):
    def __init__(self, dmg, dscrpt, count, acc, ammo_cost):
        super().__init__(dmg, dscrpt, count)
        self.attack_dict['accuracy'] = acc
        self.attack_dict['ammo_cost'] = ammo_cost

    @property
    def ammo_cost(self):
        return self.attack_dict['ammo_cost']

    @property
    def acc(self):
        return self.attack_dict['accuracy']

#
# Inventory #
#


class item_collection(ABC):
    def __init__(self, items=list()):
        self.items = items

    def add_item(self, itm, amnt=Enumerators.items_to_modify):
        for i in range(amnt):
            self.items.append(itm)

    def rem_item(self, itm, amnt=Enumerators.items_to_modify):
        for i in range(amnt):
            if itm in self.items:
                self.items.remove(itm)
            else:
                print("There is/are no more " + itm.name + " to use, sell, or buy.")

    @property
    def inventory(self):
        return self.items


class vendor_collection(item_collection):
    def __init__(self, items):
        super().__init__(items)
        self.Error_No_Exist = "That item doesn't exist in this inventory."

    def swap_item(self, item, swapee, count=1):
        if item in self.items:
            for i in range(count):
                if swapee.coin >= (item.value * count):
                    swapee.collection.add_item(item)
                    self.rem_item(item)
                    self.coin = item.value
                else:
                    print(swapee.name + " ran out of money.")
        else:
            print(self.Error_No_Exist)


class battler_collection(item_collection):
    def __init__(self, items, equipped=list()):
        super().__init__(items)
        self.on_entity = equipped
        self.Errors = "That didn't work."

    def equip(self, item):
        try:
            if item in self.items:
                for i in range(len(self.on_entity)):
                    if item.__class__ == self.on_entity.__class__:
                        del self.on_entity[i]

            self.on_entity.append(item)

        except AttributeError:
            print(self.Errors)

        @property
        def equipped(self):
            return self.on_entity


class player_collection(battler_collection, vendor_collection):
    def __init__(self, items, equipped):
        super().__init__(items, equipped)

    def add_item(self, itm, amnt=Enumerators.items_to_modify):
        for i in range(amnt):
            self.items.append(itm)

        pub_item_obtained.send(sender=self, itms=self.collectionentory)

#
# Quests #
#


class quest:
    def __init__(self, name):
        # Placeholder
        self.name = name
        pass


#
# Battle System #
#

class battle_manager:
    pass


#
# Tracker #
#

class object_tracker:
    def __init__(self):
        self.one_time_init = 0

    def empty_tracker(self):
        if self.one_time_init != 0:
            self.track_dict.update((key, []) for key in self.track_dict)
        else:
            self.track_dict = {}
            self.one_time_init = 1

    def categ_list(self, globl):
        # check for Gilbo-defined class parents
        try:
            import inspect
            if 'Gilbo' in str(inspect.getfile(globl.__class__)).split('\\')[-1]:
                temp = []
                parents = inspect.getmro(globl.__class__)

                # Append list of matched objects to temporary list
                for i in range(len(parents)):
                    temp_append = str(parents[i]).split("'")[1]
                    try:
                        temp_append = temp_append.split('.')[1]
                    except IndexError:
                        pass
                    temp.append(temp_append)

                # Append globals that match the object to list
                for i in range(len(temp)):
                    try:
                        self.track_dict[temp[i]].append(globl)
                    except KeyError:
                        self.track_dict.update({temp[i]: [globl]})

                del temp

        except TypeError:
            pass

    def update_tracker(self, class_list, spec_search=None):
        self.empty_tracker()

        # Check if user wants to search for a specific item
        if spec_search is None:
            for key in class_list:
                if isinstance(class_list[key], list):
                    for i in range(len(class_list[key])):
                        self.categ_list(class_list[key][i])
                else:
                    self.categ_list(class_list[key])

        else:
            # If the user wants to search for something specifically, begin another process
            store_names = []
            import inspect

            for key in class_list:
                try:
                    if 'Gilbo' in str(inspect.getfile(class_list[key].__class__)).split('\\')[-1]:
                        # Find instances of the searched term
                        if isinstance(class_list[key], spec_search):
                            store_names.append(class_list[key])

                except TypeError:
                    pass

            return store_names

    def read_write_data(self, data_set=[]):
        for i in range(len(data_set)):
            print(data_set[i])

        print('\n')

    def writeout(self, spec_search=None):
        print()
        for i, j in self.tracker.items():
            if spec_search is None:
                self.read_write_data([i, j])
            elif spec_search is not None and str(i) == spec_search:
                self.read_write_data([i, j])

    def save_data(self, obj_list):
        keys = list(obj_list.keys())
        values = list(obj_list.values())

        with open('sav.pickle', 'wb') as handle:
            handle.truncate(0)
            import dill as pickle
            pickle.dump((keys, values), handle)

        del keys, values

    def load_data(self, obj_list):
        with open('sav.pickle', 'rb') as handle:
            import dill as pickle
            keys, values = pickle.load(handle)
            for i in range(len(keys)):
                try:
                    obj_list.update({keys[i]: values[i]})
                except IndexError:
                    print('There were more objects to load than values.')

    @property
    def tracker(self):
        return self.track_dict


tracker = object_tracker()
loc_man = location_manager()
