from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.products import Product as ProductModel
from app.models.reviews import Review as ReviewModel
from app.models.users import User as UserModel
from app.schemas import Review as ReviewSchema, ReviewCreate
from app.db_depends import get_db
from app.auth import get_current_buyer, get_current_user

from sqlalchemy.ext.asyncio import AsyncSession
from app.db_depends import get_async_db


router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
)


async def update_product_rating(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )
    avg_rating = result.scalar() or 0.0
    product = await db.get(ProductModel, product_id)
    product.rating = avg_rating
    await db.commit()


@router.get("/", response_model=list[ReviewSchema])
async def get_all_reviews(db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))
    reviews =  result.all()
    return reviews


@router.get("products/{product_id}/reviews", response_model=list[ReviewSchema])
async def get_reviews_by_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    product_result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id,
                                                                ProductModel.is_active == True))
    product = product_result.first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Review not found or inactive")
    reviews_result = await db.scalars(select(ReviewModel).where(ReviewModel.product_id == product_id,
                                                                ReviewModel.is_active == True))
    reviews = reviews_result.all()
    return reviews


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_buyer) 
):
    product_result = await db.scalars(
        select(ProductModel).where(ProductModel.id == review.product_id,
                                    ProductModel.is_active == True))
    product = product_result.first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_BAD_REQUEST,
                            detail="Product not found or inactive")

    db_review = ReviewModel(**review.model_dump(), user_id=current_user.id)
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)

    await update_product_rating(db, product_id=review.product_id)
    
    return db_review


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user)
):
    review_result = await db.scalars(select(ReviewModel).where(ReviewModel.id == review_id,
                                                               ReviewModel.is_active == True))
    review = review_result.first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Review not found or inactive")
    
    if review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You can only delete your own reviews or do it as an administrator")
    
    review.is_active = False
    await db.commit()
    await db.refresh(review)

    await update_product_rating(db, product_id=review.product_id)

    return {"message": "Review deleted!"}