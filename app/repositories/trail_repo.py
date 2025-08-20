from models.trail import Trail

def get_all_trails(db):
    return db.query(Trail).all()