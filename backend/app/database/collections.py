from app.database.connection import get_database


def urls_collection():
    return get_database()["urls"]


def analytics_collection():
    return get_database()["analytics"]


def reports_collection():
    return get_database()["reports"]