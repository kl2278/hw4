import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import "./NavBar.css";

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <header className="navbar">
      <NavLink to="/" className="brand">
        Campus Customs
      </NavLink>
      <nav className="nav-links">
        <NavLink to="/" end>
          Home
        </NavLink>
        <NavLink to="/products">Products</NavLink>
        <NavLink to="/about">About Us</NavLink>
        {user ? (
          <>
            <span className="nav-greeting">Hi, {user.first_name}</span>
            <button className="nav-pill nav-pill-button" onClick={handleLogout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login" className="nav-pill">
              Log in
            </NavLink>
            <NavLink to="/create-account" className="nav-pill nav-pill-solid">
              Create account
            </NavLink>
          </>
        )}
      </nav>
    </header>
  );
}
