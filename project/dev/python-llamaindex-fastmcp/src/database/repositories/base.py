from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

class BaseRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, instance):
        self.session.add(instance)
        self.session.commit()
        return instance

    def get(self, model, id):
        instance = self.session.query(model).get(id)
        if instance is None:
            raise NoResultFound(f"{model.__name__} with id {id} not found.")
        return instance

    def update(self, instance):
        self.session.commit()
        return instance

    def delete(self, instance):
        self.session.delete(instance)
        self.session.commit()