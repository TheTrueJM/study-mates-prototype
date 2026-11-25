import { useTutorial } from "../contexts/TutorialContext";

export default function ConnectionBanner() {
  const { connected, connectionLost } = useTutorial();

  if (connected || !connectionLost) return null;

  return (
    <div className="connection-banner" role="status">
      <span className="spinner" aria-hidden="true" />
      Connection Lost. Reconnecting…
    </div>
  );
}
