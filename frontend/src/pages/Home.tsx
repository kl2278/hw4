import { Link } from "react-router-dom";
import { useQuiz } from "../quizContext";
import "./Home.css";

export default function Home() {
  const { openQuiz } = useQuiz();

  return (
    <div className="home">
      <section className="hero">
        <h1>Campus Customs</h1>
        <p className="hero-sub">
          Officially licensed Yale gear for students, alumni, and anyone who bleeds Yale Blue.
        </p>
        <div className="hero-actions">
          <Link to="/products" className="hero-cta">
            Shop the collection
          </Link>
          <button className="hero-quiz-cta" onClick={openQuiz}>
            Find Your Yale Fit ✨
          </button>
        </div>
      </section>

      <section className="feature-grid">
        <div className="feature-card">
          <h3>Residential Colleges</h3>
          <p>
            Rep your college with crewnecks, hoodies, and tees designed around each of Yale's
            residential communities.
          </p>
        </div>
        <div className="feature-card">
          <h3>Sports Teams</h3>
          <p>
            Gear built for game day — from football and hockey to sailing, squash, and everything
            in between.
          </p>
        </div>
        <div className="feature-card">
          <h3>Graduate & Professional Schools</h3>
          <p>
            Apparel for Yale's schools of law, medicine, business, art, music, and more, made for
            students and grads alike.
          </p>
        </div>
      </section>

      <section className="visit-us">
        <h2>Visit us in New Haven</h2>
        <p>
          Stop by our storefront at 57 Broadway, New Haven, CT to browse the full collection in
          person, or browse everything online.
        </p>
      </section>
    </div>
  );
}
