from kaggle_environments.envs.kore_fleets.helpers import *
from kaggle_environments.envs.kore_fleets.kore_fleets import get_shortest_flight_path_between
from kaggle_environments.envs.kore_fleets.kore_fleets import get_closest_enemy_shipyard
from random import randint
import math


def agent(obs, config):
    board = Board(obs, config)
    me = board.current_player

    me = board.current_player
    turn = board.step
    spawn_cost = board.configuration.spawn_cost
    kore_left = me.kore

    # loop through all shipyards you control
    for shipyard in me.shipyards:
        # build a ship!
        if kore_left >= spawn_cost:
            action = ShipyardAction.spawn_ships(1)
            shipyard.next_action = action

    return me.next_actions