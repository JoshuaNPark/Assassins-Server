import uuid
import persistent


# Represents one user of the system which may play in multiple games
class User(persistent.Persistent):

    def __init__(self, user_id, name, bio, favourite_location):
        # Assign attributes
        self.user_id = user_id
        self.name = name
        self.bio = bio
        self.favourite_location = favourite_location

        # Null game_id
        self.game_id = None

        # Generate QR code
        self.qr_code = str(uuid.uuid4())
