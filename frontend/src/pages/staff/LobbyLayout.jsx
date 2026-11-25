import { useState } from "react";
import { QRCodeSVG } from "qrcode.react";

import { useTutorial } from "../../contexts/TutorialContext";

import Button from "../../components/Button";
import Modal from "../../components/Modal";


export default function LobbyLayout({ code, students = {}, availableAttributes = [], onGrouping, busy = false }) {
  const { notify } = useTutorial();
  const [enlarged, setEnlarged] = useState(false);

  // Scanning the QR Code opens the Session directly, joining it automatically
  const joinUrl = `${window.location.origin}/tutorial/${code}`;

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(joinUrl);
      notify("Join Link Copied.", "success");
    } catch {
      notify("The Link couldn't be Copied. Students can enter the Code instead.", "error");
    }
  };

  const entries = Object.entries(students);
  const noDetailsRequired = availableAttributes.length === 0;
  const isReady = (student) => noDetailsRequired || !!student.attributes_complete;
  const readyCount = entries.filter(([, student]) => isReady(student)).length;

  return (
    <>
      {/* Tutorial code + QR code area */}
      <div className="join-panel mb-lg">
        <div className="join-panel-text">
          <span className="eyebrow">Join Code</span>
          <div className="join-code">
            <div className="code-value">{code}</div>
          </div>
          <p className="join-instructions">
            Go to <strong>{window.location.host}</strong> and enter this Code, or scan the QR Code.
          </p>
          <p className="text-muted">No Accounts or Personal Details Needed.</p>
          <div className="join-actions">
            <Button variant="outline" size="sm" onClick={() => setEnlarged(true)}>Show Fullscreen</Button>
            <Button variant="outline" size="sm" onClick={copyLink}>Copy Join Link</Button>
          </div>
        </div>
        <button
          type="button"
          className="qr-code-container qr-button"
          onClick={() => setEnlarged(true)}
          aria-label="Enlarge QR Code"
        >
          <QRCodeSVG value={joinUrl} size={256} level="M" marginSize={0} className="qr-image" title={`Join Session ${code}`} />
        </button>
      </div>

      <Modal title="Join this session" isOpen={enlarged} onClose={() => setEnlarged(false)} size="lg">
        <div className="join-fullscreen">
          <div className="join-fullscreen-qr">
            <QRCodeSVG value={joinUrl} size={512} level="M" marginSize={0} className="qr-image" title={`Join Session ${code}`} />
          </div>
          <div className="join-fullscreen-text">
            <p className="join-instructions">Scan the QR Code, or go to <strong>{window.location.host}</strong> and Enter</p>
            <div className="join-code">
              <div className="code-value">{code}</div>
            </div>
          </div>
        </div>
      </Modal>

      {/* Joined students grid */}
      <section className="mb-md">
        <div className="section-header">
          <h2 className="section-title">Students</h2>
          <span className="text-muted">{entries.length} Joined · {readyCount} Ready</span>
        </div>

        {entries.length === 0 ? (
          <div className="empty-state">Waiting for Students to join…</div>
        ) : (
          <div className="grid grid-responsive">
            {entries.map(([uuid, student]) => {
              const ready = isReady(student);
              return (
                <div key={uuid} className={`student-chip ${ready ? "is-ready" : "is-pending"}`}>
                  {ready && <span className="student-chip-check" aria-hidden="true">✓</span>}
                  {student.name || "Unknown"}
                  <span className="sr-only">{ready ? " (ready)" : " (still adding details)"}</span>
                </div>
              );
            })}
          </div>
        )}

        {entries.length > readyCount && (
          <p className="input-hint mt-xs">Students with a dashed outline are still adding Details. You can start without them.</p>
        )}
      </section>

      <Button variant="secondary" fullWidth onClick={onGrouping} disabled={entries.length < 2 || busy}>
        {busy ? "Forming Groups…" : "Begin Group Formation"}
      </Button>
      {entries.length < 2 && (
        <p className="input-hint text-center mt-xs">At least 2 Students need to join before Groups can be Formed.</p>
      )}
    </>
  );
}
