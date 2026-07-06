import { Modal } from "./Modal";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  busy?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  danger = false,
  busy = false,
  onConfirm,
  onClose,
}: ConfirmDialogProps) {
  return (
    <Modal
      open={open}
      title={title}
      onClose={busy ? () => undefined : onClose}
      footer={
        <div className="form-actions">
          <button
            type="button"
            className={danger ? "btn btn-danger" : "btn btn-primary"}
            disabled={busy}
            onClick={onConfirm}
          >
            {busy ? "Working…" : confirmLabel}
          </button>
          <button type="button" className="btn btn-ghost" disabled={busy} onClick={onClose}>
            {cancelLabel}
          </button>
        </div>
      }
    >
      <p>{message}</p>
    </Modal>
  );
}
