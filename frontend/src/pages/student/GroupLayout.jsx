export default function GroupLayout({ state = 'groups', username, groupNumber, groupMembers = [], questions = [], timeRemaining = 0, isRunning = false }) {
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
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
                <div key={member} className="member-card">
                  <div className="member-name">{member}</div>
                </div>
              ))}
            </div>
          </>
        )}

        <div className="divider mt-md">
          <p style={{ fontSize: '0.875rem', color: '#888' }}>
            Discuss the Topics and Questions to get to know your Group Members!
          </p>
        </div>
    </>
  );
}