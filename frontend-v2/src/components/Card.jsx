import React from "react";

export default function Card({ children, title }) {
    return (
        <div className="card">
            {title && <h2>{title}</h2>}
            {children}
        </div>
    );
}