import flask
from flask import request, jsonify, abort, Response
import uuid
import json
import ZODB
import ZODB.FileStorage
from user import User
from game import Game
import BTrees


# =======================================
# ============ FLASK SETUP ==============
# =======================================
app = flask.Flask(__name__)
app.config["DEBUG"] = True


# =======================================
# ============= ZODB SETUP ==============
# =======================================
# storage = ZODB.FileStorage.FileStorage('assasins.fs')
db_instance = ZODB.DB(None)  # ZODB.DB(storage)
conn = db_instance.open()
db = conn.root
db.users = BTrees.OOBTree.BTree()
db.games = BTrees.OOBTree.BTree()


# =======================================
# ============= HOME (HEALTH) ===========
# =======================================
@app.route('/', methods=['GET'])
def home():
    return "{\"healthy\":\"true\"}"


# =======================================
# ============= CREATE USER =============
# =======================================
@app.route('/register', methods=['POST'])
def register():
    # Parse & validate fields
    try:
        user_id = request.json['id']
        bio = request.json['bio']
        name = request.json['name']
        fav_loc = request.json['favourite_location']
    except:
        abort(Response("Malformed request"), 400)

    # Check ID is unused
    if user_id in db.users:
        abort(Response("User ID already exists", 400))

    # Create user
    db.users[user_id] = User(user_id, name, bio, fav_loc)

    # Return success
    return "{\"success\":\"true\"}"


# =======================================
# ============= LOOKUP USER =============
# =======================================
@app.route('/user/<user_id>', methods=['GET'])
def user(user_id):
    # Get user
    if not user_id in db.users:
        abort(Response("No user with provided ID exists", 400))
    user = db.users[user_id]

    # Convert to JSON & return
    return json.dumps({
        "id": user.user_id,
        "name": user.name,
        "bio": user.bio,
        "favourite_location": user.favourite_location,
        "game_id": None,
    })


# =======================================
# ============= GET USER QR =============
# =======================================
@app.route('/qr/<user_id>', methods=['GET'])
def user_qr(user_id):
    # Get user
    if not user_id in db.users:
        abort(Response("No user with provided ID exists", 400))
    user = db.users[user_id]

    # Return & QR code
    return json.dumps({
        "id": user.user_id,
        "qr_hash": user.qr_code,
    })


# =======================================
# ============ PERFORM KILL =============
# =======================================
@ app.route('/kill', methods=['POST'])
def kill():
    # Parse & validate fields
    try:
        game_id = request.json['game_id']
        killer_id = request.json['killer_id']
        victim_qr_hash = request.json['victim_qr_hash']
    except:
        abort(Response("Malformed request", 400))

    # Get game if exists
    if not game_id in db.games:
        abort(Response("No game with provided ID exists", 400))
    game = db.games[game_id]

    # Get killer if in game
    if not killer_id in game.player_ids:
        abort(Response("No killer with provided ID exists in game", 400))
    killer = db.users[killer_id]

    # Get victim ID from QR hash
    victim = None
    for player_id in game.player_ids:
        # Get player from DB
        player = db.users[player_id]

        # Check for match
        if player.qr_code == victim_qr_hash:
            victim = player

    # Check for no victim found
    if victim == None:
        abort(Response("No killer in game with provided ID", 400))

    # Check victim is killer's target
    if killer.victim.id != victim.id:
        # TODO

        # Perform kill
    game.perform_kill(killer, victim)

    # Return success
    return "{\"success\":\"true\"}"


# =======================================
# ============= JOIN GAME ===============
# =======================================
@ app.route('/join', methods=['POST'])
def join():
    # Parse & validate fields
    try:
        game_id = request.json['game_id']
        player_id = request.json['player_id']
    except:
        abort(Response("Malformed request"), 400)

    # Get game
    if game_id not in db.games:
        abort(Response("No game with provided ID exists", 400))
    game = db.games[game_id]

    # Get user
    if player_id not in db.users:
        abort(Response("No user with provided ID exists", 400))
    player = db.users[player_id]

    # Check if user is already in the game
    if player.game_id != None:
        abort(Response("Player with provided ID already in game", 400))

    # Check game is not at max capacity
    if len(game.player_ids) >= game.max_players:
        abort(Response("Game is already full", 400))

    # Add user to game
    game.join_player(player_id)
    player.game_id = game_id

    # Return success
    return "{\"success\":\"true\"}"


# =======================================
# ============ CREATE GAME ==============
# =======================================
@app.route('/setup', methods=['POST'])
def game_setup():
    # Parse & validate fields
    try:
        name = request.json['name']
        max_players = request.json['max_players']
        end_date = request.json['end_date']
        location = request.json['location']
    except:
        abort(Response("Malformed request"), 400)

    # Create game object
    game = Game(name, end_date, location, max_players)

    # Re-generate ID if already in use
    while game.game_id in db.games:
        game.game_id = game.gen_id()

    # Persist
    db.games[game.game_id] = game

    # Return ID
    return "{\"id\":\"" + game.game_id + "\"}"


# =======================================
# ========== LOOKUP GAME (ANON) =========
# =======================================
@ app.route('/game/<game_id>', methods=['GET'])
def game_info_anon(game_id):
    # Get game
    if not game_id in db.games:
        abort(Response("No game with provided ID exists", 400))
    game = db.games[game_id]

    # Convert game to JSON & return
    return json.dumps({
        "id": game.game_id,
        "player_ids": game.player_ids,
        "target_ids":  game.targets_map,
        "location": game.location,
        "max_players": game.max_players,
        "end_date": game.end_date,
    })


# =======================================
# ======== LOOKUP GAME (AS USER) ========
# =======================================
@ app.route('/game/<game_id>/<user_id>', methods=['GET'])
def game_info(game_id, user_id):
    # Get game
    if not game_id in db.games:
        abort(Response("No game with provided ID exists", 400))
    game = db.games[game_id]

    # Convert game to JSON & return
    return json.dumps({
        "id": game.game_id,
        "player_ids": game.player_ids,
        "target_ids":  game.targets_map[user_id],
        "location": game.location,
        "max_players": game.max_players,
        "end_date": game.end_date,
    })


# =======================================
# ============ START SERVER =============
# =======================================
app.run()
