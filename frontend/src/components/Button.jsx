// Variants: "primary" (blue), "secondary" (orange), "outline" (border only), "danger" (red outline), "link" (text only)
// Sizes: "md" (default), "sm"
function Button({
  children, onClick, variant = "primary", size = "md", fullWidth = false, disabled = false,
  type = "button", className = "", ...props
}) {
  const classes = [
    "btn",
    `btn-${variant}`,
    size === "sm" && "btn-sm",
    fullWidth && "btn-full",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button type={type} className={classes} onClick={onClick} disabled={disabled} {...props}>
      {children}
    </button>
  );
}

export default Button;
