function Card({ title, subtitle, actions, children }) {
  return (
    <div className="card">
      {(title || actions) && (
        <div className="card-header">
          <div className="card-heading">
            {title && <h1 className="card-title">{title}</h1>}
            {subtitle && <div className="card-heading-subtitle">{subtitle}</div>}
          </div>
          {actions && <div className="card-actions">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

export default Card;
