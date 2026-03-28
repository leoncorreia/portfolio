type Props = { message: string | null; onDismiss?: () => void };

export function ErrorBanner({ message, onDismiss }: Props) {
  if (!message) return null;
  return (
    <div className="banner error" role="alert">
      <span>{message}</span>
      {onDismiss ? (
        <button type="button" className="link-btn" onClick={onDismiss}>
          Dismiss
        </button>
      ) : null}
    </div>
  );
}
