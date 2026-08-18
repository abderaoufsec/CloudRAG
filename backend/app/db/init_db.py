from app.db.database import Base, engine

# Import models so SQLAlchemy knows about them.
from app.models.document import Document  # noqa: F401


def initialize_database():
    Base.metadata.create_all(
        bind=engine,
    )