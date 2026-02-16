// DiscussionBoard - Countdown timer + discussion questions for the current round
// Receives timeMinutes and questions as props from parent (fetched from backend API)

import { useState, useEffect } from 'react';
import Card from '../../components/Card';
import Button from '../../components/Button';

function DiscussionBoard({ timeMinutes = 10, questions = [] }) {
  // timeMinutes and questions will come from backend API via props
  // Defaults are placeholders for development only
  const defaultQuestions = [
    'What are your career goals after graduation?',
    'What study techniques work best for you?',
    'What aspect of this course interests you most?',
    'How do you prefer to collaborate on group projects?',
  ];
  const configuredQuestions = questions.length > 0 ? questions : defaultQuestions;

  const [timeRemaining, setTimeRemaining] = useState(timeMinutes * 60);
  const [isRunning, setIsRunning] = useState(false);

  // Timer countdown effect - runs every second while isRunning is true
  useEffect(() => {
    if (!isRunning) return;

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 0) {
          setIsRunning(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isRunning]);

  // Format seconds as MM:SS
  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;
  const display = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

  const handleNextRound = () => {
    console.log('Next group forming round');
    // TODO: Call API -> navigate to /staff/groups
  };

  return (
    <div className="page">
      <div className="container container-md">
      <Card title="Discussion Round in Progress">

        {/* Timer display */}
        <div className="form-group">
          <label className="input-label">Time Remaining</label>
          <div className="timer-display">
            <div className="timer-value">{display}</div>
            <div className="timer-status">
              {isRunning ? 'Timer running' : 'Timer ready'}
            </div>
          </div>
        </div>

        {/* Discussion questions */}
        <div className="mb-md">
          <label className="input-label">Discussion Topics / Ice-Breaker Questions</label>
          <div className="flex-col gap-xs" style={{ display: 'flex' }}>
            {configuredQuestions.map((question, index) => (
              <div key={index} className="question-item">
                <div className="question-number">{index + 1}</div>
                <div>{question}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Action buttons - toggles between Start/End */}
        <div className="btn-group">
          {!isRunning ? (
            <Button variant="secondary" onClick={() => setIsRunning(true)}>
              Start Discussion Timer
            </Button>
          ) : (
            <Button variant="outline" onClick={() => setIsRunning(false)}>
              End Discussion Early
            </Button>
          )}
          <Button variant="primary" onClick={handleNextRound}>
            Next Group Forming Round
          </Button>
        </div>

      </Card>
      </div>
    </div>
  );
}

export default DiscussionBoard;
