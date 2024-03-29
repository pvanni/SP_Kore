#%%writefile starter.py

from kaggle_environments.envs.kore_fleets.helpers import *
from kaggle_environments.envs.kore_fleets.kore_fleets import get_shortest_flight_path_between
from kaggle_environments.envs.kore_fleets.kore_fleets import get_closest_enemy_shipyard
from kaggle_environments.helpers import *
from random import randint
import math
import copy

#####################################################################################
##      INTERCEPTOR FUNCTIONS AND CLASSES START
#####################################################################################
#
#   Brief           Contains intercept_calculator function output object.
#
class intercept_outcome:
    collision = False       # false for no combat is going to happen. true for combat.
    outcome = 0             # Positive value means that own fleet wins, negative means losing combat

#
#   Brief           Checks if position is out of bounds and wraps it around the kore map
#
#   position        position (position object)
#   return          -
#
def wrap_coordinates(position):
	if position.x > 20:
		position.x = 0
	if position.y > 20:
		position.y = 0
	if position.x < 0:
		position.x = 20
	if position.y < 0:
		position.y = 20

#
#   Brief           Converts flight_plan object to cartesian coordinate list
#
#   flight_plan     flight_plan string
#   position        fleet position (position object)
#   direction       fleet direction, char
#   return          Coordinate list
#
def fplan_to_coordinates(flight_plan, position, direction):
	cartesian_path = []
	fplan = flight_plan
	direct= direction
	pos = position
	idx = 0
	while idx < len(fplan):
		if fplan[idx].isdigit():
			if fplan[idx:idx+2].isdigit():
				steps = int(fplan[idx:idx+2])
				idx+=2
			else:
				steps = int(fplan[idx])
				idx+=1

			j = 0
			while j < steps:
				if direct == 'N':
					pos.y += 1
				elif direct == 'E':
					pos.x += 1
				elif direct == 'S':
					pos.y += -1
				elif direct == 'W':
					pos.x += -1
				wrap_coordinates(pos)
				cartesian_path.append(copy.copy(pos))
				j+=1
		else:
			direct = fplan[idx]
			if direct == 'N':
				pos.y += 1
			elif direct == 'E':
				pos.x += 1
			elif direct == 'S':
				pos.y += -1
			elif direct == 'W':
				pos.x += -1
			wrap_coordinates(pos)
			cartesian_path.append(copy.copy(pos))
			idx+=1
	
	return cartesian_path

#
#   Brief           Checks if two points in board are adjacent
#
#   p1              position object 1, compared to 2
#   p2              position object 2, compared to 1
#   return          True if adjacent
#
def are_points_adjacent(p1, p2):
	tp = p1
	if tp.x == p2.x and tp.y == p2.y:
		return True
	tp = p1
	tp.x += 1
	wrap_coordinates(tp)
	if tp.x == p2.x and tp.y == p2.y:
		return True
	tp = p1
	tp.x += -1
	wrap_coordinates(tp)
	if tp.x == p2.x and tp.y == p2.y:
		return True
	tp = p1
	tp.y += 1
	wrap_coordinates(tp)
	if tp.x == p2.x and tp.y == p2.y:
		return True
	tp = p1
	tp.y += -1
	wrap_coordinates(tp)
	if tp.x == p2.x and tp.y == p2.y:
		return True
	return False

#
#   Brief           Detects collision of two Cartesian coordinate fligth paths
#
#   fplan_coord1    flight_plan cartesian coordinates list 1, compared to 2
#   fplan_coord2    flight_plan cartesian coordinates list 2, compared to 1
#   return          True if collision detected
#
def detect_collision(fplan_coord1, fplan_coord2):
	fc1_len = len(fplan_coord1)
	fc2_len = len(fplan_coord2)

	if fc1_len <= fc2_len:
		loop_count = fc1_len
	else:
		loop_count = fc2_len
	i=0
	while i < loop_count:
		if are_points_adjacent(fplan_coord1[i],fplan_coord2[i]):
			return True
		i+=1
	return False

#
#   Brief           Checks if own and enemy fleets collide in combat. Calculates outcome for this combat.
#
#   own_fleet       Own fleet (fleet object) used in calculation
#   enemy_fleet     Enemy fleet (fleet object) used in calculation
#   return          intercept_outcome object
#
def intercept_calculator(own_fleet, enemy_fleet):
    result = intercept_outcome()
    o_fplan_coord = fplan_to_coordinates(own_fleet.flight_plan, own_fleet.position, own_fleet.direction.to_char())
    e_fplan_coord = fplan_to_coordinates(enemy_fleet.flight_plan, enemy_fleet.position, enemy_fleet.direction.to_char())
    result.collision = detect_collision(o_fplan_coord,e_fplan_coord)
    result.outcome = own_fleet.ship_count - enemy_fleet.ship_count
    return result

#
#   Brief               Loops through all enemy fleets, checks if they will collide with own fleets in winning output.
#                       Then finds new enemy fleets that we could intercept that doesnt collide existing own fleets
#   
#   opponent_fleets     Opponent fleet object list
#   player_fleets       Own fleet object list
#   return              List of enemy fleets that are not intercepted
#
def intercept_scanner(opponent_fleets, player_fleets):
    itc_opportunities = []
    for o_fleet in opponent_fleets:
        intercept_detected = False
        for p_fleet in player_fleets:
            itc = intercept_calculator(p_fleet,o_fleet)
            if itc.collision:
                intercept_detected = True
                break
        if intercept_detected == False:
            # New intercept opportunity detected. Push to list
            itc_opportunities.append(o_fleet)

    return itc_opportunities
#####################################################################################
##      INTERCEPTOR FUNCTIONS AND CLASSES END
#####################################################################################

def agent(obs, config):
    board = Board(obs, config)
    me = board.current_player
    turn = board.step
    spawn_cost = board.configuration.spawn_cost
    kore_left = me.kore

    def meno_paluu_matka(a_point, b_point):
        meno = get_shortest_flight_path_between(a_point, b_point, board.configuration.size, trailing_digits=True)
        paluu = get_shortest_flight_path_between(b_point, a_point, board.configuration.size, trailing_digits=False)
        return meno + paluu

    def parse_path(path):
        new_path = []
        for kirjain in path:
            new_path.append(kirjain)

        final_path = []
        while len(new_path) > 0:
            kirjain = new_path.pop(0)
            if kirjain.isdigit():
                if len(new_path) != 0:
                    if new_path[0].isdigit():
                        final_path.append(kirjain + new_path.pop(0))
                    else:
                        final_path.append(kirjain)
                else:
                    final_path.append(kirjain)
            else:
                final_path.append(kirjain)

        return final_path

    def sum_core_on_path(start_point, path, all_cells, defense=False):
        # defense is the single letter air direction the fleet is facing
        # Parse through all points on the way
        # X vertical, Y horizontal
        current_position = [start_point[0], start_point[1]]

        if defense:
            path = defense + path
            if defense == 'N':
                current_position[1] = current_position[1] - 1
            elif defense == 'E':
                current_position[0] = current_position[0] - 1
            elif defense == 'S':
                current_position[1] = current_position[1] + 1
            elif defense == 'W':
                current_position[0] = current_position[0] + 1

        parsed_path = parse_path(path)
        core_sum = 0
        total_mining_moves = 0
        point_list = []
        last_direction = None
        # Kulje polkua ja laske koret yhteen
        while len(parsed_path) > 0:
            askel = parsed_path.pop(0)
            last_direction = askel
            if askel == 'N':
                current_position[1] = current_position[1] + 1
            elif askel == 'E':
                current_position[0] = current_position[0] + 1
            elif askel == 'S':
                current_position[1] = current_position[1] - 1
            elif askel == 'W':
                current_position[0] = current_position[0] - 1

            # Check if we went over or under 20 or 0
            if current_position[0] == -1:
                current_position[0] = 20
            elif current_position[0] == 21:
                current_position[0] = 0

            if current_position[1] == -1:
                current_position[1] = 20
            elif current_position[1] == 21:
                current_position[1] = 0

            # Laske solun koret yhteen
            solu = all_cells[(current_position[0], current_position[1])]
            core_sum += solu.kore
            total_mining_moves += 1
            point_list.append(Point(x=current_position[0], y=current_position[1]))

            if len(parsed_path) != 0:
                if parsed_path[0].isdigit():
                    askel2 = parsed_path.pop(0)
                    for i in range(int(askel2)):
                        if askel == 'N':
                            current_position[1] = current_position[1] + 1
                        elif askel == 'E':
                            current_position[0] = current_position[0] + 1
                        elif askel == 'S':
                            current_position[1] = current_position[1] - 1
                        elif askel == 'W':
                            current_position[0] = current_position[0] - 1

                        # Check if we went over or under 20 or 0
                        if current_position[0] == -1:
                            current_position[0] = 20
                        elif current_position[0] == 21:
                            current_position[0] = 0

                        if current_position[1] == -1:
                            current_position[1] = 20
                        elif current_position[1] == 21:
                            current_position[1] = 0
                        # Laske solun koret yhteen
                        solu = all_cells[(current_position[0], current_position[1])]
                        core_sum += solu.kore
                        total_mining_moves += 1
                        point_list.append(Point(x=current_position[0], y=current_position[1]))

        if not defense:
            while current_position != start_point:
                if last_direction == 'N':
                    current_position[1] = current_position[1] + 1
                elif last_direction == 'E':
                    current_position[0] = current_position[0] + 1
                elif last_direction == 'S':
                    current_position[1] = current_position[1] - 1
                elif last_direction == 'W':
                    current_position[0] = current_position[0] - 1

                # Check if we went over or under 20 or 0
                if current_position[0] == -1:
                    current_position[0] = 20
                elif current_position[0] == 21:
                    current_position[0] = 0

                if current_position[1] == -1:
                    current_position[1] = 20
                elif current_position[1] == 21:
                    current_position[1] = 0

                if current_position == start_point:
                    break
                solu = all_cells[(current_position[0], current_position[1])]
                core_sum += solu.kore
                total_mining_moves += 1

        # Laske myös kaikki pisteet kun flight plan loppuu
        if defense:
            i = 0
            loop_start = [current_position[0], current_position[1]]
            while i < 20:
                if last_direction == 'N':
                    current_position[1] = current_position[1] + 1
                elif last_direction == 'E':
                    current_position[0] = current_position[0] + 1
                elif last_direction == 'S':
                    current_position[1] = current_position[1] - 1
                elif last_direction == 'W':
                    current_position[0] = current_position[0] - 1

                # Check if we went over or under 20 or 0
                if current_position[0] == -1:
                    current_position[0] = 20
                elif current_position[0] == 21:
                    current_position[0] = 0

                if current_position[1] == -1:
                    current_position[1] = 20
                elif current_position[1] == 21:
                    current_position[1] = 0

                point_list.append(Point(x=current_position[0], y=current_position[1]))
                i += 1
            return point_list

        if core_sum != 0:
            return core_sum / total_mining_moves
        return core_sum

    def find_optimal_route(shipyard, ship_count, max_distance):
        # self._cells: Dict[Point, Cell] = {}
        ship_x = shipyard._position.x
        ship_y = shipyard._position.y
        shipyard_position = [ship_x, ship_y]

        all_cells = board.cells

        target_list = []
        distance_list = []
        path_list = []
        kore_sum_list = []
        for i in range(0, 21):
            for j in range(0, 21):
                ij_point = Point(x=i, y=j)
                target_list.append([i, j])
                distance_list.append(shipyard._position.distance_to(ij_point, board.configuration.size))
                path = meno_paluu_matka(shipyard._position, ij_point)
                path_list.append(path)
                kore_sum_list.append(sum_core_on_path(shipyard_position, path, all_cells))

        # maximum length:
        max_word_length = math.floor(2 * math.log(ship_count)) + 1

        max_kore_sum = 0
        paras_index = 0
        for i in range(0, len(target_list)):
            if len(path_list[i]) > max_word_length:
                continue

            if max_distance < distance_list[i]:
                # print(distance_list[i])
                continue

            if kore_sum_list[i] > max_kore_sum:
                max_kore_sum = kore_sum_list[i]
                paras_index = i
        # print(target_list[paras_index])
        # print(kore_sum_list[paras_index])
        return path_list[paras_index]

    def build(shipyard):

        if shipyard.ship_count >= 50:
            # Määritä kohde
            suitable_spot = False
            new_base = None
            n_fail = 0
            while not suitable_spot:
                n_fail += 1
                if n_fail == 100:
                    spawn_ships(shipyard, kore_left, spawn_cost)
                    return

                i, j = random.randint(0, 20), random.randint(0, 20)
                ij_point = Point(x=i, y=j)
                if ij_point.distance_to(shipyard._position, board.configuration.size) > 6:
                    continue

                min_dist = 100000
                closest_shipyard = None
                for any_shipyard in board.shipyards.values():
                    dist = ij_point.distance_to(any_shipyard._position, board.configuration.size)

                    if dist < min_dist:
                        min_dist = dist
                if min_dist < 5:
                    continue
                new_base = ij_point
                suitable_spot = True

            new_base_matka = get_shortest_flight_path_between(shipyard._position, new_base, board.configuration.size,
                                                              trailing_digits=True)
            action = ShipyardAction.launch_fleet_with_flight_plan(50, new_base_matka + 'C')
            shipyard.next_action = action
            return True
        else:
            return False

    def do_we_attack(shipyard):
        try:
            closest_enemy = get_closest_enemy_shipyard(board, shipyard._position, me)
            if shipyard.ship_count >= 100:
                route = get_shortest_flight_path_between(shipyard._position, closest_enemy._position,
                                                         board.configuration.size, trailing_digits=False)
                # print(f'{turn} attack1: route:{route} size: {shipyard.ship_count}')
                action = ShipyardAction.launch_fleet_with_flight_plan(shipyard.ship_count, route)
                shipyard.next_action = action
                return True
            elif shipyard._position.distance_to(closest_enemy._position, board.configuration.size) <= 7:
                if closest_enemy.ship_count < shipyard.ship_count:
                    if shipyard.ship_count >= 20:
                        route = get_shortest_flight_path_between(shipyard._position, closest_enemy._position,
                                                                 board.configuration.size, trailing_digits=False)
                        print(f'{turn} attack2: route:{route} size: {shipyard.ship_count}')
                        action = ShipyardAction.launch_fleet_with_flight_plan(shipyard.ship_count, route)
                        shipyard.next_action = action
                        return True
        except:
            return False

    def send_help_to_friend(shipyard, shipyards_under_attack):
        # Is any enemy fleet attacking target that I can help or needs help?
        all_cells = board.cells
        for point in shipyards_under_attack:
            if shipyard._position != point:
                if shipyard._position.distance_to(point, board.configuration.size) < shipyards_under_attack[point][2]:
                    # Enough help to defeat enemy
                    n_send = shipyards_under_attack[point][1] - shipyards_under_attack[point][0].ship_count

                    # Shipyard dont need help
                    if n_send <= 1:
                        return
                    path = get_shortest_flight_path_between(shipyard._position, point, board.configuration.size,
                                                            trailing_digits=False)

                    while n_send < shipyard.ship_count:
                        if len(path) < math.floor(2 * math.log(n_send)) + 1:
                            n_send += 1
                        else:
                            break

                    # Send help and return
                    # Pystyykö lähettään tämän kokoisen saattueen
                    if len(path) <= math.floor(2 * math.log(n_send)) + 1:
                        if n_send <= shipyard.ship_count:
                            print(f'{turn} help: route:{path} size: {n_send}')
                            action = ShipyardAction.launch_fleet_with_flight_plan(n_send, path)
                            shipyard.next_action = action
                            return True
                        else:
                            if shipyard.ship_count > 1:
                                if len(path) <= math.floor(2 * math.log(shipyard.ship_count)) + 1:
                                    print(f'{turn} help2: route:{path} size: {n_send}')
                                    action = ShipyardAction.launch_fleet_with_flight_plan(shipyard.ship_count, path)
                                    shipyard.next_action = action
                                    return True
        # Did not find anyone to help
        return False

    def gather_enemy_fleet_information(fleets):
        # Go through each fleet and calculate their trajectory
        # board.fleets.values()
        all_paths = []
        all_fleet_sizes = []
        all_cells = board.cells
        found_c = None
        found_own_c = None

        # how many enemy shipyards
        n_enemy_shipyards = 0
        for any_shipyard in board.shipyards.values():
            if any_shipyard.player_id == me.id:
                continue
            n_enemy_shipyards += 1

        for fleet in fleets:
            if fleet.player_id == me.id:
                if 'C' in fleet.flight_plan:
                    found_own_c = True
                continue

            # Gather all points in a list the fleet will traverse without accounting that it will hit something
            if 'C' in fleet.flight_plan:
                found_c = True
            fleet_path_points = sum_core_on_path([fleet._position.x, fleet._position.y], fleet.flight_plan, board.cells,
                                                 defense=fleet.direction.to_char())
            all_paths.append(fleet_path_points)
            all_fleet_sizes.append(fleet.ship_count)

        shipyards_under_attack = {}
        for path_points, fleet_size in zip(all_paths, all_fleet_sizes):
            for i, point in enumerate(path_points):
                cell = all_cells[point]
                if cell.shipyard:
                    if cell.shipyard.player_id != me.id:
                        break
                    if cell.shipyard.player_id == me.id:
                        if point in shipyards_under_attack:
                            # shipyard is under attack
                            shipyards_under_attack[point][1] += fleet_size
                            if shipyards_under_attack[point][2] > i + 1:
                                shipyards_under_attack[point][2] = i + 1
                        else:
                            shipyards_under_attack[point] = [cell.shipyard, fleet_size + 1, i + 1]
                        break

        return shipyards_under_attack, found_c, found_own_c, n_enemy_shipyards

    def spawn_ships(shipyard, kore_left, spawn_cost):
        if kore_left > spawn_cost * shipyard.max_spawn:
            action = ShipyardAction.spawn_ships(shipyard.max_spawn)
            shipyard.next_action = action
            kore_left -= spawn_cost * shipyard.max_spawn
            return True
        elif kore_left > spawn_cost:
            action = ShipyardAction.spawn_ships(1)
            shipyard.next_action = action
            kore_left -= spawn_cost
            return True

    def mine_and_build(shipyard, ship_count, max_distance, ship_defense_n=0):

        shipyard_ship_n = shipyard.ship_count - ship_defense_n
        if shipyard_ship_n >= 21:
            optimal_route = find_optimal_route(shipyard, 21, max_distance)
            print(f'{turn} mine_and_build1: route:{optimal_route} size: {21} {shipyard.ship_count}')
            action = ShipyardAction.launch_fleet_with_flight_plan(21, optimal_route)
            shipyard.next_action = action
            return True
        elif shipyard_ship_n < 21 and shipyard_ship_n > 2 and kore_left < spawn_cost * shipyard.max_spawn:
            optimal_route = find_optimal_route(shipyard, shipyard_ship_n, max_distance)
            print(f'{turn} mine_and_build2: route:{optimal_route} size: {shipyard_ship_n}')
            action = ShipyardAction.launch_fleet_with_flight_plan(shipyard_ship_n, optimal_route)
            shipyard.next_action = action
            return True

        return False

    def under_attack(shipyard, shipyards_under_attack):

        if shipyard._position in shipyards_under_attack:
            if mine_and_build(shipyard, ship_count, 5, shipyards_under_attack[shipyard._position][1]):
                return True
            elif spawn_ships(shipyard, kore_left, spawn_cost):
                return True
            return True
        else:
            return False

    # Defense info
    shipyards_under_attack, found_c, found_own_c, n_enemy = gather_enemy_fleet_information(board.fleets.values())

    we_have_built_a_new_shipyard = False
    if found_own_c:
        we_have_built_a_new_shipyard = True

    # Kuinka monta shippiä kentällä
    ship_count = 0
    for fleet in me.fleets:
        ship_count += fleet.ship_count

    for shipyard in me.shipyards:
        ship_count += shipyard.ship_count

    # if you have 75 ships wait for everything and expand
    if len(me.shipyards) == 1:
        # how many enemy shipyards
        for shipyard in me.shipyards:
            if ship_count >= 75:
                if under_attack(shipyard, shipyards_under_attack):
                    continue
                elif shipyard.ship_count > 200:
                    if not we_have_built_a_new_shipyard:
                        build(shipyard)
                elif shipyard.ship_count >= 50:
                    if found_c or n_enemy > len(me.shipyards):
                        if not we_have_built_a_new_shipyard:
                            build(shipyard)
                    else:
                        mine_and_build(shipyard, ship_count, 15)

                elif kore_left > spawn_cost * shipyard.max_spawn:
                    action = ShipyardAction.spawn_ships(shipyard.max_spawn)
                    shipyard.next_action = action
                    kore_left -= spawn_cost * shipyard.max_spawn
                elif kore_left > spawn_cost:
                    action = ShipyardAction.spawn_ships(1)
                    shipyard.next_action = action
                    kore_left -= spawn_cost

                return me.next_actions

            else:
                if under_attack(shipyard, shipyards_under_attack):

                    continue
                elif mine_and_build(shipyard, ship_count, 15):
                    continue
                elif kore_left > spawn_cost * shipyard.max_spawn:
                    action = ShipyardAction.spawn_ships(shipyard.max_spawn)
                    shipyard.next_action = action
                    kore_left -= spawn_cost * shipyard.max_spawn
                elif kore_left > spawn_cost:
                    action = ShipyardAction.spawn_ships(1)
                    shipyard.next_action = action
                    kore_left -= spawn_cost

    for shipyard in me.shipyards:

        # Defense and attack. Always defend before attacking
        if under_attack(shipyard, shipyards_under_attack):
            continue
        elif send_help_to_friend(shipyard, shipyards_under_attack):
            continue
        elif do_we_attack(shipyard):
            continue
        elif turn > 50 and kore_left > 100:
            spawn_ships(shipyard, kore_left, spawn_cost)
        elif found_c or n_enemy > len(me.shipyards):
            if not we_have_built_a_new_shipyard:
                if build(shipyard):
                    we_have_built_a_new_shipyard = True
        elif shipyard._position not in shipyards_under_attack:
            if mine_and_build(shipyard, ship_count, 15):
                continue
        elif kore_left > spawn_cost:
            spawn_ships(shipyard, kore_left, spawn_cost)
            continue

    return me.next_actions