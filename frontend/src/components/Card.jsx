// Card - Reusable card wrapper with optional title header

function Card({ title, actions, children }) {
  return (
    <div className="card">
      {title && <h1 className="card-header">{title} {actions && <div className="card-actions">{actions}</div>}</h1>}
      {children}
    </div>
  );
}

export default Card;
