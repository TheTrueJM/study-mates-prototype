from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func


db = SQLAlchemy()


class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(db.String(25), primary_key=True) # Could be changed to non-identifiable id
    username = db.Column(db.String(51), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    firstname = db.Column(db.String(25)) # Could be removed for non-identifiable
    surname = db.Column(db.String(25)) # Could be removed for non-identifiable
    
    def __repr__(self):
        return f"{self.id}: {self.username}"
    
class Tutorial(db.Model):
    __tablename__ = "tutorials"

    code = db.Column(db.String(6), primary_key=True)
    staff_id = db.Column(db.String(25), db.ForeignKey("staff.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    in_lobby = db.Column(db.Boolean, default=True)

    students = db.relationship("Student", backref="tutorial")
    groups = db.relationship("Group", backref="tutorial")
    
    def __repr__(self):
        return f"{self.code} by {self.staff_id}"


class TimePeriod(db.Model): # NOTE: This will need to be prefilled with the codes
    __tablename__ = "time_periods"

    code = db.Column(db.String(4), primary_key=True) # e.g. MONM (Monday Morning), TUEA (Tuesday Afternoon), WEDN (Wednesday Night)

    def __repr__(self):
        return f"{self.code}"

class Availability(db.Model):
    __tablename__ = "availabilities"

    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), primary_key=True)
    time_period_code = db.Column(db.String(4), db.ForeignKey("time_period.code"), primary_key=True)

    def __repr__(self):
        return f"{self.student_id} - {self.time_period_id}"


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True) # Can change to string UUID
    tutorial_code = db.Column(db.String(6), db.ForeignKey("tutorial.code"))
    username = db.Column(db.String(50), nullable=False)
    currentGPA = db.Column(db.Float, default=None)
    goalGPA = db.Column(db.Float, default=4)
    availability = db.relationship("Availability", backref="student")

    # Combine (Union) these lists when handling Matches
    matchesAsA = db.relationship("StudentMatch", foreign_keys="[StudentMatch.studentA_id]", backref="student")
    matchesAsB = db.relationship("StudentMatch", foreign_keys="[StudentMatch.studentB_id]", backref="student")
    
    @property
    def matches(self):
        return [
            m.studentB_id if m.studentA_id == self.id else m.studentA_id
            for m in self.matchesAsA.union(self.matchesAsB)
        ]

    def __repr__(self):
        return f"{self.id}: {self.username}"


class Group(db.Model):
    __tablename__ = "groups"

    num = db.Column(db.Integer, primary_key=True)
    tutorial_code = db.Column(db.String(6), db.ForeignKey("tutorial.code"), primary_key=True)

class GroupMember(db.Model):
    __tablename__ = "group_members"

    group_num = db.Column(db.Integer, db.ForeignKey("num"), primary_key=True)
    tutorial_code = db.Column(db.String(6), db.ForeignKey("group.tutorial_code"), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), primary_key=True)

class StudentMatch(db.Model): # NOTE: Store students as (min(A_id, B_id), max(A_id, B_id)) to not need symmetric storage
    __tablename__ = "student_matches"

    studentA_id = db.Column(db.Integer, db.ForeignKey("student.id"), primary_key=True)
    studentB_id = db.Column(db.Integer, db.ForeignKey("student.id"), primary_key=True)



class DiscussionCategory(db.Model):
    __tablename__ = "discussion_categories"

    name = db.Column(db.String(25), primary_key=True)
    questions = db.relationship("discussion_question", backref="discussion_category")

class DiscussionQuestion(db.Model):
    __tablename__ = "discussion_questions"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(100))
    category_name = db.Column(db.String(25), db.ForeignKey("discussion_category.name"))