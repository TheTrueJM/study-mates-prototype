// Button - Reusable button component
// Variants: 'primary' (blue), 'secondary' (orange), 'outline' (border only)

function Button({ variant = 'primary', fullWidth = false, onClick, children }) {
  const className = [
    'btn',
    `btn-${variant}`,
    fullWidth && 'btn-full'
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button className={className} onClick={onClick}>
      {children}
    </button>
  );
}

export default Button;
