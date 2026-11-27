from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f"{self.id}: {self.username}"


class DiscussionCategory(db.Model):
    __tablename__ = "discussion_categories"

    name = db.Column(db.String(25), primary_key=True)
    questions = db.relationship("DiscussionQuestion", backref="discussion_category")

class DiscussionQuestion(db.Model):
    __tablename__ = "discussion_questions"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(100))
    category_name = db.Column(db.String(25), db.ForeignKey("discussion_categories.name"))