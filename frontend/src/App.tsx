import { Route, Routes } from "react-router-dom";
import NavBar from "./components/NavBar";
import ChatPanel from "./components/ChatPanel";
import QuizModal from "./components/QuizModal";
import QuizTeaser from "./components/QuizTeaser";
import Home from "./pages/Home";
import About from "./pages/About";
import Products from "./pages/Products";
import ProductDetail from "./pages/ProductDetail";
import Login from "./pages/Login";
import CreateAccount from "./pages/CreateAccount";

function App() {
  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/products" element={<Products />} />
        <Route path="/products/:productId" element={<ProductDetail />} />
        <Route path="/about" element={<About />} />
        <Route path="/login" element={<Login />} />
        <Route path="/create-account" element={<CreateAccount />} />
      </Routes>
      <ChatPanel />
      <QuizModal />
      <QuizTeaser />
    </>
  );
}

export default App;
