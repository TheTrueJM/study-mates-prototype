// GroupView - Student sees their assigned group members
// TODO: Replace dummy data with API response

import Card from '../../components/Card';

function GroupView() {
  // Placeholder data (will come from backend)
  const groupMembers = [
    {
      name: 'Anonymous-Wombat-42',
      gradeExpectation: '6.0',
      currentGPA: '5.2',
      times: ['Mon Morning', 'Wed Afternoon'],
    },
    {
      name: 'Random-Koala-17',
      gradeExpectation: '6.5',
      currentGPA: '6.0',
      times: ['Mon Morning', 'Fri Evening'],
    },
    {
      name: 'Mystery-Dolphin-89',
      gradeExpectation: '6.8',
      currentGPA: '6.2',
      times: ['Tue Afternoon', 'Wed Afternoon', 'Thu Evening', 'Fri Evening'],
    },
    {
      name: 'Unknown-Eagle-23',
      gradeExpectation: '6.2',
      currentGPA: '5.8',
      times: ['Mon Morning', 'Thu Evening'],
    },
  ];

  return (
    <div className="page">
      <div className="container container-md">
      <Card title="Tutorial Session ABCD-1234">
        <div className="card-subtitle">Group 1</div>

        {/* Member list */}
        <div className="flex-col gap-xs" style={{ display: 'flex' }}>
          {groupMembers.map((member) => (
            <div key={member.name} className="member-card">
              <div className="member-name">{member.name}</div>

              <div className="member-info">
                <div>
                  <strong>GPA Expectation:</strong> {member.gradeExpectation}
                  {' | '}
                  <strong>Current GPA:</strong> {member.currentGPA}
                </div>
                <div>
                  <strong>Available:</strong>{' '}
                  {/* Show all times if <= 3, otherwise show first 2 + "+X more" */}
                  {member.times.length <= 3 ? (
                    member.times.join(', ')
                  ) : (
                    <>
                      {member.times.slice(0, 2).join(', ')}
                      <span className="text-muted"> +{member.times.length - 2} more</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="divider mt-md">
          <p style={{ fontSize: '0.875rem', color: '#888' }}>
            Discuss and exchange contact information with your group members
          </p>
        </div>
      </Card>
      </div>
    </div>
  );
}

export default GroupView;
