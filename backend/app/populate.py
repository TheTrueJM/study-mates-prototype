from flask_bcrypt import generate_password_hash
import os

from .database import db, Staff, DiscussionCategory, DiscussionQuestion


DISCUSSION = {
    "academic": [
        "What are your career goals after graduation?",
        "What study techniques work best for you?",
        "What aspect of this degree interests you most?",
        "How do you prefer to communicate and organise work in a team?",
        "What's one academic challenge you're currently working to improve?",
        "What responsibility do you think you personally hold in making a group succeed?",
        "Do you like to get work done fast, or do you tend to leave it to the due date?"
        ],
    "casual": [
        "What is your favourite video game?",
        "What fictional world would you actually choose to live in, and why?",
        "What is something small that can always improve your moood?",
        "How do you like to unwind after a long day?",
        "What is your favourite food?",
        "Who is your most played music artist?",
        "Where is your dream holiday destination?"
    ],
    "study": [
        "What unit did you enjoy the most?",
        "What is your favourite study spot, and why?",
        "What is one piece of advice you would give to someone starting this course?",
        "What's a mistake you made academically that ended up helping you grow?",
        "When did you realise you wanted to study your course?",
        "Who is your favourite productive/educational YouTuber?",
        "What is your favourite part of university"
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