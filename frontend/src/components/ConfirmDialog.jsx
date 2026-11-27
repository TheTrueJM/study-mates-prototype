import Modal from "./Modal";
import Button from "./Button";

export default function ConfirmDialog({
  isOpen, title, message, confirmLabel = "Confirm", cancelLabel = "Cancel", danger = false, busy = false, onConfirm, onCancel,
}) {
  return (
    <Modal
      title={title}
      isOpen={isOpen}
      onClose={onCancel}
      size="sm"
      footer={
        <div className="btn-group">
          <Button variant="outline" onClick={onCancel} disabled={busy}>{cancelLabel}</Button>
          <Button variant={danger ? "danger-solid" : "primary"} onClick={onConfirm} disabled={busy}>
            {busy ? "Please wait…" : confirmLabel}
          </Button>
        </div>
      }
    >
      <p>{message}</p>
    </Modal>
  );
}
