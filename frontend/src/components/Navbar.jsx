// Navbar - Top navigation bar shown on every page
// Left: site name (links to home), Right: Staff login button

import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="nav">
      <div className="nav-inner">
        <Link to="/" className="nav-brand">Study Mates</Link>
        
        <Link to="/staff/setup" className="nav-action">Staff Login</Link>
      </div>
    </nav>
  );
}

export default Navbar;
