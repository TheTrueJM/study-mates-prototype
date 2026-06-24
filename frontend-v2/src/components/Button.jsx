import React from "react";

export default function Button({ children, onClick, variant = "primary", disabled = false }) {
    const baseClasses = "button";
    const variantClasses = variant === "primary" ? "btn-primary" : "btn-secondary";
    
    return (
        <button 
            className={`${baseClasses} ${variantClasses}`}
            onClick={onClick}
            disabled={disabled}
        >
            {children}
        </button>
    );
}