// Variants: 'primary' (blue), 'secondary' (orange), 'outline' (border only)
function Button({ children, onClick, variant = 'primary', fullWidth = false, disabled = false }) {
  const className = [
    'btn',
    `btn-${variant}`,
    fullWidth && 'btn-full'
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button className={className} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}

export default Button;
