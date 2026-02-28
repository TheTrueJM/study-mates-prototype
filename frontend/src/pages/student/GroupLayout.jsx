import { useState } from 'react';
import Button from '../../components/Button';
import Modal from '../../components/Modal';

export default function GroupLayout({ state = 'groups', username, groupNumber, groupMembers = [], questions = [], timeRemaining = 0, isRunning = false }) {
  const [expandedMember, setExpandedMember] = useState(null);
  const [showQuestionsModal, setShowQuestionsModal] = useState(false);
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };


  const toggleMember = (name) => {
    setExpandedMember(expandedMember === name ? null : name);
  };

  return (
    <>
        {groupNumber === null ? (
          <div className="text-center">
            <p>Waiting for Group Formation...</p>
          </div>
        ) : (
          <>
            <div className="card-subtitle">Group {groupNumber}</div>

            {state === 'discussion' && (
              <div className="timer-display mb-md">
                <div className="timer-value">{formatTime(timeRemaining)}</div>
                <div className="timer-status">Remaining Discussion Time</div>
              </div>
            )}

            <div className="flex-col gap-xs" style={{ display: 'flex' }}>
              {groupMembers.map((member) => (
                <div
                  key={member.name}
                  className={`member-card ${member.name === username ? 'current-user' : ''}`}
                  style={{ cursor: 'pointer' }}
                  onClick={() => toggleMember(member.name)}
                >
                  <div className="member-name">{member.name}</div>
                  {expandedMember === member.name && member.availability && (
                    <div className="member-availability" style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#666' }}>
                      <strong>Availability:</strong> {member.availability.join(', ') || 'None specified'}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}

        {state === 'discussion' && (
          <div className="divider mt-md">
            <Button variant="secondary" onClick={() => setShowQuestionsModal(true)} fullWidth>
              View Discussion Topics
            </Button>

            <p className="mt-sm" style={{ fontSize: '0.875rem', color: '#888' }}>
              Discuss the Topics and Questions to get to know your Group Members!
            </p>
          </div>
        )}

        {showQuestionsModal && (
          <Modal title="Discussion Topics/Questions" onClose={() => setShowQuestionsModal(false)}>
            {questions.length === 0 ? (
              <p style={{ color: '#888' }}>No topics available yet.</p>
            ) : (
              <div className="flex-col gap-xs" style={{ display: 'flex' }}>
                {questions.map((question, index) => (
                  <div key={index} className="question-item">
                    <div className="question-number">{index + 1}</div>
                    <div>{question}</div>
                  </div>
                ))}
              </div>
            )}
          </Modal>
        )}
    </>
  );
}

