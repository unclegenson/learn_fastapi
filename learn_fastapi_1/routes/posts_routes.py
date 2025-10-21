from fastapi import HTTPException,APIRouter,Depends
from sqlmodel import select
from models import Post,PostIn, PostUpdate, User,PostOutWithAuthor,UserOut
from db import sessionDep
from jwt_auth import JWTBearer

router = APIRouter()


@router.post("/posts/", response_model=PostOutWithAuthor, dependencies=[Depends(JWTBearer())])
async def create_post(post: PostIn, session: sessionDep):
    user = session.get(User, post.user_id)
    if not user:
        raise HTTPException(status_code=400, detail='User with this id does not exist!')

    similar_post = session.exec(select(Post).where(Post.title == post.title)).first()
    if similar_post:
        raise HTTPException(status_code=400, detail='A post with this title already exists!')
        
    db_post = Post(
        title=post.title,
        description=post.description,
        user_id=post.user_id  
    )
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    
    # Now db_post includes the author relationship
    return PostOutWithAuthor.model_validate(db_post)



@router.get("/posts/", response_model=list[PostOutWithAuthor])
async def get_posts(session: sessionDep):
    posts = session.exec(select(Post)).all()
    
    result = []
    for post in posts:
        user = session.get(User, post.user_id)
        # Check if user exists before creating UserOut
        if user:
            result.append(PostOutWithAuthor(
                id=post.id,
                title=post.title,
                description=post.description,
                user_id=post.user_id,
                author=UserOut(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    phone_number=user.phone_number
                )
            ))
        else:            
            #Include post without author details
            result.append(PostOutWithAuthor(
                id=post.id,
                title=post.title,
                description=post.description,
                user_id=post.user_id,
                author=None  # Would require making author optional in the model
            ))
    
    return result

@router.get("/posts/{post_id}", response_model=PostOutWithAuthor)
async def get_post(post_id: int, session: sessionDep):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    user = session.get(User, post.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Author of this post not found")
    
    return PostOutWithAuthor(
        id=post.id,
        title=post.title,
        description=post.description,
        user_id=post.user_id,
        author=UserOut(
            id=user.id,
            username=user.username,
            email=user.email,
            phone_number=user.phone_number
        )
    )


@router.delete("/posts/{post_id}",dependencies=[Depends(JWTBearer())])
async def delete_post(post_id: int, session: sessionDep):
    post = session.get(Post,post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    session.delete(post)
    session.commit()
    return {'message':'Post deleted successfully'}


@router.patch("/posts/{post_id}",dependencies=[Depends(JWTBearer())])
async def update_post(post_id: int, post: PostUpdate, session: sessionDep):
    want_to_update_post = session.get(Post,post_id)
    if not want_to_update_post:
        raise HTTPException(status_code=404, detail="post not found")
    
    # If user_id is being updated, check if the new user exists
    if post.user_id is not None:
        user = session.get(User, post.user_id)
        if not user:
            raise HTTPException(status_code=400, detail="User with this id does not exist!")
    
    post_data = post.model_dump(exclude_unset=True)
    want_to_update_post.sqlmodel_update(post_data)
    session.add(want_to_update_post)
    session.commit()
    session.refresh(want_to_update_post)
    
    # Get the current author (could be updated)
    current_user = session.get(User, want_to_update_post.user_id)
    if not current_user:
        raise HTTPException(status_code=404, detail="Author of this post not found")
    
    return PostOutWithAuthor(
        id=want_to_update_post.id,
        title=want_to_update_post.title,
        description=want_to_update_post.description,
        user_id=want_to_update_post.user_id,
        author=UserOut(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            phone_number=current_user.phone_number
        )
    )