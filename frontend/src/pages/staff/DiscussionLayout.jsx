// DiscussionBoard - Staff shows the discussion questions and the timer to students
import React from 'react';
import Input from '../../components/Input';
import Button from '../../components/Button';

export default function DiscussionLayout({ timeRemaining = 0, isRunning = false, resetTime = 10, setResetTime = () => {}, questions = [], onResetTimer, onStartTimer, onStopTimer, onGrouping }) {
  return (
    <>
      <div className="card-subtitle">Group Discussion</div>

      {/* Timer display */}
      <div className="form-group">
        <label className="input-label">Time Remaining</label>
        <div className="timer-display">
          <div className="timer-value">{`${String(Math.floor(timeRemaining/60)).padStart(2,'0')}:${String(timeRemaining%60).padStart(2,'0')}`}</div>
          <div className="timer-status">{isRunning ? 'Timer running' : 'Timer ready'}</div>
        </div>
      </div>

      {/* Timer controls */}
      <div className="form-group">
        <div className="flex gap-sm items-center">
          <input
            type="number"
            className="input"
            value={resetTime}
            min="1"
            max="60"
            placeholder="10..."
            onChange={(e) => setResetTime(Number(e.target.value))}
            style={{ width: '80px' }}
          />
          <span>minutes</span>
          <Button variant="outline" onClick={onResetTimer}>Reset Timer</Button>
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

      <div className="btn-group">
        {!isRunning ? (
          <Button variant="secondary" onClick={onStartTimer}>Resume Discussion Timer</Button>
        ) : (
          <Button variant="outline" onClick={onStopTimer}>Pause Discussion Timer</Button>
        )}
        <Button variant="primary" onClick={onGrouping}>Next Group Forming Round</Button>
      </div>
    </>
  );
}
