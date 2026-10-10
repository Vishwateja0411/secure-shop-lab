from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text, or_

from backend.app.database import get_db
from backend.app.models.models import Product, Review, User
from backend.app.auth.dependencies import get_current_user
from backend.app.security.sanitizer import sanitize_comment, sanitize_search_query
from backend.app.config import settings

router = APIRouter(prefix="/api/products", tags=["Products"])

class ReviewCreateRequest(BaseModel):
    rating: int = 5
    comment: str

@router.get("")
def list_products(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    products = query.all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "stock": p.stock,
            "category": p.category,
            "image_url": p.image_url
        }
        for p in products
    ]

@router.get("/search")
def search_products(
    q: str = Query(..., description="Search keyword"),
    db: Session = Depends(get_db)
):
    """
    Product search endpoint:
    Vulnerable mode: Dynamic SQL string concatenation (LAB-002 SQL Injection)
    Secure mode: Parameterized ORM filter
    """
    if not settings.SECURE_MODE:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-002 SQL Injection)
        # Raw string concatenation into SQL allows injection payloads to alter query logic
        unsafe_sql = f"SELECT id, name, description, price, stock, category, image_url FROM products WHERE name LIKE '%{q}%' OR description LIKE '%{q}%'"
        try:
            result = db.execute(text(unsafe_sql))
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "price": float(row[3]),
                    "stock": row[4],
                    "category": row[5],
                    "image_url": row[6]
                }
                for row in rows
            ]
        except Exception as e:
            # In vulnerable mode, verbose error message exposed (Security Misconfiguration)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database Query Error: {str(e)}")
    else:
        # Secure implementation: Parameterized ORM search
        pattern = f"%{q}%"
        products = db.query(Product).filter(
            or_(
                Product.name.ilike(pattern),
                Product.description.ilike(pattern)
            )
        ).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "stock": p.stock,
                "category": p.category,
                "image_url": p.image_url
            }
            for p in products
        ]

@router.get("/search-echo")
def search_echo(query: str = Query(""), secure_mode: Optional[bool] = None):
    """
    Demonstration endpoint reflecting search term into response:
    Vulnerable mode: Returns unencoded user input (LAB-004 Reflected XSS)
    Secure mode: HTML entity escapes reflection
    """
    use_secure = settings.SECURE_MODE if secure_mode is None else secure_mode
    reflected_term = sanitize_search_query(query, secure_mode=use_secure)
    return {
        "status": "success",
        "search_term": reflected_term,
        "message": f"Results for: {reflected_term}"
    }

@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    
    reviews = db.query(Review).filter(Review.product_id == product_id).order_by(Review.created_at.desc()).all()
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock,
        "category": product.category,
        "image_url": product.image_url,
        "reviews": [
            {
                "id": r.id,
                "username": r.username,
                "rating": r.rating,
                "comment": r.comment,  # In vulnerable mode, contains raw unescaped input (LAB-003)
                "created_at": r.created_at.isoformat()
            }
            for r in reviews
        ]
    }

@router.post("/{product_id}/reviews")
def add_review(
    product_id: int,
    req: ReviewCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add product review:
    Vulnerable mode: Stored XSS (LAB-003) - Stores raw comment containing HTML/script tags
    Secure mode: Sanitizes and entity-encodes input before persisting
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    comment_to_store = sanitize_comment(req.comment, secure_mode=settings.SECURE_MODE)

    review = Review(
        product_id=product.id,
        user_id=current_user.id,
        username=current_user.username,
        rating=req.rating,
        comment=comment_to_store
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return {
        "status": "success",
        "message": "Review added.",
        "review": {
            "id": review.id,
            "username": review.username,
            "rating": review.rating,
            "comment": review.comment
        }
    }
