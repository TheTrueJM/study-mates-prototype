// DiscussionBoard - Countdown timer + discussion questions for the current round
// TODO: configuredTime and configuredQuestions should come from SessionSetup via API

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { getStaffSocket } from '../../socket';

function DiscussionBoard() {
  const navigate = useNavigate();

  const [timeRemaining, setTimeRemaining] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [tutorialName, setTutorialName] = useState('');

  useEffect(() => {
    const socket = getStaffSocket();

    const onUpdate = (tutorial) => {
      if (!tutorial) return;
      setTutorialName(`${tutorial.name || 'Tutorial'} - ${tutorial.tutorial_code}`);
      if (tutorial.timer) {
        setTimeRemaining(tutorial.timer.remaining || 0);
        setIsRunning(!!tutorial.timer.running);
      }
      setQuestions(tutorial.questions || []);

      if (tutorial.state === 'lobby') navigate('/staff/tutorial/' + (tutorial.tutorial_code || ''));
      if (tutorial.state === 'groups') navigate('/staff/groups');
    };

    socket.on('tutorial_update', onUpdate);

    return () => {
      socket.off('tutorial_update', onUpdate);
    };
  }, [navigate]);

  const handleNextRound = () => {
    const socket = getStaffSocket();
    socket.emit('start_grouping');
  };

  const handleBackToLobby = () => {
    const socket = getStaffSocket();
    socket.emit('reset_lobby');
  };

  return (
    <div className="container container-md mt-lg">
      <Card title={tutorialName} actions={(
        <Button variant="outline" onClick={handleBackToLobby}>Back to Lobby</Button>
      )}>
        <div className="card-subtitle">Group Discussion</div>

        {/* Timer display */}
        <div className="form-group">
          <label className="input-label">Time Remaining</label>
          <div className="timer-display">
            <div className="timer-value">{`${String(Math.floor(timeRemaining/60)).padStart(2,'0')}:${String(timeRemaining%60).padStart(2,'0')}`}</div>
            <div className="timer-status">
              {isRunning ? 'Timer running' : 'Timer ready'}
            </div>
          </div>
        </div>

        {/* Discussion questions */}
        <div className="mb-md">
          <label className="input-label">Discussion Topics and Questions</label>
          <div className="flex-col gap-xs" style={{ display: 'flex' }}>
            {questions.map((question, index) => (
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
            <Button variant="secondary" onClick={() => getStaffSocket().emit('start_timer')}>
              Start Discussion Timer
            </Button>
          ) : (
            <Button variant="outline" onClick={() => getStaffSocket().emit('stop_timer')}>
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
