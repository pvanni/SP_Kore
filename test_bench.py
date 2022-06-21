import copy

class position:
  def __init__(self, x, y):
    self.x = x
    self.y = y

def wrap_coordinates(position):
	if position.x > 20:
		position.x = 0
	if position.y > 20:
		position.y = 0
	if position.x < 0:
		position.x = 20
	if position.y < 0:
		position.y = 20

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

fplan1 = '16N4E33'
pos1 = position(0,0)

fplan2 = '16N4E33'
pos2 = position(2,0)

coords1 = fplan_to_coordinates(fplan1,pos1,'N')
coords2 = fplan_to_coordinates(fplan2,pos2,'N')

print(detect_collision(coords1,coords2))