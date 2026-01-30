import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

export default function Navigation() {
  const location = useLocation();

  return (
    <nav className="navigation">
      <Link 
        to="/" 
        className={location.pathname === '/' ? 'active' : ''}
      >
        📄 Upload
      </Link>
      <Link 
        to="/chat" 
        className={location.pathname === '/chat' ? 'active' : ''}
      >
        💬 Chat
      </Link>
    </nav>
  );
}
