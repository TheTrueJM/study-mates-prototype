// DiscussionBoard - Countdown timer + discussion questions for the current round
// TODO: configuredTime and configuredQuestions should come from SessionSetup via API

import { useState, useEffect } from 'react';
import Card from '../../components/Card';
import Button from '../../components/Button';

function DiscussionBoard() {
  // Placeholder config (will come from session setup)
  const configuredTime = 10; // minutes
  const configuredQuestions = [
    'What are your career goals after graduation?',
    'What study techniques work best for you?',
    'What aspect of this course interests you most?',
    'How do you prefer to collaborate on group projects?',
  ];

  const [timeRemaining, setTimeRemaining] = useState(configuredTime * 60); // in seconds
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
    <div className="container container-md mt-lg">
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
  );
}

export default DiscussionBoard;
