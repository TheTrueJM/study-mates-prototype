import { useEffect, useId, useRef } from "react";

export default function Modal({ title, isOpen, onClose, children, footer, size = "md" }) {
  const titleId = useId();
  const contentRef = useRef(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!isOpen) return;

    // Close on Escape, Prevent the Page behind from Scrolling, and Restore Focus Afterwards
    const previouslyFocused = document.activeElement;
    const handleKey = (event) => {
      if (event.key === "Escape") onCloseRef.current?.();
    };
    const previousOverflow = document.body.style.overflow;

    document.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";
    contentRef.current?.focus();

    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = previousOverflow;
      previouslyFocused?.focus?.();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        ref={contentRef}
        className={`modal-content modal-${size}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id={titleId}>{title}</h2>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">&times;</button>
        </div>
        <div className="modal-body">
          {children}
        </div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}
