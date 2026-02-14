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
          <Link to="/student/join">Join</Link>
          <Link to="/student/attributes">Attributes</Link>
          <Link to="/student/waiting">Waiting</Link>
          <Link to="/student/group">Group</Link>
          <span className="nav-debug-divider">|</span>
          <span className="nav-debug-label">Staff:</span>
          <Link to="/staff/setup">Setup</Link>
          <Link to="/staff/lobby">Lobby</Link>
          <Link to="/staff/groups">Groups</Link>
          <Link to="/staff/discussion">Discussion</Link>
        </div>

        <Link to="/staff/setup" className="nav-action">Staff Login</Link>
      </div>
    </nav>
  );
}

export default Navbar;
