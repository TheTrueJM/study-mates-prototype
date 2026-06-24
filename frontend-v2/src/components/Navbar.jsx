import React from "react";
import { Link } from "react-router-dom";

export default function Navbar() {
    return (
        <nav className="navbar">
            <div className="navbar-brand">Study Mates</div>
            <div className="navbar-links">
                <Link to="/">Home</Link>
                <Link to="/staff/login">Staff Login</Link>
                <Link to="/staff/setup">Create Tutorial</Link>
            </div>
        </nav>
    );
}