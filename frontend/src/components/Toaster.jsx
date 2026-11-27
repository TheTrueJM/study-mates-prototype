import { useTutorial } from "../contexts/TutorialContext";

export default function Toaster() {
  const { toasts, dismissToast } = useTutorial();

  return (
    <div className="toast-region" aria-live="polite">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast toast-${toast.type}`} role={toast.type === "error" ? "alert" : "status"}>
          <span className="toast-message">{toast.message}</span>
          <button type="button" className="toast-close" onClick={() => dismissToast(toast.id)} aria-label="Dismiss">
            &times;
          </button>
        </div>
      ))}
    </div>
  );
}
