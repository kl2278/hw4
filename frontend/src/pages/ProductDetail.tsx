import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchProduct, type ProductDetail as ProductDetailType } from "../api";
import "./ProductDetail.css";

export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>();
  const [product, setProduct] = useState<ProductDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;
    fetchProduct(productId)
      .then(setProduct)
      .catch(() => setError("Couldn't load this product."));
  }, [productId]);

  if (error) return <p className="products-error">{error}</p>;
  if (!product) return <p className="product-loading">Loading...</p>;

  return (
    <div className="product-detail">
      <Link to="/products" className="back-link">
        ← Back to products
      </Link>
      <div className="product-detail-grid">
        <div className="product-detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="product-detail-info">
          <h1>{product.name}</h1>
          <p className="product-detail-price">${product.price.toFixed(2)}</p>
          <p className="product-detail-desc">{product.description}</p>

          <h3>Colors</h3>
          <p>{product.colors.join(", ")}</p>

          <h3>Stock by size</h3>
          <ul className="size-list">
            {product.sizes.map((s) => (
              <li key={s.size} className={s.quantity === 0 ? "size-out" : ""}>
                <span>{s.size}</span>
                <span>{s.quantity === 0 ? "Out of stock" : `${s.quantity} in stock`}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
