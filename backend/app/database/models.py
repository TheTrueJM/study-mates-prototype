from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone


db = SQLAlchemy()


class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f"{self.id}: {self.username}"


def _now():
    return datetime.now(timezone.utc)


class SavedAttribute(db.Model):
    """A Custom Detail saved to a Staff Account, to be reused in their Tutorials"""
    __tablename__ = "saved_attributes"

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True)
    definition = db.Column(db.JSON, nullable=False) # { label, hint, options, multiple, matching }
    updated_at = db.Column(db.DateTime(timezone=True), default=_now, onupdate=_now)

    def to_dict(self):
        return {"id": self.id, **self.definition}


class TutorialPreset(db.Model):
    """Tutorial Settings saved to a Staff Account, to quickly set up their Tutorials"""
    __tablename__ = "tutorial_presets"

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    settings = db.Column(db.JSON, nullable=False) # As accepted when creating a Tutorial
    updated_at = db.Column(db.DateTime(timezone=True), default=_now, onupdate=_now)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "settings": self.settings}


class DiscussionCategory(db.Model):
    __tablename__ = "discussion_categories"

    name = db.Column(db.String(25), primary_key=True)
    questions = db.relationship("DiscussionQuestion", backref="discussion_category")

class DiscussionQuestion(db.Model):
    __tablename__ = "discussion_questions"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(100))
    category_name = db.Column(db.String(25), db.ForeignKey("discussion_categories.name"))