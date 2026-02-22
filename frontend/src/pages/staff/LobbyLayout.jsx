// LobbyLayout - Staff sees tutorial code and students joining in real-time
import Button from '../../components/Button';
import QRCode from '../../static/Application-QR.svg';

export default function LobbyLayout({ tutorialCode, students = {}, onGrouping }) {
  const studentList = Object.values(students || {}).map(s => s.name || 'Unknown');

  return (
    <>
      {/* Tutorial code + QR code area */}
      <div className="mb-lg">
        <label className="input-label">Join Code</label>
        <div className="flex gap-md">
          <div className="join-code">
            <div className="code-value">{tutorialCode}</div>
          </div>
          <div className="qr-code-container">
            <img src={QRCode} alt="Tutorial QR Code" className="qr-image" />
          </div>
        </div>
      </div>

      {/* Joined students grid */}
      <div className="mb-md">
        <div className="input-label">Students Joined: {studentList.length}</div>
        <div className="grid grid-responsive">
          {studentList.map((student) => (
            <div key={student} className="student-chip">{student}</div>
          ))}
        </div>
      </div>

      <Button variant="secondary" fullWidth onClick={onGrouping}>
        Begin Group Formation
      </Button>
    </>
  );
}
