# This game is a modified version from Pythonic cheat game by Mitchell Kember in 2009
# This modified version include the AI created by Tung Thai, Aparna Penmetcha, and Avi Block
# Copyright (c) 2020. All rights reserved.

"""
Created on 24-4-2020

AI cheat MTCS based game
written in python 3.6.5.

Classes:
Player
Human(Player)
Computer(Player)
Difficulty #this need to be fixed
Deck
Card
Value
Suit #can be deleted, can just leave it there for show
Game

Functions:
game_setup

@author: Tung Thai, Aparna Penmetcha, and Avi Block

"""

# Imports
from random import randint
from random import shuffle
from re import split
from time import sleep
import copy
import random
import math
import hashlib
import logging
import argparse

SCALAR=1/math.sqrt(2.0)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('MyLogger')
lying = False
turn_ct = 0

class State():
	NUM_TURNS = 10
	GOAL = 0
	#PREVIOUS MOVE
	MAX_VALUE= (5.0*(NUM_TURNS-1)*NUM_TURNS)/2
	def __init__(self, value, moves, prev_move,turn, g, p, turn_type):
		global bs
		#Value = num_cards held
		self.g = copy.deepcopy(g)
		self.num_moves = len(moves)
		self.cur_player = self.g.players[0]
		for pl in self.g.players:
			if isinstance(pl, Human):
				# print("new rollout")
				tmp = Computer(pl.name, 2)
				tmp.hand = copy.copy(pl.hand)
				i = self.g.players.index(pl)
				# self.g.players.remove(pl)
				self.g.players[i] = tmp
			if pl == p:
				self.cur_player = pl
			# if pl == p_prev:
			# 	self.prev_player = pl
		self.value=len(p.hand)
		self.turn=turn
		self.prev_move = prev_move
		self.turn_type = turn_type
		# print("previous move: ", self.prev_move)
		#Moves = [play_all_matching_cards(), play_1_lie(), play_2_lie(), etc]
		self.moves=moves
		bs = self
	def next_state(self):
		global lying
		#nextmove = random.choice([x for x  in self.MOVES])
		nextmove = random.choice([x for x  in self.moves])
		# prev_player = self.prev_player
		# print("sim next_move for turn ", self.turn + 1," by ", self.cur_player.name, ": ", nextmove, " from moves: ", self.moves, " after prev move: ", self.prev_move)
		# add previous move, dont change value
		next_cur = True
		self.cur_player.hand = Deck.sort_hand(self.cur_player.hand)
		second_challenge = False
		try:
			lying = nextmove["lying"]
		except AttributeError:
			# print("ATCH")
			pass
		except KeyError:
			# print("KEY!")
			pass
		try:
			test = self.prev_move["lying"]
		except KeyError:
			# print("IDK WHAT IM DOING")
			pass
		if nextmove["move"] == "challenge":
			if self.turn_type == 0:
				self.turn_type = 2
			if self.turn_type == 2:
				second_challenge = True
			self.prev_player = self.g.c_player
			prev_player = self.prev_player
			if lying:
				if len(self.g.pile) > 0:
					# print("Caught! adding ", [c.value for c in self.g.pile], "to ", prev_player.name, "'s hand")
					prev_player.hand += self.g.pile
				self.g.pile = []
			elif not lying:
				if len(self.g.pile) > 0:
					# print("Wrongful Accusation! adding ", [c.value for c in self.g.pile], "to ", self.cur_player.name, "'s hand")
					self.cur_player.hand += self.g.pile
				self.g.pile = []
			if second_challenge:
				self.g.update_current()
				new_cur_player = self.g.c_player
				# print("now it is ", new_cur_player.name, "'s turn")
				next_cur = True
			else:
				next_cur = False
				try:
					new_cur_player = self.g.players[self.g.players.index(self.cur_player) + 1]
				except IndexError:
					new_cur_player = self.g.players[0]
		elif nextmove["move"] == "no challenge":
			if self.turn_type == 1 or self.turn_type == 0:
				next_cur = False
				if self.turn_type == 0: self.turn_type = 2
				try:
					new_cur_player = self.g.players[self.g.players.index(self.cur_player) + 1]
				except IndexError:
					# print("uh oh")
					new_cur_player = self.g.players[0]
			if self.turn_type == 2:
				next_cur = True
				self.g.update_current()
				new_cur_player = self.g.c_player
				# print("now it is ", new_cur_player.name, "'s turn")
		else:
			next_cur = False
			cards = []
			try:
				new_cur_player = self.g.players[self.g.players.index(self.g.c_player) + 1]
			except IndexError:
				# print("UGH")
				new_cur_player = self.g.players[0]
			for a in nextmove["move"]:
				try:
					cards.append(copy.copy(self.g.c_player.hand[a]))
				except IndexError:
					# print("Index out of range: ", a, ", hand: ", [c.value for c in self.g.c_player.hand])
					# exit(0)
					pass
			for c in cards:
				self.g.c_player.hand.remove(c)
				self.g.pile.append(c)

		self.value = len(new_cur_player.hand)
		# tst = "lying" in self.prev_move.keys()
		# if tst:
		# 	next_cur = False
		# 	print("just in case")
		self.moves = self.g.get_moves(new_cur_player)
		self.turn_type = (self.turn_type + 1) % 3
		# print("hmmm... new turn type: ", self.turn_type, " new_cur_player: ", new_cur_player)
		self.turn += 1
		self.cur_player = new_cur_player
		return State(self.value, self.moves, nextmove, self.turn, self.g, self.cur_player, self.turn_type)
		# if self.turn % 100 == 0:
		# 	print("Still simming, at turn #", self.turn)
		# return new_state

	def terminal(self):
		if any([len(p.hand) == 0 for p in self.g.players]):
			return True
		return False

	def reward(self):
		#need
		r = 1.0-(self.value/(52 - len(self.g.pile)))
		return r
	def __hash__(self):
		return int(hashlib.md5(str(self.moves).encode('utf-8')).hexdigest(),16)
	def __eq__(self,other):
		if hash(self)==hash(other):
			return True
		return False
	def __repr__(self):
		s="Value: %d; Moves: %s"%(self.value,self.moves)
		return s

# MCTS
class Node():
	def __init__(self, state, parent=None):
		self.visits=1
		self.reward=0.0
		self.state=state
		self.children=[]
		self.parent=parent
	def add_child(self,child_state):
		child=Node(child_state,self)
		self.children.append(child)
	def update(self,reward):
		self.reward+=reward
		self.visits+=1
	def fully_expanded(self):
		if len(self.children)==self.state.num_moves:
			return True
		return False
	def __repr__(self):
		s="Node; children: %d; visits: %d; reward: %f"%(len(self.children),self.visits,self.reward)
		return s

def UCTSEARCH(budget,root):
	for iter in range(int(budget)):
		# print("STARTING ROLLOUT ", iter,"! from root: ", root.state)
		if iter%10000==9999:
			logger.info("simulation: %d"%iter)
			logger.info(root)
		front=TREEPOLICY(root)
		reward=DEFAULTPOLICY(front.state)
		BACKUP(front,reward)
	return BESTCHILD(root,0)

def TREEPOLICY(node):
	#a hack to force 'exploitation' in a game where there are many options, and you may never/not want to fully expand first
	while node.state.terminal()==False:
		if len(node.children)==0:
			return EXPAND(node)
		elif random.uniform(0,1)<.5:
			node=BESTCHILD(node,SCALAR)
		else:
			if node.fully_expanded()==False:
				return EXPAND(node)
			else:
				node=BESTCHILD(node,SCALAR)
	# print("end treepolicy")
	return node

def EXPAND(node):
	tried_children=[c.state for c in node.children]
	new_state=node.state.next_state()
	while new_state in tried_children:
		new_state=node.state.next_state()
	node.add_child(new_state)
	return node.children[-1]

#current this uses the most vanilla MCTS formula it is worth experimenting with THRESHOLD ASCENT (TAGS)
def BESTCHILD(node,scalar):
	bestscore=0.0
	bestchildren=[]
	for c in node.children:
		exploit=c.reward/c.visits
		explore=math.sqrt(2.0*math.log(node.visits)/float(c.visits))
		score=exploit+scalar*explore
		if score==bestscore:
			bestchildren.append(c)
		if score>bestscore:
			bestchildren=[c]
			bestscore=score
	if len(bestchildren)==0:
		logger.warn("OOPS: no best child found, probably fatal")
	return random.choice(bestchildren)

def DEFAULTPOLICY(state):
	while state.terminal()==False:
		state=state.next_state()
	return state.reward()

def BACKUP(node,reward):
	while node!=None:
		node.visits+=1
		node.reward+=reward
		node=node.parent
	return

# Functions
def game_setup():
	"""Sets up a game with user input.

	Sets up a game by asking the user how many players,
	their names, difficulties, asks if they would like
	to see the rules, etc.

	"""
	print("This is an AI Cheat game using MCTS model")
	print("This game limited to 4 players (including the computers and humans) at a time.")
	# Get the amount of human players.
	while True:
		h = input("How many human players will there be?").strip()
		try:
			h = int(h)
		except ValueError:
			print("Please type a number.")
		else:
			break
	# Get the amount of computer players.
	while True:
		c = input("How many computer players will there be?").strip()
		try:
			c = int(c)
		except ValueError:
			print("Please type a number.")
		else:
			break
	# Get the names of the human players.
	humans = []
	for num in range(h):
		while True:
			name = input("Type the {0} human's name:".format(Game.ranks[num])) \
					.strip()
			if not (name.isspace() or not name):
				break
		humans.append(Human(name))
	# Get the names and levels of difficulty of the computer players.
	computers = []
	for num in range(c):
		while True:
			name = input("Type the {0} computer player's name:".format(
				Game.ranks[num])).strip()
			if not (name.isspace() or not name):
				break
		while True:
			d = input("Enter {0}'s difficulty (Easy = 1, Medium = 2, Hard = 3):"
				.format(name)).strip()
			try:
				d = int(d)
			except ValueError:
				print("Please type a number.")
			else:
				break
		computers.append(Computer(name, d))
	players = humans + computers
	# Ask if they want to see the rules.
	if 'y' in input("Would you like to see the rule of the game ? (Y/N):").lower():
		print(Game.gameplay)
	input("Press enter to start...")
	# Begin the game
	Game(*players)

# Classes
class Player:

	"""A player in the game.

	A player in the game with a name and
	a hand of cards. A player can be converted to
	a string with str(instance_of_player), which
	returns their name attribute.

	Attributes:
	self.name -- str
	self.hand -- list

	Keyword Arguments:
	name -- the player's name - str

	"""

	def __init__(self, name):
		super().__init__()
		self.name = name
		self.hand = []

	def __str__(self):
		"""The string representation of a Player object, the name attribute."""
		return self.name

	def __eq__(self, obj):
		return self.name == obj.name

class Human(Player):

	"""A human player, derived from class Player.

	A human player in the game, derived from the
	class PLayer. Currently, it is exactly the same as
	its superclass, and is used only for the name \"Human\".
	A human player has a name and a hand of cards.

	Inherited Attributes:
	self.name -- str
	self.hand -- list

	Keyword Arguments:
	name -- the human player's name - str

	"""

	def __init__(self, name):
		super().__init__(name)

class Computer(Player):

	"""A computer player, derived from class Player.

	A computer player for the cheat game, derived from the
	class PLayer. It is a Player (which has a name and a hand
	of cards) with a level of difficulty.

	Inherited Attributes:
	self.name -- str
	self.hand -- list

	New Attributes:
	self.difficulty - use class Difficulty (numbers 1 to 3)

	Keyword Arguments:
	name -- the computer player's name
	[difficulty] -- the computer player's level of difficulty,
		Difficulty.easy, Difficulty.medium or Difficulty.hard
		Default: a random choice out of the three

	"""

	def __init__(self, name, difficulty=randint(1, 3)):
		super().__init__(name)
		if difficulty < 1 or difficulty > 3:
			raise ValueError
		self.difficulty = difficulty


## this class can be deleted/modified later
class Difficulty:

	"""An enum class for a computer player's difficulty.

	An enum class to define a computer player's level
	of difficulty, either 1 (Difficulty.easy), 2
	(Difficulty.medium) or 3 (Difficulty.hard). Difficulty
	is not to be instatiated.

	Attributes:
	Difficulty.unknown -- 0
	Difficulty.easy -- 1
	Difficulty.medium -- 2
	Difficulty.hard -- 3

	Methods:
	Difficulty.name -- returns str

	"""

	unknown, easy, \
	medium, hard = range(4)

	@staticmethod
	def name(difficulty):
		"""Returns the name of the difficulty level."""
		return ['unknown', 'easy', 'medium', 'hard'][difficulty]

class Deck:

	"""A Deck of 52 cards.

	A deck of 52 regular playing cards for the game, each
	card being an instance of the Card class (see the Card
	class documentation for more details).

	Attributes:
	self.cards -- list

	Methods:
	self.shuffle_deck -- returns None
	Deck.sort_hand -- returns list

	Keyword Arguments:
	[shuffled] -- shuffles the deck after creating if True - bool
		default: True

	"""

	def __init__(self, shuffled=True):
		super().__init__()
		self.cards = []
		# Loop through the four suits and the 13 values
		# And create each card (52)
		for s in range(1, 5):
			for v in range(1, 14):
				self.cards.append(Card(v, s))
		if shuffled:
			self.shuffle_deck()
	def shuffle_deck(self):
		"""Shuffles the deck."""
		shuffle(self.cards)

	@staticmethod
	def sort_hand(hand):
		"""Sorts a Player's hand of cards by value (ace through king)."""
		vals = []
		for c in hand:
			if isinstance(c, Card):
				vals.append((c, c.value))
		# Sort by the second element in each tuple (the value)
		vals.sort(key=lambda a:a[1])
		return [c[0] for c in vals]

class Card:

	"""A regular playing card.

	A regular playing Card, each with a value
	(ace through king) and a suit (spades, clubs,
	hearts or diamonds). 52 Card objects make up
	a Deck object. Card objects can be compared
	with ==, !=, <=, >=, > or < and can be converted
	to a string with str(instance_of_Card).

	Attributes:
	self.value -- the card's value (ace, four, queen, etc.)
	self.suit -- the card's suit (spades, diamonds, etc.)

	Keyword Arguments:
	value -- the card's value, a number from 1 to 13.
		use Value.ace, Value.two, etc. Value is
		a class with the 13 values
	suit -- the card's suit, a number from 1 to 4.
		use Suit.spades, Suit.hearts, etc. Suit is a
		class with the 4 suits

	"""

	def __init__(self, value, suit):
		super().__init__()
		self.value = value
		self.suit = suit

	def __str__(self):
		"""Returns the name of the Card. (Format: \"The [value] of [suit]\")"""
		return "the " + Value.name(self.value) + " of " + \
			Suit.name(self.suit)

	def __eq__(self, obj):
		"""How to compare two Card objects for equality."""
		if not isinstance(obj, Card):
			return False
		return self.value == obj.value and self.suit == obj.suit

	def __ne__(self, obj):
		"""How to compare two Card objects for inequality."""
		return not self.__eq__(obj)

	def __gt__(self, obj):
		"""How to compare two Card objects for greatness."""
		if not isinstance(obj, Card):
			raise TypeError
		return self.value > obj.value

	def __ge__(self, obj):
		"""How to compare two Card objects for greatness or equality."""
		if not isinstance(obj, Card):
			raise TypeError
		return self > obj or self.value == obj.value

class Value:

	"""An enum class for a card's value.

	An enum class to define a card's value,
	which is a number between 1 and 13, using the Value
	class, Value.ace, Value.four, Value.king etc.
	Value is not to be instatiated.

	Attributes:
	Value.unknown -- 0
	Value.ace -- 1
	Value.two -- 2
	Value.three -- 3
	Value.four -- 4
	Value.five -- 5
	Value.six -- 6
	Value.seven -- 7
	Value.eight -- 8
	Value.nine -- 9
	Value.ten -- 10
	Value.jack -- 11
	Value.queen -- 12
	Value.king -- 13

	Methods:
	Value.name -- returns str

	"""

	unknown, ace, two, three, four, five, six, \
	seven, eight, nine, ten, jack, queen, king = range(14)

	@staticmethod
	def name(value):
		"""Returns the name of the value."""
		return ['unknown', 'ace', 'two', 'three', 'four', 'five', 'six',
			'seven', 'eight', 'nine', 'ten', 'jack', 'queen', 'king'][value]

class Suit:

	"""An enum class for a card's suit.

	An enum class to define a card's suit,
	which is a number between 1 and 4, using
	the Suit class, Suit.spades, Suit.hearts,
	etc. Suit is not to be instantiated.

	Attributes:
	unknown -- 0
	spades -- 1
	clubs -- 2
	hearts -- 3
	diamonds -- 4

	Methods:
	Suit.name -- returns str

	"""

	unknown, spades, clubs, \
	hearts, diamonds = range(5)

	@staticmethod
	def name(suit):
		"""Returns the name of the suit."""
		return ['unknown', 'spades', 'clubs', 'hearts', 'diamonds'][suit]

class Game:

	"""A Pythonic CHEAT! game.

	A game of Pythonic CHEAT!. Instatiating Game will start
	the game immediately. There can be a maximum of 8 players
	in the game. The Game class controls the user interface.
	Game should not be instantiated directly, but through
	the game_setup global function.

	Attributes:
	Game.gameplay -- str
	Game.ranks -- list
	self.players -- list
	self.winners -- list
	self.deck -- Deck
	self.pile -- list
	self.player_iter -- iter()
	self.c_player -- Player
	self.value_iter -- iter()
	self.c_value -- int

	Methods:
	self.reset_player_iter -- returns None
	self.reset_value_iter -- returns None
	self.deal_cards -- returns None
	self.update_current -- returns None
	self.next_turn -- returns None
	self.human_turn -- returns None
	self.computer_turn -- returns None
	self.finish_turn -- returns None
	self.get_challenges -- returns list
	self.human_challenge -- returns list
	self.computer_challenge -- returns list

	Keyword Arguments:
	*players -- a variable amount of Player objects (max: 8)

	"""

	# gameplay: The rules of cheat and how it is played.
	gameplay = """                         Cheat gameplay:
\tThe object of the game is to get rid of all your cards. The winner is the
first person to get rid of all their cards.

\tTo start the game, the entire deck of 52 cards is dealt evenly to everyone.
Now, the Player with the ace of spades will start. On this first turn, he or
she is allowed to put down all of his or her aces. He or she will take the
cards, place them face-down on the pile of cards and say the number of cards
they are putting down and that turn's card (ex \"2 twos\", \"1 jack\"). The
next Player will put down twos, the next three, etc. until king, then it goes
back to aces.

\tOn each Player's turn, they will have to cheat if they do not have
any of the correct card. This means they will put down cards other than the
correct ones. You are NOT allowed to put down your cards and say that you are
putting down a Difficultyerent number of cards (ex say \"1 king\" but actually
put down two). So you can put down an ace and an eight when you are supposed to
put down kings and say \"2 kings\". You can also cheat even if you don't have
to, if you are supposed to put down fours and you have 2 fours, you could put
the fours down and also put a queen and say \"3 fours\", or even put down a jack
and say \"1 four\", and not even put down the fours that you have at all!

\tAfter any Player's turn, any other Player can challenge them by accusing
\"Cheat!\". If the Player cheated, they must take up the entire pile. If the
Player hasn't cheated, the challenger must add the entire pile to their hand.

\tThis will continue until a Player wins."""
	# Ranks for the winners
	ranks = ['first', 'second', 'third', 'fourth']

	def __init__(self, *players):
		super().__init__()
		self.players = list(players)  # (So that it is mutable)
		# Make sure there are no more than eight players:
		if len(self.players) > 4:
			print("There cannot be more than 4 Players.")
			return
		# And no less than 1.
		elif len(self.players) < 1:
			print("There has to be atleast one player.")
			return
		# Make sure all players are instances of the class Player
		for p in self.players:
			if not isinstance(p, Player):
				print('Error: Players are not Player objects.')
				raise TypeError
				return
		# self.c_player: The player whose turn it is.
		# self.c_value: This turn's card value (ace through king).
		self.winners = []
		self.deck = Deck()
		self.pile = []
		self.player_iter = iter(self.players)
		self.c_player = None
		self.value_iter = iter(range(1, 14))
		self.c_value = 0
		self.prev_move = {}
		self.turn_num = 1

		self.deal_cards()
		# Move the player with the ace of spades to the front of self.players.
		for ind, p in enumerate(self.players):
			for c in p.hand:
				if c == Card(Value.ace, Suit.spades):
					self.players[0], self.players[ind] = \
						self.players[ind], self.players[0]
		# Begin the chain of turns.
		self.next_turn()

	def reset_player_iter(self):
		"""Resets the player iterator by re-assigning it."""
		self.player_iter = iter(self.players)

	def reset_value_iter(self):
		"""Resets the value iterator by re-assigning it."""
		self.value_iter = iter(range(1, 14))

	def deal_cards(self):
		"""Deals the deck to each player."""
		i = 0
		for c in self.deck.cards:
			if i == len(self.players):
				i = 0
			self.players[i].hand.append(c)
			i += 1
		# Delete self.deck, and use self.pile instead so to not have to use
		# self.deck.cards.
		del self.deck

	# NEED MOVES function

	def update_current(self):
		"""Updates the current player and current value attributes.

		Updates the current player and current value for the next
		turn (Ace -> Two, self.players[0] -> self.players[1]).

		"""
		while True:
			# Go to the next player in the self.players list.
			try:
				self.c_player = next(self.player_iter)
			# If at the end of the list, go back to the start.
			except StopIteration:
				self.reset_player_iter()
				self.c_player = next(self.player_iter)
			if self.c_player not in self.winners:
				break
		# Go to the next card value in the range of numbers 1 through 14.
		try:
			self.c_value = next(self.value_iter)
		# If at the end of the list, go back to the start.
		except StopIteration:
			self.reset_value_iter()
			self.c_value = next(self.value_iter)

	def next_turn(self):
		"""Continues to the next turn in the game.

		Begins the next turn. First, updating the current player
		and value attributes and then checking if the game is over. The
		information about this turn (which player, what value) is
		printed, and then the next section of the turn is executed
		by calling human_turn or computer_turn depending on which
		type the player is.

		"""
		# Update self.c_player and self.c_value.
		# self.turn_num += 1
		self.update_current()
		# Check to see if there is only one player left (game is over).
		# If there is, then print the ranks and end.
		if len([p for p in self.players if p not in self.winners]) == 1:
			print("The game is over.\n\nThe ranks:\n")
			for place, p in enumerate(self.winners):
				print("{0} - {1}".format(Game.ranks[place], p))
			print("{0} - {1}".format(Game.ranks[len(self.winners)], self.c_player))
			sleep(5)
			# input("Press enter to end...")
			return
		print("It's {0}'s turn. {0}, put down your {1}s.\n".format(
			self.c_player, Value.name(self.c_value)), end=' '*6)
		sleep(2)
		# input("Press enter to continue...")
		# Go on to either human_turn() or computer_turn()
		if isinstance(self.c_player, Computer):
			self.computer_turn()
		elif isinstance(self.c_player, Human):
			self.human_turn()
		else:
			print("Error: Players are not human or computer objects.")

	def human_turn(self):
		"""Executes a Human Player's turn.

		Tells the human player what value of card they
		are supposed to put down, shows them their hand
		of cards, lets them choose the cards, validates
		the choice and then calls the finish_turn method.

		"""
		# Sort the player's cards by value, so that they go from ace to king.
		self.c_player.hand = Deck.sort_hand(self.c_player.hand)
		print("{0}, here are your cards.".format(self.c_player) + \
			"Type the number keys of the cards you want to play")
		# Print the player's cards, and
		# print the value that is supposed to be put down in CAPS.
		for ind, c in enumerate(self.c_player.hand):
			print("{0:2}: ".format(ind), end='')
			if c.value == self.c_value:
				print(str(c).upper())
			else:
				print(c)
		# Loop until atleast one valid card is chosen by the human.
		while True:
			# card_indexes: The indexes of the cards put down.
			# The indexes can be entered seperated by spaces or commas.
			card_indexes = split('\W+', input("Enter the number keys: "))
			for ind, c in enumerate(card_indexes):
				# Make sure that each index is a number (digit).
				if not c.isdigit():
					card_indexes[ind] = None
					continue
				# Make sure the index is valid, that it is one of the indexes
				# in the player's hand of cards.
				if int(c) >= len(self.c_player.hand):
					card_indexes[ind] = None
			# Remove multiple occurences
			card_indexes = list(set(card_indexes))
			# Delete the invalid items
			if None in card_indexes:
				card_indexes.remove(None)
			# Make sure at least one card is chosen.
			if not card_indexes:
				print("You have to put down at least one card.")
			else:
				break
		if all([c.value == self.c_value for c in [self.c_player.hand[int(i)] for i in card_indexes]]):
			lie = False
		else:
			lie = True
		self.finish_turn(card_indexes, lie)

	def one_lie(self,p):
		move = []
		for i in range(len(p.hand)):
			if p.hand[i].value < self.c_value:
				move = [i]
		if len(move) == 0:
			move = [0]
		return {"move": move, "lying": True}

	def two_lie(self,p):
		move = []
		if len(p.hand) >= 2:
			for i in range(len(p.hand)):
				if p.hand[i].value < self.c_value:
					if i >= 1:
						move = [i-1, i]
					else:
						move = [i, i+1]
			if len(move) == 0:
				move = [0,1]
		else:
			move = []
		return {"move": move, "lying": True}

	def three_lie(self,p):
		move = []
		if len(p.hand) >= 3:
			for i in range(len(p.hand)):
				if p.hand[i].value < self.c_value:
					if i >= 2:
						move = [i-2, i-1, i]
					elif i == 1:
						move = [i-1, i, i+1]
					elif i == 0:
						move = [i, i+1, i+2]
			if len(move) == 0:
				move = [0,1,2]
		else:
			move = []
		return {"move": move, "lying": True}

	def four_lie(self,p):
		move = []
		if len(p.hand) >= 4:
			for i in range(len(p.hand)):
				if p.hand[i].value < self.c_value:
					if i >= 3:
						move = [i-3, i-2, i-1, i]
					elif i == 2:
						move = [i-2, i-1, i, i+1]
					elif i == 1:
						move = [i-1, i, i+1, i+2]
					elif i == 0:
						move = [i, i+1, i+2, i+3]
			if len(move) == 0:
				move = [0,1,2,3]
		else:
			move = []
		return {"move": move, "lying": True}

	def no_lie(self,p):
		move = []
		p.hand = Deck.sort_hand(p.hand)
		for i in range(len(p.hand)):
			if (p.hand[i].value == self.c_value):
				move.append(i)
		return {"move": move, "lying": False}

	def get_moves(self, p):
		cur = self.c_player == p
		try:
			p.hand = Deck.sort_hand(p.hand)
		except AttributeError:
			print("not sorting")

		moves = []
		if cur:
			no = self.no_lie(p)
			if len(no["move"]) > 0:
				moves = [no]
			elif len(moves) == 0:
				one = self.one_lie(p)
				if len(one["move"]) > 0:
					moves.append(one)
				two = self.two_lie(p)
				if len(two["move"]) > 0:
					moves.append(two)
				three = self.three_lie(p)
				if len(three["move"]) > 0:
					moves.append(three)
				four = self.four_lie(p)
				if len(four["move"]) > 0:
					moves.append(four)
		else:
			moves = [{"move": "challenge"},{"move": "no challenge"}]
		return moves

	def make_state(self,p, cur, turn_type):
		value = len(p.hand)
		moves = self.get_moves(p)

		("Moves: ", moves)
		return State(value, moves, self.prev_move, self.turn_num, self, p, turn_type)


	def computer_turn(self):
		"""Executes a computer Player's turn.

		Selects the cards that the computer player will
		put down for their turn, and then calls the finish_turn
		method. The harder the computer player's difficulty, the
		more intelligently they will select the cards, and the
		more likely they are to win.

		"""
		# card_indexes: the indexes of the cards in the computer
		# players hand that they are putting down.
		card_indexes = []

		# If the player only has one card then just chose that one.
		# If the computer player's difficulty is not Difficulty.Easy, or if it is
		# and a random number from 1 to 2 is 1 (50% chance), then find all
		# the cards that the computer player has and can put down without
		# cheating.
		# if (self.c_player.difficulty != Difficulty.easy or \
		# 							randint(1, 2) == 1) and not skip:
		# 	for ind, c in enumerate(self.c_player.hand):
		# 		if c.value == self.c_value:
		# 			card_indexes.append(ind)
		# What the easy computer player does:
		if self.c_player.difficulty == Difficulty.easy:
			# If the computer player already put down some cards from the
			# 50% chance above, half the time leave it and don't add any more.
			# Add either 1, 2, 3 or 4 more random cards
			budget = 2
		# What the medium computer player does:
		elif self.c_player.difficulty == Difficulty.medium:
			budget = 5
		# What the hard computer player does:
		elif self.c_player.difficulty == Difficulty.hard:
			budget = 8
		# print("SIM MODE: TURN")
		cur_state = self.make_state(self.c_player, True, 0)
		cur_node = Node(cur_state)
		best_move = UCTSEARCH(budget,cur_node)
		card_indexes = best_move.state.prev_move["move"]
		try:
			self.finish_turn(card_indexes, best_move.state.prev_move["lying"])
		except KeyError:
			# print("trying again")
			self.computer_turn()
		# UCTSEARCH

	def finish_turn(self, card_indexes, lie):
		"""Finishes the turn.

		Finishes the turn by printing what the player claimed
		to put down, allows the other players to challenge
		by calling the self.get_challenges method, and then
		does different things depending on if there were no
		challenges, if there were but they were incorrect, etc.,
		and then check if the player has won.

		Keyword Arguments:
		card_indexes -- the indexes of the cards that were put down
						- list

		"""
		global turn_ct
		print("{0} put down {1} {2}(s). (lying?: {3})\n".format(
			self.c_player, len(card_indexes), Value.name(self.c_value), lie))
		# cards: The actual Card objects that were put down.
		turn_ct += 1
		cards = [self.c_player.hand[int(i)] for i in card_indexes]
		# challenges: Get the challenges from other players.
		self.prev_move = {"move": card_indexes, "lying": lie}
		challenges = self.get_challenges(len(card_indexes))
		cheat = False
		# If there are any challenges:
		if challenges:
			# Maybe later make this only include one challenge
			for ch in challenges:
				print("Cheat! called by {0}.\n".format(ch.name))
			for c in cards:
				# If the player cheated...
				if c.value != self.c_value:
					cheat = True
					break
			# If the player has cheated:
			if cheat:
				print("{0} Cheated! {0} gets to pick up the pile!\n".format(
					self.c_player), end=' '*6)
				dialouges = random.random()
				if dialouges > 0 and dialouges <= 0.2:
					print("{0}: Haha! Gotcha.".format(ch.name))
				elif dialouges > 0.2 and dialouges <= 0.4:
					print("{0}: I know you too well.".format(ch.name))
				elif dialouges > 0.4 and dialouges <= 0.6:
					print("{0}: You're too easy to guess.".format(ch.name))
				else:
					print("{0}: Oh well! I got you this time.".format(ch.name))
				self.c_player.hand += self.pile
				self.pile = []
			# If the player has not cheated:
			else:
				print("{0} is innocent! {1} gets to pick up the pile!\n".format(
					self.c_player, challenges[0]), end=' '*6)
				dialouges1 = random.random()
				if dialouges1 > 0 and dialouges1 <= 0.2:
					print("{0}: Oops! This is bad.".format(ch.name))
				elif dialouges1 > 0.2 and dialouges1 <= 0.4:
					print("{0}: Oh no... T.T".format(ch.name))
				elif dialouges1 > 0.4 and dialouges1 <= 0.6:
					print("{0}: I can't believe you fall for your trap.".format(ch.name))
				else:
					print("{0}: Oh NO! How can I deal with this pile of cards T.T".format(ch.name))
				for c in cards:
					self.c_player.hand.remove(c)
					self.pile.append(c)
				challenges[0].hand += self.pile
				self.pile = []
		# If the player has not been challenged:
		else:
			print("No one has accused {0} of cheating\n".format(self.c_player),
																  end=' '*6)
			for c in cards:
				self.c_player.hand.remove(c)
				self.pile.append(c)
		if (turn_ct % 5) == 0:
			print("Current Scores -- ", [str(p.name) + ": " + str(len(p.hand)) for p in self.players], "\n")
			sleep(3)
		# input("Press enter to continue...")
		# If the player has won (has no cards left):
		if not self.c_player.hand:
			print("{0} won in {1} place!".format(self.c_player,
								Game.ranks[len(self.winners)]))
			if len([p for p in self.players if not p in self.winners]) > 1:
				print("The game end here.")
				quit()
			input("Press enter to continue.")
			self.winners.append(self.c_player)
		self.next_turn()

	def get_challenges(self, cards_len):
		"""Gets the challenges from other players.

		Combines and returns the lists returned by human_turn
		and computer_turn.

		Keywords Arguments:
		cards_len -- the amount of cards that were put down - int

		"""
		tmp = self.human_challenge(cards_len)
		if len(tmp) > 0:
			return tmp
		else:
			return self.computer_challenge(cards_len)

	def human_challenge(self, cards_len):
		"""Asks the human players if they would like to challenge.

		Asks each human player if they would like to challenge. First
		they are asked if they think the player is cheating, then they
		are told the cards the player claimed to put down and how many
		of that card they have. Then if their input is taken to mean
		that they want to challenge ('cheat' or typos of it), then they
		are added to the returned list of Player objects that challenged.

		Keyword Arguments:
		cards_len -- the amount of cards that were put down - int

		"""
		# Extract instances of Human from the self.players list
		human_players = [p for p in self.players if isinstance(p, Human)
						if p not in self.winners if p != self.c_player]
		if not human_players:
			return []
		shuffle(human_players)
		human_challenges = []
		# Go through each player in human_players and ask if they want
		# to challenge, and give them information like how many cards the
		# the player put down, and how many this human already has.
		for h in human_players:
			num_cards = 0
			for c in h.hand:
				if c.value == self.c_value:
					num_cards += 1
			print("{0}: Do you think {1} is cheating?".format(
				h, self.c_player), end=' '*6)
			input("\n Press enter to continue")
			print("{0} claims to have put down {1} {2}(s).".format(
				self.c_player, cards_len, Value.name(self.c_value)))
			print("You have {0} {1}(s).".format(num_cards,
							Value.name(self.c_value)))
			challenge = input('\n Enter Cheat, or press Enter to pass.')
			# 'cehat', 'chat' - common typos of 'cheat'
			if 'cheat' in challenge.lower() or 'cehat' in challenge.lower() \
											or 'chat' in challenge.lower():
				human_challenges.append(h)
		return human_challenges

#this part need to be modified into an MCTS
	def computer_challenge(self, cards_len):
		"""Gets the challenges from the computer players.

		Gets the challenges from the computer players. Depending
		on the difficulty of the computer player, the intelligence
		in guessing if the player cheated or not is different. This
		makes harder difficulty players harder to beat and makes them
		more likely to win.

		Keyword Arguments:
		cards_len -- the amount of cards that were put down - int

		"""
		# Extract the instances of Computer from the self.players list
		computer_players = [p for p in self.players if not p in self.winners
							if isinstance(p, Computer) if p != self.c_player]
		# If computer_players is empty:
		if not computer_players:
			return []
		shuffle(computer_players)
		computer_challenges = []
		no_comp_challenges = True
		for c in computer_players:
			# Unless the computer player's difficulty is
			# Difficulty.easy, challenge if the number of cards the
			# player put down plus the number of this computer player has is
			# more then four.

			# Easy computer player. . . 
			if c.difficulty == Difficulty.easy:
			    budget = 2
			# Medium computer player . . .
			elif c.difficulty == Difficulty.medium:
			    budget = 5
			# Hard computer player . . .
			elif c.difficulty == Difficulty.hard:
			    budget = 8
			if no_comp_challenges:
				cur_state = self.make_state(c, False, 1)
				cur_node = Node(cur_state)
				best_move = UCTSEARCH(budget,cur_node)
				if best_move.state.prev_move["move"] == "challenge":
					no_comp_challenges = False
					computer_challenges.append(c)
		return computer_challenges

if __name__ == "__main__":
	bs = {}
	game_setup()
