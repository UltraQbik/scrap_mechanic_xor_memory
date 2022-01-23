import os, json, copy


SLASH = '\\' if os.name == 'nt' else '/'
DATA_PATH = os.path.dirname(os.path.abspath(__file__)) + SLASH


id_counter = 1
id_table = {0:{0:{0: 0}}}


LOGIC_GATE_MODES = {
	'and' : 0,
	'or'  : 1,
	'xor' : 2,
	'nand': 3,
	'nor' : 4,
	'xnor': 5
}


BLUEPRINT_BODY = {
	"bodies": [
		{
			"childs": [
				# Blocks here
			]
		}
	],
	"version": 3
}


MEMORY_BLUEPRINT = copy.deepcopy(BLUEPRINT_BODY)


BLOCK_BODY = {
	"color": "22eeee",
	"controller": {
		"active": False,
		"controllers": [
			# {
			# 	"id": 1
			# }
		],
		"id": 0,
		"joints": None,
		"mode": 0
	},
	"pos": {
		"x": 0,
		"y": 0,
		"z": 0
	},
	"shapeId": "9f0f56e8-2c31-4d83-996c-d00a9b296c3f",
	"xaxis": -3,
	"zaxis": -1
}


def generate_logic_block(pos: tuple = (0,0,0), mode: int = 0, color: str = '22eeee') -> dict:
	global id_counter, id_table
	block = copy.deepcopy(BLOCK_BODY)
	block['color'] = color
	block['pos']['x'] = pos[0]
	block['pos']['y'] = pos[1]
	block['pos']['z'] = pos[2]
	block['controller']['mode'] = mode
	block['controller']['id'] = id_counter
	if not id_table.get(pos[0]):
		id_table[pos[0]] = {}
	if not id_table[pos[0]].get(pos[1]):
		id_table[pos[0]][pos[1]] = {}
	if id_table[pos[0]][pos[1]].get(pos[2]):
		raise Exception('Block Interception')
	else:
		id_table[pos[0]][pos[1]][pos[2]] = id_counter
	id_counter += 1
	return block


def append_block(block: dict) -> None:
	global MEMORY_BLUEPRINT
	MEMORY_BLUEPRINT['bodies'][0]['childs'].append(block)


def add_controller(block: dict, id_: int = None) -> dict:
	if id_:
		block['controller']['controllers'].append({ 'id': id_ })
	else:
		block['controller']['controllers'].append({ 'id': block['controller']['id'] })
	return block


def get_block_id(pos: tuple = (0,0,0)) -> int:
	global id_table
	if not id_table.get(pos[0]):
		return None
	if not id_table[pos[0]].get(pos[1]):
		return None
	if not id_table[pos[0]][pos[1]].get(pos[2]):
		return None
	return id_table[pos[0]][pos[1]][pos[2]]


def get_block_index(pos: tuple = (0,0,0)) -> int:
	global MEMORY_BLUEPRINT
	if not (block_id := get_block_id(pos)):
		return -1

	for index, block in enumerate(MEMORY_BLUEPRINT['bodies'][0]['childs']):
		if block_id == block['controller']['id']:
			return index
	return -1


def connect_blocks(start: tuple = (0,0,0), end: tuple = (0,0,0)) -> None:
	if not (get_block_id(start) and get_block_id(start)):
		return None

	start_index = get_block_index(start)
	end_id = get_block_id(end)

	MEMORY_BLUEPRINT['bodies'][0]['childs'][start_index] = add_controller(MEMORY_BLUEPRINT['bodies'][0]['childs'][start_index], end_id)
	

def generate_memory(io_bit_width: int = 8, address_bit_width: int = 4, amount_of_io: int = 1) -> dict:
	global MEMORY_BLUEPRINT

	# generating input layer
	for z in range(amount_of_io):
		for y in range(2 ** address_bit_width):
			for x in range(io_bit_width):
				append_block(generate_logic_block( (x, y, z), LOGIC_GATE_MODES['and'], 'eeeeee' ))
	for z in range(amount_of_io):
		for x in range(io_bit_width):
			append_block(generate_logic_block( (x, -1, z), LOGIC_GATE_MODES['or'], 'eeeeee' ))
		for x in range(io_bit_width):
			append_block(generate_logic_block( (x, -2, z), LOGIC_GATE_MODES['and'], 'ffffff' ))

	# generating middle layer
	for y in range(2 ** address_bit_width):
		for x in range(io_bit_width):
			append_block(add_controller(generate_logic_block( (x, y, amount_of_io), LOGIC_GATE_MODES['xor'], '2222ee' )))

	# generating output layer
	for z in range(amount_of_io):
		for y in range(2 ** address_bit_width):
			for x in range(io_bit_width):
				append_block(generate_logic_block( (x, y, amount_of_io + z + 1), LOGIC_GATE_MODES['and'], '222222' ))
	for z in range(amount_of_io):
		for x in range(io_bit_width):
			append_block(generate_logic_block( (x, -2, amount_of_io + z + 1), LOGIC_GATE_MODES['or'], '22ee22' ))
		for x in range(io_bit_width):
			append_block(generate_logic_block( (x, -1, amount_of_io + z + 1), LOGIC_GATE_MODES['and'], '222222' ))

	# generating control blocks
	for z in range(amount_of_io):
		append_block(generate_logic_block( (io_bit_width, -2, z), LOGIC_GATE_MODES['or'], '0000ff' ))
		append_block(generate_logic_block( (io_bit_width, -1, z), LOGIC_GATE_MODES['or'], '222222' ))

	# parts of the decoder
	for z in range(amount_of_io):
		for y in range(2 ** address_bit_width):
			append_block(generate_logic_block( (io_bit_width, y, amount_of_io + z + 1), LOGIC_GATE_MODES['and'], 'eeee22' ))
	for z in range(amount_of_io):
		for x in range(address_bit_width):
			append_block(generate_logic_block( (io_bit_width + x + 1, -2, z), LOGIC_GATE_MODES['or'], 'ffff00' ))
			append_block(generate_logic_block( (io_bit_width + x + 1, -1, z), LOGIC_GATE_MODES['nor'], '222222' ))


	# connecting input and middle layers
	for z in range(amount_of_io):
		for y in range(2 ** address_bit_width):
			for x in range(io_bit_width):
				connect_blocks((x, y, z), (x, y, amount_of_io))

	# connecting middle and output layers
	for z in range(amount_of_io):
		for y in range(2 ** address_bit_width):
			for x in range(io_bit_width):
				connect_blocks((x, y, amount_of_io), (x, y, amount_of_io + z + 1))

	# connecting main input to inputs of cells
	for z in range(amount_of_io):
		for y in range(2 ** address_bit_width):
			for x in range(io_bit_width):
				connect_blocks((x, -1, z), (x, y, z))

	# connecting inputs
	for z in range(amount_of_io):
		for x in range(io_bit_width):
			connect_blocks((x, -2, z), (x, -1, z))

	# connecting outputs of cells to main output
	for z in range(amount_of_io):
		for y in range(2 ** address_bit_width):
			for x in range(io_bit_width):
				connect_blocks((x, y, amount_of_io + z + 1), (x, -2, amount_of_io + z + 1))

	# making loop
	for z in range(amount_of_io):
		for x in range(io_bit_width):
			connect_blocks((x, -1, amount_of_io + z + 1), (x, -1, z))
		for x in range(io_bit_width):
			connect_blocks((x, -2, amount_of_io + z + 1), (x, -1, amount_of_io + z + 1))

	# connecting decoder to inputs/outputs of cells
	for z in range(amount_of_io):
		for y in range(2 ** address_bit_width):
			for x in range(io_bit_width):
				connect_blocks((io_bit_width, y, amount_of_io + z + 1), (x, y, z)) # inputs
				connect_blocks((io_bit_width, y, amount_of_io + z + 1), (x, y, amount_of_io + z + 1)) # outputs

	# connecting control blocks
	for z in range(amount_of_io):
		for x in range(io_bit_width):
			connect_blocks((io_bit_width, -2, z), (x, -1, amount_of_io + z + 1))
			connect_blocks((io_bit_width, -1, z), (x, -2, z))
		connect_blocks((io_bit_width, -2, z), (io_bit_width, -1, z)) # set signals

		for x in range(address_bit_width):
			connect_blocks((io_bit_width + x + 1, -2, z), (io_bit_width + x + 1, -1, z))

	# connecting decoder
	for z in range(amount_of_io):
		for x in range(address_bit_width):
			for y in range(2 ** address_bit_width):
				if y & (2 ** (address_bit_width - x - 1)) == 0:
					connect_blocks((io_bit_width + x + 1, -1, z), (io_bit_width, y, amount_of_io + z + 1))
				else:
					connect_blocks((io_bit_width + x + 1, -2, z), (io_bit_width, y, amount_of_io + z + 1))


	return MEMORY_BLUEPRINT


with open(DATA_PATH + 'blueprint.json', 'w') as file:
	file.write(json.dumps(generate_memory(int(input('input/output bit width: ')), int(input('address bit width: ')), int(input('amount of inputs/outputs: ')))))
