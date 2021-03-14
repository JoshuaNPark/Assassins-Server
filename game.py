import uuid
import string
import random
import json
import persistent


# Represents a single game
class Game(persistent.Persistent):

    # Class attributes
    CODE_CHARS = string.ascii_uppercase + string.digits

    # Generate a 4-letter random ID
    def gen_id(self):
        return ''.join(random.choice(self.CODE_CHARS)
                       for i in range(4))

    def __init__(self, name, end_date, location, max_players):
        # Assign attributes
        self.name = name
        self.end_date = end_date
        self.location = location
        self.max_players = max_players

        # Generate ID
        self.game_id = self.gen_id()

        # Instantiate ID lists
        self.player_ids = []
        self.player_scores_map = {}
        self.dead_player_ids = []
        self.targets_map = {}

        # Not started
        self.started = False

        # Not ended
        self.ended = False
        self.winner_id = None

    # Joins a player to the game if space
    # Returns false if game is full
    def join_player(self, player_id):
        if (len(self.player_ids) >= self.max_players):
            # Game full
            raise Exception()

        # Add player to game
        self.player_ids.append(player_id)

        # Assigns the score 0 to the new player
        self.player_scores_map[player_id] = 0

    # Initialises game & assigns targets
    def start_game(self):
        self.started = True

        # Assigns targets to all the players
        random.shuffle(self.player_ids)
        for i in range(len(self.player_ids) - 1):
            self.targets_map[self.player_ids[i]] = self.player_ids[i+1]

        self.targets_map[self.player_ids[len(
            self.player_ids) - 1]] = self.player_ids[0]

    # Perform a kill action
    def perform_kill(self, killer, victim):
        # Add player to dead list
        self.dead_player_ids.append(victim.user_id)

        # Increase killer's score
        self.player_scores_map[killer.user_id] += 1

        # Assign victim's target to killer
        self.targets_map[killer.user_id] = self.targets_map[victim.user_id]

        # Check there is only 1 alive player
        if len(self.dead_player_ids) == len(self.player_ids) - 1:
            self.ended = True
            self.winner_id = list(set(self.player_ids) -
                                  set(self.dead_player_ids))[0]
