import os
from typing import Any 
from Event import Call, Event
from MAP import MAP, CompressionSet
import numpy as np
import sys
from decimal import Decimal

# la classe Point
# un objet Point représente par sa valeur de gr, ws et pb
class Point:
	def __init__(self, gr:Decimal, ws:Decimal, pb:Decimal) -> None:
		self.gr:Decimal = gr
		self.ws:Decimal = ws
		self.pb:Decimal = pb

	def __hash__(self) -> int:
		return hash(str(self.gr) + str(self.ws) + str(self.pb))

	def __eq__(self, other:object) -> bool:
		return isinstance(other, Point) and abs(self.gr-other.gr) < 0.001 and abs(self.ws-other.ws) < 0.001 and abs(self.pb-other.pb) < 0.001
	
	def __str__(self) -> str:
		return "("+str(self.gr)+", "+str(self.ws)+", "+str(self.pb)+")"

# la classe Cube
# un objet Cube représente un zone rectangle avec deux pointes en diagonale
class Cube:
	def __init__(self, gr_from:Decimal, gr_to:Decimal, ws_from:Decimal, ws_to:Decimal, pb_from:Decimal, pb_to:Decimal) -> None:
		self.gr_from:Decimal = Decimal(gr_from).quantize(Decimal('1.00'))
		self.gr_to:Decimal = Decimal(gr_to).quantize(Decimal('1.00'))
		self.ws_from:Decimal = Decimal(ws_from).quantize(Decimal('1.00'))
		self.ws_to:Decimal = Decimal(ws_to).quantize(Decimal('1.00'))
		self.pb_from:Decimal = Decimal(pb_from).quantize(Decimal('1.00'))
		self.pb_to:Decimal = Decimal(pb_to).quantize(Decimal('1.00'))

	def __hash__(self) -> int:
		return hash(str(self.gr_from) + str(self.gr_to) + str(self.ws_from) + str(self.ws_to) + str(self.pb_from) + str(self.pb_to))

	def __eq__(self, other:object) -> bool:
		return isinstance(other, Cube) and abs(self.gr_from-other.gr_from) < 0.001 and abs(self.gr_to-other.gr_to) < 0.001 and abs(self.ws_from-other.ws_from) < 0.001 and abs(self.ws_to-other.ws_to) < 0.001 and abs(self.pb_from-other.pb_from) < 0.001 and abs(self.pb_to-other.pb_to) < 0.001

global g_exploredMap, g_nbSteps, gr_bounds, ws_bounds, pb_bounds, g_tab_parametersToBestResultPos, g_tab_filledMap

g_nbPoints:int = 11
g_gr_bounds:tuple[Decimal, Decimal] = (Decimal(0).quantize(Decimal('1.00')), Decimal(8).quantize(Decimal('1.00')))
g_ws_bounds:tuple[Decimal, Decimal] = (Decimal(0).quantize(Decimal('1.00')), Decimal(1).quantize(Decimal('1.00')))
g_pb_bounds:tuple[Decimal, Decimal] = (Decimal(0).quantize(Decimal('1.00')), Decimal(1).quantize(Decimal('1.00')))
g_gr_step:Decimal = (g_gr_bounds[1]-g_gr_bounds[0])/(g_nbPoints-1)
g_ws_step:Decimal = (g_ws_bounds[1]-g_ws_bounds[0])/(g_nbPoints-1)
g_pb_step:Decimal = (g_pb_bounds[1]-g_pb_bounds[0])/(g_nbPoints-1)

# Association de la combinaison des paramètre à explorer représentés sous la forme d'une chaine de caractère avec le résultat de la compression pour ces paramètres
g_exploredMap:dict[str, CompressionSet] = {}

# Matrice cubique stockant pour chaque point dans l'espace 3D si le point est une solution ou pas, les valeurs de la matrice peuvent être -1 (Overime), 1 (Egal à solution) ou 2 (Différentd de la solution). Cette matrice peut contenir des trous à savoir des zones non explorées
g_tab_parametersToBestResultPos:np.ndarray[Any, np.dtype[np.float64]]

# Matrice cubique stockant pour chaque point dans l'espace 3D si le point est une solution ou pas, les valeurs de la matrice peuvent être -1 (Overime), 1 (Egal à solution) ou 2 (Différentd de la solution). Contrairement à g_tab_parametersToBestResultPos les espaces entre les points calculés sont ici comblés
g_tab_filledMap:np.ndarray[Any, np.dtype[np.float64]]

# \brief arroundi un nombre à un multiple d'un epsilone
def round_to_multiple(number:Decimal, episilon:Decimal) -> Decimal:
    return Decimal(episilon * round(Decimal(number) / Decimal(episilon)))

# \brief Essayer d'obtenir la solution avec un objet Point, si nous avons déjà eu la solution de ce point nous retournons directement la solution, sinon nous allons exécuter notre algorithme MAP avec les paramètres du point et enregistrer la solution dans un dictionnaire
#
# @point : le point sous la forme d'une combinaison gr/ws/pb à tester
# @trace : la trace à compresser sous la forme d'une chaine de caractère
# @solution : représente la solution de référence sous la forme d'une chaine de caractère.
# @return: retourne la compression associée à ce point
def get_from_map(point:Point, trace:str, solution:str) -> CompressionSet:
	global g_exploredMap, g_tab_parametersToBestResultPos
	gr:Decimal = point.gr
	ws:Decimal = point.ws
	pb:Decimal = point.pb
	#gr = Decimal(0.80).quantize(Decimal('1.00'))
	#ws = Decimal(0.10).quantize(Decimal('1.00'))
	#pb = Decimal(0.20).quantize(Decimal('1.00'))
	# dans le cas les paramètres ne sont plus légitimes
	if(gr<g_gr_bounds[0] or ws<g_ws_bounds[0] or pb<g_pb_bounds[0] or gr>g_gr_bounds[1] or ws>g_ws_bounds[1] or pb>g_pb_bounds[1]):
		raise IndexError
	# si nous avons déjà eu la solution nous la retounons directement
	if str(gr)+str(ws)+str(pb) in g_exploredMap.keys():
		return g_exploredMap[str(gr)+str(ws)+str(pb)]
	# sinon nous faisons l'essaie avec les paramètres du point
	else:
		i:int = round(gr/g_gr_step)
		j:int = round(ws/g_ws_step)
		k:int = round(pb/g_pb_step)
		print("Call MAP with parameters\tgr: "+str(gr)+"   \tws: "+str(ws)+"   \tpb: "+str(pb), end='\r')
		# Fait tourner l'algo de compression sur la trace
		# Transformation du string en une liste d'évènement
		eventList:list[Event] = []
		for char in trace:
			eventList.append(Call(char))
		compressions:CompressionSet = MAP(eventList, float(gr), float(ws), float(pb))

		#print()
		#for c in compressions.set:
		#	print(c)

		g_tab_parametersToBestResultPos[i][j][k]=compressions.getCode(solution)
		#print(solution+" "+str(g_tab_parametersToBestResultPos[i][j][k]))

		# si on a trouvé la solution ne stocker que la solution sinon stocker toutes les compressions explorées
		key:str = str(gr)+str(ws)+str(pb)
		if g_tab_parametersToBestResultPos[i][j][k] == 1:
			g_exploredMap[key] = CompressionSet()
			g_exploredMap[key].set = {solution}
		else:
			g_exploredMap[key] = compressions
		return g_exploredMap[key]

# \brief Compresse les logs contenus dans le fichier "targetFileName" en explorant les paramètres gr, ws et pb de manière dichotomique.
#
# @trace : la trace à compresser sous la forme d'une chaine de caractère
# @solution : représente la solution de référence sous la forme d'une chaine de caractère.
def search_gr_ws_by_rect(trace:str, solution:str) -> None:
	global  g_exploredMap, g_tab_parametersToBestResultPos, g_tab_filledMap
	g_exploredMap = {}
	g_tab_parametersToBestResultPos = np.zeros((g_nbPoints, g_nbPoints, g_nbPoints))
	g_tab_filledMap = np.zeros((g_nbPoints, g_nbPoints, g_nbPoints))

	gr_middle:Decimal = (g_gr_bounds[1]-g_gr_bounds[0])/2
	ws_middle:Decimal = (g_ws_bounds[1]-g_ws_bounds[0])/2
	pb_middle:Decimal = (g_pb_bounds[1]-g_pb_bounds[0])/2

	queue:list[Cube] = []
	queue.append(Cube(g_gr_bounds[0], gr_middle, g_ws_bounds[0], ws_middle, g_pb_bounds[0], pb_middle))
	queue.append(Cube(g_gr_bounds[0], gr_middle, g_ws_bounds[0], ws_middle, pb_middle, g_pb_bounds[1]))
	queue.append(Cube(g_gr_bounds[0], gr_middle, ws_middle, g_ws_bounds[1], g_pb_bounds[0], pb_middle))
	queue.append(Cube(g_gr_bounds[0], gr_middle, ws_middle, g_ws_bounds[1], pb_middle, g_pb_bounds[1]))
	queue.append(Cube(gr_middle, g_gr_bounds[1], g_ws_bounds[0], ws_middle, g_pb_bounds[0], pb_middle))
	queue.append(Cube(gr_middle, g_gr_bounds[1], g_ws_bounds[0], ws_middle, pb_middle, g_pb_bounds[1]))
	queue.append(Cube(gr_middle, g_gr_bounds[1], ws_middle, g_ws_bounds[1], g_pb_bounds[0], pb_middle))
	queue.append(Cube(gr_middle, g_gr_bounds[1], ws_middle, g_ws_bounds[1], pb_middle, g_pb_bounds[1]))
	while(len(queue)>0):
		r = queue.pop(len(queue)-1)
		# Récupération des 8 points à analyser en coordonnées gr, ws et pb
		#     p7--------p8
		#    /|         /|
		#   / |        / |
		#  /  |       /  |  pb 
		# p5--------p6   |   x
		# |   |      |   |   |  x ws
		# |   p3-----|--p4   | /
		# |  /       |  /    |/
		# | /        | /     +------x gr
		# |/         |/
		# p1--------p2
		p1 = Point(r.gr_from, r.ws_from, r.pb_from)
		p2 = Point(r.gr_to, r.ws_from, r.pb_from)
		p3 = Point(r.gr_from, r.ws_to, r.pb_from)
		p4 = Point(r.gr_to, r.ws_to, r.pb_from)
		p5 = Point(r.gr_from, r.ws_from, r.pb_to)
		p6 = Point(r.gr_to, r.ws_from, r.pb_to)
		p7 = Point(r.gr_from, r.ws_to, r.pb_to)
		p8 = Point(r.gr_to, r.ws_to, r.pb_to)
		# calcul des 8 compressions (ou récupération dans la map si déjà calculé)
		sol1 = get_from_map(p1, trace, solution)
		sol2 = get_from_map(p2, trace, solution)
		sol3 = get_from_map(p3, trace, solution)
		sol4 = get_from_map(p4, trace, solution)
		sol5 = get_from_map(p5, trace, solution)
		sol6 = get_from_map(p6, trace, solution)
		sol7 = get_from_map(p7, trace, solution)
		sol8 = get_from_map(p8, trace, solution)
		# calcul des positions intermédiaires
		gr_halfGap = round_to_multiple(abs(p2.gr-p1.gr)/2, g_gr_step)
		ws_halfGap = round_to_multiple(abs(p3.ws-p1.ws)/2, g_ws_step)
		pb_halfGap = round_to_multiple(abs(p5.pb-p1.pb)/2, g_pb_step)
		# si toutes les solution sont égales, il suffit de passer au cube suivant dans la queue
		if (sol1 == sol2 and sol1 == sol3 and sol1 == sol4 and sol1 == sol5 and sol1 == sol6 and sol1 == sol7 and sol1 == sol8):
			code = sol1.getCode(solution)
			i_gr = r.gr_from
			while (i_gr <= r.gr_to):
				i_ws = r.ws_from
				while (i_ws <= r.ws_to):
					i_pb = r.pb_from
					while (i_pb <= r.pb_to):
						g_tab_filledMap[round(i_gr/g_gr_step)][round(i_ws/g_ws_step)][round(i_pb/g_pb_step)] = code
						i_pb += g_pb_step
					i_ws += g_ws_step
				i_gr += g_gr_step
			continue
		#print (str(p1), str(p2), str(p3), str(p4), str(p5), str(p6), str(p7), str(p8))
		# si la face devant est homogène mais différente d'un point en arrière
		if (sol1 == sol2 and sol1 == sol5 and sol1 == sol6 and (sol1 != sol3 or sol2 != sol4 or sol5 != sol7 or sol6 != sol8)):
			# Construction d'un cube pour l'avant
			#     p7--------p8
			#    /|         /|
			#   +----------+ |
			#  /          /| | pb
			# p5--------p6 | |  x
			# |          | | |  |  x ws
			# |          | |p4  | /
			# |          | |/   |/
			# |          | +    +------x gr
			# |          |/
			# p1--------p2
			queue.append(Cube(p1.gr, p2.gr, p1.ws, round_to_multiple(p1.ws + ws_halfGap, g_ws_step), p1.pb, p5.pb))
			#print("F")
		# si la face arrière est homogène mais différente d'un point en avant
		if (sol3 == sol4 and sol3 == sol7 and sol3 == sol8 and (sol1 != sol3 or sol2 != sol4 or sol5 != sol7 or sol6 != sol8)):
			# Construction d'un cube pour l'arrière
			#     p7--------p8
			#    /          /|
			#   +----------+ |
			#  /|         /| | pb
			# p5--------p6 | |  x
			# | |        | | |  |  x ws
			# | |        | |p4  | /
			# | |        | |/   |/
			# | +--------|-+    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(p3.gr, p4.gr, round_to_multiple(p3.ws - ws_halfGap, g_ws_step), p3.ws, p3.pb, p7.pb))
			#print("B")
		# si la face de dessous est homogène mais différente d'un point en dessus
		if (sol1 == sol2 and sol1 == sol3 and sol1 == sol4 and (sol1 != sol5 or sol2 != sol6 or sol3 != sol7 or sol4 != sol8)):
			# Construction d'un cube pour le dessous
			#     p7--------p8
			#    /|         /|
			#   / |        / |
			#  /  +-------/--+ pb
			# p5--------p6  /|  x
			# | /        | / |  |  x ws
			# |/         |/ p4  | /
			# +----------+  /   |/
			# |          | /    +------x gr
			# |          |/
			# p1--------p2
			queue.append(Cube(p1.gr, p2.gr, p1.ws, p3.ws, p1.pb, round_to_multiple(p1.pb + pb_halfGap, g_pb_step)))
			#print("D")
		# si la face de dessus est homogène mais différente d'un point en dessous
		if (sol5 == sol6 and sol5 == sol7 and sol5 == sol8 and (sol1 != sol5 or sol2 != sol6 or sol3 != sol7 or sol4 != sol8)):
			# Construction d'un cube pour le dessus
			#     p7--------p8
			#    /          /|
			#   /          / |
			#  /          /  + pb
			# p5--------p6  /|  x
			# |          | / |  |  x ws
			# |          |/-p4  | /
			# +----------+  /   |/
			# | /        | /    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(p5.gr, p6.gr, p5.ws, p7.ws, round_to_multiple(p5.pb - pb_halfGap, g_pb_step), p5.pb))
			#print("U")
		# si la face de gauche est homogène mais différente d'un point à droite
		if (sol1 == sol3 and sol1 == sol5 and sol1 == sol7 and (sol1 != sol2 or sol3 != sol4 or sol5 != sol6 or sol7 != sol8)):
			# Construction d'un cube pour la gauche
			#     p7---+----p8
			#    /    /|    /|
			#   /    / |   / |
			#  /    /  |  /  | pb
			# p5---+----p6   |  x
			# |    |   | |   |  |  x ws
			# |    |   +-|--p4  | /
			# |    |  /  |  /   |/
			# |    | /   | /    +------x gr
			# |    |/    |/
			# p1---+----p2
			queue.append(Cube(p1.gr, round_to_multiple(p1.gr + gr_halfGap, g_gr_step), p1.ws, p3.ws, p1.pb, p5.pb))
			#print("L")
		# si la face de droite est homogène mais différente d'un point à gauche
		if (sol2 == sol4 and sol2 == sol6 and sol2 == sol8 and (sol1 != sol2 or sol3 != sol4 or sol5 != sol6 or sol7 != sol8)):
			# Construction d'un cube pour la droite
			#     p7----+---p8
			#    /|    /    /|
			#   / |   /    / |
			#  /  |  /    /  | pb
			# p5----+---p6   |  x
			# |   | |    |   |  |  x ws
			# |   p3|    |  p4  | /
			# |  /  |    |  /   |/
			# | /   |    | /    +------x gr
			# |/    |    |/
			# p1----+---p2
			queue.append(Cube(round_to_multiple(p2.gr - gr_halfGap, g_gr_step), p2.gr, p2.ws, p4.ws, p2.pb, p6.pb))
			#print("R")
		# si l'arête avant/bas est homogène mais différente d'un point en dessus et en arrière
		if (sol1 == sol2 and (sol1 != sol3 or sol2 != sol4) and (sol1 != sol5 or sol2 != sol6)):
			# Construction d'un cube en bas devant
			#     p7--------p8
			#    /|         /|
			#   / |        / |
			#  /  |       /  | pb
			# p5--------p6   |  x
			# | +--------|-+ |  |  x ws
			# |/         |/|p4  | /
			# +----------+ |/   |/
			# |          | +    +------x gr
			# |          |/
			# p1--------p2
			queue.append(Cube(p1.gr, p2.gr, p1.ws, round_to_multiple(p1.ws + ws_halfGap, g_ws_step), p1.pb, round_to_multiple(p1.pb + pb_halfGap, g_pb_step)))
			#print("FD")
		# si l'arête arrière/bas est homogène mais différente d'un point en dessus et en avant
		if (sol3 == sol4 and (sol3 != sol7 or sol4 != sol8) and (sol3 != sol1 or sol4 != sol2)):
			# Construction d'un cube en bas devant
			#     p7--------p8
			#    /|         /|
			#   / |        / |
			#  /  +-------/--+ pb
			# p5--------p6  /|  x
			# | +--------|-+ |  |  x ws
			# | |        | |p4  | /
			# | |        | |/   |/
			# | +--------|-+    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(p3.gr, p4.gr, round_to_multiple(p3.ws - ws_halfGap, g_ws_step), p3.ws, p3.pb, round_to_multiple(p3.pb + pb_halfGap, g_pb_step)))
			#print("BD")
		# si l'arête arrière/haut est homogène mais différente d'un point en dessous et en avant
		if (sol7 == sol8 and (sol7 != sol5 or sol8 != sol6) and (sol7 != sol3 or sol8 != sol4)):
			# Construction d'un cube en haut arrière
			#     p7--------p8
			#    /          /|
			#   +----------+ |
			#  /|         /| + pb
			# p5--------p6 |/|  x
			# | +--------|-+ |  |  x ws
			# |   p3-----|--p4  | /
			# |  /       |  /   |/
			# | /        | /    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(p7.gr, p8.gr, round_to_multiple(p7.ws - ws_halfGap, g_ws_step), p7.ws, round_to_multiple(p7.pb - pb_halfGap, g_pb_step), p7.pb))
			#print("BU")
		# si l'arête avant/haut est homogène mais différente d'un point en dessous et en arrière
		if (sol5 == sol6 and (sol5 != sol1 or sol6 != sol2) and (sol5 != sol7 or sol6 != sol8)):
			# Construction d'un cube en haut devant
			#     p7--------p8
			#    /|         /|
			#   +----------+ |
			#  /          /| | pb
			# p5--------p6 | |  x
			# |          | + |  |  x ws
			# |          |/-p4  | /
			# +----------+  /   |/
			# | /        | /    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(p5.gr, p6.gr, p5.ws, round_to_multiple(p5.ws + ws_halfGap, g_ws_step), round_to_multiple(p5.pb - pb_halfGap, g_pb_step), p5.pb))
			#print("FU")
		# si l'arête gauche/bas est homogène mais différente d'un point en dessus et à droite
		if (sol1 == sol3 and (sol1 != sol2 or sol3 != sol4) and (sol1 != sol5 or sol3 != sol7)):
			# Construction d'un cube en bas à gauche
			#     p7--------p8
			#    /|         /|
			#   / |        / |
			#  /  +----+  /  | pb
			# p5--------p6   |  x
			# | /    / | |   |  |  x ws
			# |/    /  +-|--p4  | /
			# +----+  /  |  /   |/
			# |    | /   | /    +------x gr
			# |    |/    |/
			# p1---+----p2
			queue.append(Cube(p1.gr, round_to_multiple(p1.gr + gr_halfGap, g_gr_step), p1.ws, p3.ws, p1.pb, round_to_multiple(p1.pb + pb_halfGap, g_pb_step)))
			#print("LD")
		# si l'arête droite/bas est homogène mais différente d'un point en dessus et à gauche
		if (sol2 == sol4 and (sol1 != sol2 or sol3 != sol4) and (sol2 != sol6 or sol4 != sol8)):
			# Construction d'un cube en bas à droite
			#     p7--------p8
			#    /|         /|
			#   / |        / |
			#  /  |     +-/--+ pb
			# p5--------p6  /|  x
			# |   |   /  | / |  |  x ws
			# |   p3-/   |/ p4  | /
			# |  /  +----+  /   |/
			# | /   |    | /    +------x gr
			# |/    |    |/
			# p1----+---p2
			queue.append(Cube(round_to_multiple(p2.gr - gr_halfGap, g_gr_step), p2.gr, p2.ws, p4.ws, p2.pb, round_to_multiple(p2.pb + pb_halfGap, g_pb_step)))
			#print("LR")
		# si l'arête droite/haut est homogène mais différente d'un point en dessous et à gauche
		if (sol6 == sol8 and (sol6 != sol5 or sol8 != sol7) and (sol2 != sol6 or sol4 != sol8)):
			# Construction d'un cube en haut à droite
			#     p7----+---p8
			#    /|    /    /|
			#   / |   /    / |
			#  /  |  /    /  + pb
			# p5----+---p6  /|  x
			# |   | |    | / |  |  x ws
			# |   p3|    |/-p4  | /
			# |  /  +----+  /   |/
			# | /        | /    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(round_to_multiple(p6.gr - gr_halfGap, g_gr_step), p6.gr, p6.ws, p8.ws, round_to_multiple(p6.pb - pb_halfGap, g_pb_step), p6.pb))
			#print("UR")
		# si l'arête gauche/haut est homogène mais différente d'un point en dessous et à droite
		if (sol5 == sol7 and (sol5 != sol6 or sol7 != sol8) and (sol1 != sol5 or sol3 != sol7)):
			# Construction d'un cube en haut à gauche
			#     p7---+----p8
			#    /    /|    /|
			#   /    / |   / |
			#  /    /  +  /  | pb
			# p5---+----p6   |  x
			# |    | /   |   |  |  x ws
			# |    |/----|--p4  | /
			# +----+     |  /   |/
			# | /        | /    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(p5.gr, round_to_multiple(p5.gr + gr_halfGap, g_gr_step), p5.ws, p7.ws, round_to_multiple(p5.pb - pb_halfGap, g_pb_step), p5.pb))
			#print("UL")
		# si l'arête avant/gauche est homogène mais différente d'un point en arrière et à droite
		if (sol1 == sol5 and (sol1 != sol2 or sol5 != sol6) and (sol1 != sol3 or sol5 != sol7)):
			# Construction d'un cube devant à gauche
			#     p7--------p8
			#    /|         /|
			#   +----+     / |
			#  /    /|    /  | pb
			# p5---+----p6   |  x
			# |    | |   |   |  |  x ws
			# |    | |---|--p4  | /
			# |    | |   |  /   |/
			# |    | +   | /    +------x gr
			# |    |/    |/
			# p1---+----p2
			queue.append(Cube(p1.gr, round_to_multiple(p1.gr + gr_halfGap, g_gr_step), p1.ws, round_to_multiple(p1.ws + ws_halfGap, g_ws_step), p1.pb, p5.pb))
			#print("FL")
		# si l'arête avant/droite est homogène mais différente d'un point en arrière et à gauche
		if (sol2 == sol6 and (sol1 != sol2 or sol5 != sol6) and (sol2 != sol4 or sol6 != sol8)):
			# Construction d'un cube devant à droite
			#     p7--------p8
			#    /|         /|
			#   / |  +-----+ |
			#  /  | /     /| | pb
			# p5---+----p6 | |  x
			# |   ||     | | |  |  x ws
			# |   p|     | |p4  | /
			# |  / |     | |/   |/
			# | /  |     | +    +------x gr
			# |/   |     |/
			# p1---+----p2
			queue.append(Cube(round_to_multiple(p2.gr - gr_halfGap, g_gr_step), p2.gr, p2.ws, round_to_multiple(p2.ws + ws_halfGap, g_ws_step), p2.pb, p6.pb))
			#print("FR")
		# si l'arête arrière/droite est homogène mais différente d'un point en avant et à gauche
		if (sol4 == sol8 and (sol3 != sol4 or sol7 != sol8) and (sol2 != sol4 or sol6 != sol8)):
			# Construction d'un cube en arrière à droite
			#     p7---+----p8
			#    /|   /     /|
			#   / |  +-----+ |
			#  /  |  |    /| | pb
			# p5--------p6 | |  x
			# |   |  |   | | |  |  x ws
			# |   p3-|   | |p4  | /
			# |  /   |   | |/   |/
			# | /    +---|-+    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(round_to_multiple(p4.gr - gr_halfGap, g_gr_step), p4.gr, round_to_multiple(p4.ws - ws_halfGap, g_ws_step), p4.ws, p4.pb, p8.pb))
			#print("BR")
		# si l'arête arrière/gauche est homogène mais différente d'un point en avant et à droite
		if (sol3 == sol7 and (sol3 != sol4 or sol7 != sol8) and (sol3 != sol1 or sol7 != sol5)):
			# Construction d'un cube en arrière à gauche
			#     p7---+----p8
			#    /    /|    /|
			#   +----+ |   / |
			#  /|    | |  /  | pb
			# p5--------p6   |  x
			# | |    | | |   |  |  x ws
			# | |    | +-|--p4  | /
			# | |    |/  |  /   |/
			# | +----+   | /    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(p3.gr, round_to_multiple(p3.gr + gr_halfGap, g_gr_step), round_to_multiple(p3.ws - ws_halfGap, g_ws_step), p3.ws, p3.pb, p7.pb))
			#print("BL")
		# si le coin avant/bas/gauche est isolé
		if(sol1 != sol2 and sol1 != sol3 and sol1 != sol5):
			# Construction d'un cube en bas à gauche devant
			#     p7--------p8
			#    /|         /|
			#   / |        / |
			#  /  |       /  | pb
			# p5--------p6   |  x
			# | +----+   |   |  |  x ws
			# |/    /|---|--p4  | /
			# +----+ |   |  /   |/
			# |    | +   | /    +------x gr
			# |    |/    |/
			# p1---+----p2
			queue.append(Cube(p1.gr, round_to_multiple(p1.gr + gr_halfGap, g_gr_step), p1.ws, round_to_multiple(p1.ws + ws_halfGap, g_ws_step), p1.pb, round_to_multiple(p1.pb + pb_halfGap, g_pb_step)))
			#print("FDL")
		# si le coin avant/haut/gauche est isolé
		if(sol5 != sol6 and sol5 != sol7 and sol5 != sol1):
			# Construction d'un cube en haut à gauche devant
			#     p7--------p8
			#    /|         /|
			#   +----+     / |
			#  /    /|    /  | pb
			# p5---+----p6   |  x
			# |    | +   |   |  |  x ws
			# |    |/----|--p4  | /
			# +----+     |  /   |/
			# | /        | /    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(p5.gr, round_to_multiple(p5.gr + gr_halfGap, g_gr_step), p5.ws, round_to_multiple(p5.ws + ws_halfGap, g_ws_step), round_to_multiple(p5.pb - pb_halfGap, g_pb_step), p5.pb))
			#print("FUL")
		# si le coin avant/bas/droite est isolé
		if(sol2 != sol1 and sol2 != sol6 and sol2 != sol4):
			# Construction d'un cube en bas à droite devant
			#     p7--------p8
			#    /|         /|
			#   / |        / |
			#  /  |       /  | pb
			# p5--------p6   |  x
			# |   |   +--|-+ |  |  x ws
			# |   p3-/   |/|p4  | /
			# |  /  +----+ |/   |/
			# | /   |    | +    +------x gr
			# |/    |    |/
			# p1----+---p2
			queue.append(Cube(round_to_multiple(p2.gr - gr_halfGap, g_gr_step), p2.gr, p2.ws, round_to_multiple(p2.ws + ws_halfGap, g_ws_step), p2.pb, round_to_multiple(p2.pb + pb_halfGap, g_pb_step)))
			#print("FDR")
		# si le coin avant/haut/droite est isolé
		if(sol6 != sol5 and sol6 != sol2 and sol6 != sol8):
			# Construction d'un cube en haut à droite devant
			#     p7--------p8
			#    /|         /|
			#   / |   +----+ |
			#  /  |  /    /| | pb
			# p5----+---p6 | |  x
			# |   | |    | + |  |  x ws
			# |   p3|    |/-p4  | /
			# |  /  +----+  /   |/
			# | /        | /    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(round_to_multiple(p6.gr - gr_halfGap, g_gr_step), p6.gr, p6.ws, round_to_multiple(p6.ws + ws_halfGap, g_ws_step), round_to_multiple(p6.pb - pb_halfGap, g_pb_step), p6.pb))
			#print("FUR")
		# si le coin arrière/bas/gauche est isolé
		if(sol3 != sol1 and sol3 != sol4 and sol3 != sol7):
			# Construction d'un cube en bas à gauche derrière
			#     p7--------p8
			#    /|         /|
			#   / |        / |
			#  /  +----+  /  | pb
			# p5--------p6   |  x
			# | +----+ | |   |  |  x ws
			# | |    |-+-|--p4  | /
			# | |    |/  |  /   |/
			# | +----+   | /    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(p3.gr, round_to_multiple(p3.gr + gr_halfGap, g_gr_step), round_to_multiple(p3.ws - ws_halfGap, g_ws_step), p3.ws, p3.pb, round_to_multiple(p3.pb + pb_halfGap, g_pb_step)))
			#print("BDL")
		# si le coin arrière/haut/gauche est isolé
		if(sol7 != sol3 and sol7 != sol8 and sol7 != sol5):
			# Construction d'un cube en haut à gauche derrière
			#     p7---+----p8
			#    /    /|    /|
			#   +----+ |   / |
			#  /|    | +  /  | pb
			# p5--------p6   |  x
			# | +----+   |   |  |  x ws
			# |   p3-----|--p4  | /
			# |  /       |  /   |/
			# | /        | /    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(p7.gr, round_to_multiple(p7.gr + gr_halfGap, g_gr_step), round_to_multiple(p7.ws - ws_halfGap, g_ws_step), p7.ws, round_to_multiple(p7.pb - pb_halfGap, g_pb_step), p7.pb))
			#print("BUL")
		# si le coin arrière/bas/droite est isolé
		if(sol4 != sol3 and sol4 != sol2 and sol4 != sol8):
			# Construction d'un cube en bas à droite derrière
			#     p7--------p8
			#    /|         /|
			#   / |        / |
			#  /  |     +-/--+ pb
			# p5--------p6  /|  x
			# |   |   +--|-+ |  |  x ws
			# |   p3--|  | |p4  | /
			# |  /    |  | |/   |/
			# | /     +--|-+    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(round_to_multiple(p4.gr - gr_halfGap, g_gr_step), p4.gr, round_to_multiple(p4.ws - ws_halfGap, g_ws_step), p4.ws, p4.pb, round_to_multiple(p4.pb + pb_halfGap, g_pb_step)))
			#print("BDR")
		# si le coin arrière/haut/droite est isolé
		if(sol8 != sol7 and sol8 != sol4 and sol8 != sol6):
			# Construction d'un cube en haut à droite derrière
			#     p7----+---p8
			#    /|    /    /|
			#   / |   +----+ |
			#  /  |   |   /| + pb
			# p5--------p6 |/|  x
			# |   |   +--|-+ |  |  x ws
			# |   p3-----|--p4  | /
			# |  /       |  /   |/
			# | /        | /    +------x gr
			# |/         |/
			# p1--------p2
			queue.append(Cube(round_to_multiple(p8.gr - gr_halfGap, g_gr_step), p8.gr, round_to_multiple(p8.ws - ws_halfGap, g_ws_step), p8.ws, round_to_multiple(p8.pb - pb_halfGap, g_pb_step), p8.pb))
			#print("BUR")


# \brief Compresse une trace en explorant les paramètres gr, ws et pb.
#
# @trace : la trace à compresser sous la forme d'une chaine de caractère
# @solution : représente la solution de référence sous la forme d'une chaine de caractère.
def search_aveugle(trace:str, solution:str):
	global  g_tab_parametersToBestResultPos

	g_tab_parametersToBestResultPos = np.zeros((g_nbPoints, g_nbPoints, g_nbPoints))

	# boucle pour calculer les gr
	for i in range(g_nbPoints):
		gr = i*g_gr_step
		# boucle pour calculer les ws
		for j in range(g_nbPoints):
			ws = j*g_ws_step
			for k in range(g_nbPoints):
				pb = k*g_pb_step
				print("Call parser with parameters\tgr: "+str(gr)+"   \tws: "+str(ws)+"   \tpb: "+str(pb))
				# Fait tourner l'algo de compression sur la trace
				# Transformation du string en une liste d'évènement
				eventList:list[Event] = []
				for char in trace:
					eventList.append(Call(char))
				compressions:CompressionSet = MAP(eventList, float(gr), float(ws), float(pb))

				g_tab_parametersToBestResultPos[i][j][k] = compressions.getCode(solution)
	


# \brief Exécuter la recherche de paramètres avec la façon qu'on souhaite
#
# @dichotomique : utilisation l'algorithme de dichotomique avec des rectangles pour réduire le nombre de test
# @files : liste des fichiers à analyser
def run(dichotomique:bool, files:list[str]):
	# Façon dichotomique
	if (dichotomique):
		for fileName in files:
			# Chargement du contenu du fichier
			trace:str = ""
			with open("./example/"+fileName, 'r') as file:
				trace = file.readline()
			print("Recherche des paramètres pour le fichier : "+fileName)
			# Chargement du contenu de la solution
			solution:str = ""
			with open("./example/solutions/"+fileName, 'r') as file:
				solution = file.readline()
			# Analyse
			search_gr_ws_by_rect(trace, solution)
			# Mise en évidence en vert des paramètres permettant d'obtenir la meilleure solution
			np.save("./files_npy/"+fileName.replace(".log", ".npy"),g_tab_parametersToBestResultPos)
			# Idem que la précédente sauf que les trous de l'approche dicotomique sont remplis
			np.save("./files_npy/filled_"+fileName.replace(".log", ".npy"), g_tab_filledMap)
			print("Nombe de points explorés : "+str(len(g_exploredMap))+"                                                        ")
			#print(str(g_exploredMap))
			#print("************************************************************\n\n")
	# Façon aveugle
	else:
		for fileName in files:
			# Chargement du contenu du fichier
			trace:str = ""
			with open("./example/"+fileName, 'r') as file:
				trace = file.readline()
			print("Recherche des paramètres pour le fichier : "+fileName)
			# Chargement du contenu de la solution
			solution:str = ""
			with open("./example/solutions/"+fileName, 'r') as file:
				solution = file.readline()
			search_aveugle(trace, solution)
			# Mise en évidence en vert des paramètres permettant d'obtenir la meilleure solution
			np.save("./files_npy/"+fileName.replace(".log", ".npy"),g_tab_parametersToBestResultPos)
			print("************************************************************\n\n")

if __name__ == "__main__":
	test_file:list[str] = []
	argv = sys.argv
	if(not os.path.exists("./files_npy/")):
		os.makedirs("./files_npy/")
	if(len(argv)>2):
		test_file.append(argv[1])
		if(sys.argv[2]=="aveugle"):
			run(dichotomique=False, files=test_file)
		elif(sys.argv[2]=="dichotomique"):
			run(dichotomique=True, files=test_file)
		else:
			print("Utilisation dans terminal : python rechercheParameters.py fileName aveugle/dichotimique\n")
	elif(len(sys.argv)==2):
		test_file.append(argv[1])
		run(dichotomique=True, files=test_file)
	else:
		print("Lancement des tests...\n")
		#test_file = ["1_rienAFaire.log", "2_simpleBoucle.log", "3_simpleBoucleAvecDebut.log", "4_simpleBoucleAvecFin.log", "5_simpleBoucleAvecDebutEtFin.log", "6.01_simpleBoucleAvecIf.log", "6.02_simpleBoucleAvecIf.log", "6.03_simpleBoucleAvecIf.log", "6.04_simpleBoucleAvecIf.log", "6.05_simpleBoucleAvecIf.log", "6.06_simpleBoucleAvecIf.log", "6.07_simpleBoucleAvecIf.log", "6.08_simpleBoucleAvecIf.log", "6.09_simpleBoucleAvecIf.log", "6.10_simpleBoucleAvecIf.log", "6.11_simpleBoucleAvecIf.log", "6.12_simpleBoucleAvecIf.log", "6.13_simpleBoucleAvecIf.log", "6.14_simpleBoucleAvecIf.log", "6.15_simpleBoucleAvecIf.log", "7.01_bouclesEnSequence.log", "7.02_bouclesEnSequence.log", "8_bouclesEnSequenceAvecIf.log", "9.01_bouclesImbriquees.log", "9.02_bouclesImbriquees.log", "9.03_bouclesImbriquees.log"]
		#test_file = ["m1.log", "m2.log", "m3.log", "m4.log", "m5.log", "m6.log", "m7.log", "m81.log", "m82.log", "m11.log"]
		#test_file = ["m8.log"]
		test_file = ["6.15_simpleBoucleAvecIf.log"]
		run(dichotomique=True, files=test_file)
