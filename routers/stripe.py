import logging
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
import stripe

from models.user import User
from lib.token_util import AccessTokenBearer
from lib.config import DOMAIN, STRIPE_API_KEY, STRIPE_PRICE_ID


logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

router = APIRouter()
access_token_scheme = AccessTokenBearer()
stripe.api_key = STRIPE_API_KEY
from . import cache



@router.post("/stripe/create")
async def create(
        resourceId: int,
        req: Request,
        user: User = Depends(access_token_scheme),
):  
    payment_id = uuid.uuid4().hex
    checkout_session = None
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                "price": f"{STRIPE_PRICE_ID}",
                "quantity": resourceId, # TODO get quality from resource id.
            },],
            mode="payment",
            customer_email=user.name,
            success_url=f"{DOMAIN}/payment/stripe/succes?id={payment_id}",
            cancel_url=f"{DOMAIN}/payment/stripe/cancel?id={payment_id}",
            automatic_tax={"enabled": True},
        )
    except Exception as e:
        # TODO handle excetpion here
        logger.error(f"Stripe payment session create failed with error: {e}")
    
    if checkout_session:
        await cache.set(payment_id, user.name)
        logger.info(f"[payment id: {payment_id}] Redirecto to url: {checkout_session.url}")
        return RedirectResponse(checkout_session.url)
    return "payment failed"


@router.get("/stripe/succes")
async def succes(
    id: str,
    req: Request,
    user: User = Depends(access_token_scheme), 
):
    payee = await cache.get(id)
    if (user.name != payee):
        logger.warn("payee is not current user")
        # TODO
        # 1) mark the resource as 'paid' in DB.
        # 2) return to a page with download url
    logger.info(f"[payment id: {id}] Cha-ching! Payment success invoked for user: {user.name}")
    return f"payment success for user: {user.name} and payment id"



@router.get("/stripe/cancel")
async def cancel(
    id: str,
    req: Request,
    user: User = Depends(access_token_scheme), 
):
    return f"payment canceled for user: {user.name}"

