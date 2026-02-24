from flask_bcrypt import generate_password_hash
import os

from .database import db, Staff, DiscussionCategory, DiscussionQuestion


DISCUSSION = {
    "academic": [
        "What are your career goals after graduation, and how do you plan to achieve them?",
        "Which study techniques work best for you, and why?",
        "What aspect of your degree interests you the most?",
        "How do you prefer to communicate and organize work when collaborating in a team?",
        "What is an academic challenge you are currently working to overcome?",
        "What personal responsibility do you feel you hold in ensuring a group's success?",
        "Do you prefer to complete work quickly, or do you tend to wait until the deadline approaches?"
    ],
    "casual": [
        "What is your favorite video game, and what do you enjoy most about it?",
        "If you could live in any fictional world, which would you choose and why?",
        "What is something small that can always improve your mood?",
        "How do you like to relax or unwind after a long day?",
        "What is your favorite food, and how often could you eat it?",
        "Who is your most frequently listened to musician?",
        "What is your dream holiday destination, and what makes it appealing to you?"
    ],
    "study": [
        "Which unit or subject did you enjoy the most, and why?",
        "What is your favorite study spot, and what makes it ideal for you?",
        "What one piece of advice would you give to someone starting this course, and why?",
        "Can you share a mistake you made academically that ended up helping you grow?",
        "When did you realize that you wanted to study your chosen course?",
        "Who is your favorite productive or educational YouTube channel, and why?",
        "What is your favorite part of university life, and what do you hope to gain from it?"
    ]
}


def populate_discussion_categories():
    for category in DISCUSSION:
        db.session.add(DiscussionCategory(name=category))
        db.session.commit()


def populate_discussion_questions():
    for category in DISCUSSION:
        for question in DISCUSSION[category]:
            db.session.add(DiscussionQuestion(question=question, category_name=category))
            db.session.commit()


def populate_discussions():
    if DiscussionCategory.query.count():
        return

    populate_discussion_categories()
    populate_discussion_questions()


def create_staff_admin():
    if Staff.query.first():
        return

    username = os.getenv("ADMIN_USERNAME", "StaffAdmin")
    password_hash = generate_password_hash(os.getenv("ADMIN_PASSWORD", "We'reGettingHacked!"))
    db.session.add(Staff(username=username, password_hash=password_hash))
    db.session.commit()


def populate_all():
    populate_discussions()
    create_staff_admin()