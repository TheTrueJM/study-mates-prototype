from app.database import db, DiscussionQuestion
from app.populate import DISCUSSION, populate_discussions


def test_every_question_is_added_once(app):
    populate_discussions()
    populate_discussions()
    for category, questions in DISCUSSION.items():
        stored = [q.question for q in DiscussionQuestion.query.filter_by(category_name=category)]
        assert sorted(stored) == sorted(questions)

def test_new_questions_are_added_to_existing_databases(app):
    question = DiscussionQuestion.query.filter_by(question=DISCUSSION["casual"][-1]).first()
    db.session.delete(question)
    db.session.commit()

    populate_discussions()
    assert DiscussionQuestion.query.filter_by(question=DISCUSSION["casual"][-1]).count() == 1

def test_questions_fit_their_column():
    assert all(len(question) <= 100 for questions in DISCUSSION.values() for question in questions)
