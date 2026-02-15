// Card - Reusable card wrapper with optional title header

function Card({ title, children }) {
  return (
    <div className="card">
      {title && <h1 className="card-header">{title}</h1>}
      {children}
    </div>
  );
}

export default Card;
