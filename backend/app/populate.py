from .database import db, DiscussionCategory, DiscussionQuestion


# Questions are kept under 100 characters (the column's length)
DISCUSSION = {
    "academic": [
        "What are your career goals after graduation, and how do you plan to achieve them?",
        "Which study techniques work best for you, and why?",
        "What aspect of your degree interests you the most?",
        "How do you prefer to communicate and organize work when collaborating in a team?",
        "What is an academic challenge you are currently working to overcome?",
        "What personal responsibility do you feel you hold in ensuring a group's success?",
        "Do you prefer to complete work quickly, or do you tend to wait until the deadline approaches?",
        "What skill do you most want to improve before you graduate?",
        "How do you think tasks should be split up fairly in a group assignment?",
        "What does a great teammate look like to you?",
        "How do you prefer to handle disagreements within a group project?",
        "What role do you usually end up taking in a team, and do you enjoy it?",
        "Would you rather work at a startup or a large company, and why?",
        "What is something outside of your degree that you are teaching yourself right now?"
    ],
    "casual": [
        "What is your favorite video game, and what do you enjoy most about it?",
        "If you could live in any fictional world, which would you choose and why?",
        "What is something small that can always improve your mood?",
        "How do you like to relax or unwind after a long day?",
        "What is your favorite food, and how often could you eat it?",
        "Who is your most frequently listened to musician?",
        "What is your dream holiday destination, and what makes it appealing to you?",
        "What is a hobby you have picked up recently, or would like to try?",
        "What is the best show or movie you have watched lately?",
        "If you could instantly master any skill, what would it be?",
        "What is your go-to snack or drink while studying?",
        "Which app on your phone could you not live without?",
        "Are you more of a morning person or a night owl?",
        "What is the most interesting place you have lived in or visited?"
    ],
    "study": [
        "Which unit or subject did you enjoy the most, and why?",
        "What is your favorite study spot, and what makes it ideal for you?",
        "What one piece of advice would you give to someone starting this course, and why?",
        "Can you share a mistake you made academically that ended up helping you grow?",
        "When did you realize that you wanted to study your chosen course?",
        "Who is your favorite productive or educational YouTube channel, and why?",
        "What is your favorite part of university life, and what do you hope to gain from it?",
        "Which programming language or tool would you recommend to a first year, and why?",
        "How do you stay focused when studying at home?",
        "What is your strategy for preparing for exams?",
        "Do you prefer studying alone or with others, and why?",
        "What resource (a website, book, or tool) has helped you the most in your studies?",
        "How do you take notes in lectures and tutorials?",
        "What do you do when you get stuck on a problem or a bug?"
    ]
}


def populate_discussions():
    """Adds any Categories and Questions the Database doesn't have yet (so existing databases get new questions)"""
    categories = {category.name for category in DiscussionCategory.query.all()}
    questions = {(question.category_name, question.question) for question in DiscussionQuestion.query.all()}

    for category, category_questions in DISCUSSION.items():
        if category not in categories:
            db.session.add(DiscussionCategory(name=category))
        for question in category_questions:
            if (category, question) not in questions:
                db.session.add(DiscussionQuestion(question=question, category_name=category))

    db.session.commit()


def populate_all():
    populate_discussions()
