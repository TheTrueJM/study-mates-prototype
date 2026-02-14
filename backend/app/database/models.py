from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func


db = SQLAlchemy()


class Staff(db.Model, UserMixin):
    __tablename__ = "staff"

    username = db.Column(db.String(50), primary_key=True)
    password_hash = db.Column(db.String(255), nullable=False)

    invites = db.relationship("AccountInvite", backref="staff")
    
    def __repr__(self):
        return f"{self.id}: {self.username}"
    
    def get_id(self):
        return self.username
    
class AccountInvite(db.Model):
    __tablename__ = "account_invites"

    code = db.Column(db.String(20), primary_key=True)
    staff_username = db.Column(db.String(50), db.ForeignKey("staff.username"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    active = db.Column(db.Boolean, default=True)


class DiscussionCategory(db.Model):
    __tablename__ = "discussion_categories"

    name = db.Column(db.String(25), primary_key=True)
    questions = db.relationship("DiscussionQuestion", backref="discussion_category")

class DiscussionQuestion(db.Model):
    __tablename__ = "discussion_questions"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(100))
    category_name = db.Column(db.String(25), db.ForeignKey("discussion_categories.name"))