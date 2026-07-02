import Button from '../../components/Button';

import QRCode from '/static/Application-QR.svg';


export default function LobbyLayout({ code, students = {}, onGrouping }) {
  return (
    <>
      {/* Tutorial code + QR code area */}
      <div className="mb-lg">
        <label className="input-label">Join Code</label>
        <div className="flex gap-md">
          <div className="join-code">
            <div className="code-value">{code}</div>
          </div>
          <div className="qr-code-container">
            {/* TODO: Update Link and QR Code (Automatically Generate with Tutorial Code) */}
            <img src={QRCode} alt="Tutorial QR Code" className="qr-image" />
          </div>
        </div>
      </div>

      {/* Joined students grid */}
      <div className="mb-md">
        {/* TODO: Calculate "Ready" Students (Details Complete) and Display Ready/Joined Value */}
        <div className="input-label">Students Joined: {students.length}</div>
        <div className="grid grid-responsive">
          {Object.entries(students).map(([uuid, details]) => (
            // TODO: Highlight "Ready" Students (Details Complete)
            <div key={uuid} className="student-chip">{details.name || "Unknown"}</div>
          ))}
        </div>
      </div>

      <Button variant="secondary" fullWidth onClick={onGrouping}>
        Begin Group Formation
      </Button>
    </>
  );
}