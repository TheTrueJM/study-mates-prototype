// Navbar - Top navigation bar shown on every page
// Left: site name (links to home), Right: Staff login button

import { useState } from 'react';
import { Link, useLocation } from "react-router-dom";
import Button from './Button';
import Modal from './Modal';
import { useAuth } from "../hooks/useAuth";
import QRCode from '../static/Feedback-Form-QR.svg';

function Navbar() {
  const { staffAuth, _ } = useAuth();
  const location = useLocation();

  const [showAboutModal, setShowAboutModal] = useState(false);


  const showStaffLogin = location.pathname === "/";
  const showBackToStudent = location.pathname === "/staff/login";

  const backToStaff = location.pathname.startsWith("/staff/");
  const onTutorial = location.pathname.startsWith("/staff/tutorial/") || location.pathname.startsWith("/tutorial/");

  return (
    <nav className="nav">
      <div className="nav-inner">
        {onTutorial ? (
          <span className="nav-brand">Study Mates</span> // Not clickable
          ) : (
          <Link to={backToStaff ? "/staff/" : "/"} className="nav-brand">
          Study Mates
          </Link>
        )}
          
        <div className="nav-actions">
          <a className="nav-action" onClick={() => setShowAboutModal(true)}>About Us</a>

          {showStaffLogin && (
            <Link to="/staff/login" className="nav-action">
              Staff Login
            </Link>
          )}
          {showBackToStudent && (
            <Link to="/" className="nav-action">
              Back to Student
            </Link>
          )}
        </div>
      </div>

      {showAboutModal && (
        <Modal title="Study Mates - About Us" onClose={() => setShowAboutModal(false)}>
          <div className="mb-sm">
            Lorem, ipsum dolor sit amet consectetur adipisicing elit. Reprehenderit, dignissimos repellat aspernatur, harum maxime rem similique nesciunt voluptate fuga numquam dolorum dolores, quos error excepturi necessitatibus veritatis laboriosam dicta ipsam.
            <br/><br/>
            Lorem, ipsum dolor sit amet consectetur adipisicing elit. Reprehenderit, dignissimos repellat aspernatur, harum maxime rem similique nesciunt voluptate fuga numquam dolorum dolores, quos error excepturi necessitatibus veritatis laboriosam dicta ipsam.
          </div>
          <div className="divider flex gap-md justify-center">
            <div className="qr-code-container">
              <img src={QRCode} alt="Tutorial QR Code" className="qr-image" />
            </div>
            <a href="https://forms.office.com/r/4x1A33ZKUX" target="_blank" rel="noopener noreferrer" className="self-center">
              <Button> Share Feedback </Button>
            </a>
          </div>
        </Modal>
      )}
    </nav>
  );
}

export default Navbar;
