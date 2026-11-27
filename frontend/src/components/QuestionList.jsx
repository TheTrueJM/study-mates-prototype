export default function QuestionList({ questions = [] }) {
  if (!questions.length) {
    return <p className="text-muted">No Discussion Prompts Yet.</p>;
  }

  return (
    <ol className="question-list">
      {questions.map((question, index) => (
        <li key={index} className="question-item">
          <span className="question-number" aria-hidden="true">{index + 1}</span>
          <span>{question}</span>
        </li>
      ))}
    </ol>
  );
}
