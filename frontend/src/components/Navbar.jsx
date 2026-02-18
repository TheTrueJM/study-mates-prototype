// Navbar - Top navigation bar shown on every page
// Left: site name (links to home), Right: Staff login button

import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="nav">
      <div className="nav-inner">
        <Link to="/" className="nav-brand">Study Mates</Link>

        {/* TODO: Remove debug links before production */}
        <div className="nav-debug">
          <span className="nav-debug-label">Student:</span>
          <Link to="/join">Join</Link>
          <Link to="/attributes">Attributes</Link>
          <Link to="/tutorial">Tutorial</Link>
          <span className="nav-debug-divider">|</span>
          <span className="nav-debug-label">Staff:</span>
          <Link to="/staff/login">Login</Link>
          <Link to="/staff/">Setup</Link>
        </div>

        <Link to="/staff/login" className="nav-action">Staff Login</Link>
      </div>
    </nav>
  );
}

export default Navbar;
