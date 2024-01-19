import logging
import stripe

from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from models.user import User
from models.payment import Payment, Status
from lib.token_util import AccessTokenBearer
from lib.config import DOMAIN, STRIPE_API_KEY, STRIPE_PRICE_ID
from . import cache

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

router = APIRouter()
access_token_scheme = AccessTokenBearer()
stripe.api_key = STRIPE_API_KEY


async def cache_payment(payment: Payment):
    await cache.set(f"pay_{payment.id}", payment)


async def get_payment_cached(id: int) -> Optional[Payment]:
    payment = await cache.get(f"pay_{id}")
    if not payment:
        logger.warning(f"Payment {id} is not cached!")
        payment = Payment.get(id=id)

    return payment


@router.get("/stripe/create")
async def create(
        quantity: int,  # minutes.
        _req: Request,
        user: User = Depends(access_token_scheme),
):
    payment = Payment.create(
        user_id=user.id,
        quantity=quantity
    )
    checkout_session = None

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[{
                "price": f"{STRIPE_PRICE_ID}",
                "quantity": quantity,
            }],
            mode="payment",
            customer_email=user.name,
            success_url=f"{DOMAIN}/payment/stripe/succes?id={payment.id}",
            cancel_url=f"{DOMAIN}/payment/stripe/cancel?id={payment.id}",
            automatic_tax={"enabled": True},
        )
    except stripe.StripeError as e:
        logger.error(
            f"Failed to create checkout session due to StripeError: {e}"
        )
    except Exception as e:
        logger.error(
            f"Failed to create checkout session due to unknown: {e}"
        )
    if checkout_session:
        await cache_payment(payment)
        logger.info(
            f"[payment id: {payment.id}] "
            f"Redirecto to url: {checkout_session.url}"
        )
        return RedirectResponse(checkout_session.url)
    return RedirectResponse(
        f"{DOMAIN}/payment/stripe/failed?id={payment.id}"
    )


@router.get("/stripe/succes")
async def succes(
    id: str,
    _req: Request,
    user: User = Depends(access_token_scheme),
):
    payment = await get_payment_cached(id)
    if not payment:
        logger.error(f"Can not find the cached payment with id: {id}")
        return RedirectResponse(f"{DOMAIN}/payment/stripe/failed?id={id}")
    if (user.id != payment.user_id):
        logger.warn(
            "payee is not current user!!! "
            f"current login user is: {user.id} but payee is: {payment.user_id}"
        )
    payment.set_status(Status.SUCCESS)
    old_credit = user.credit
    user.set_credit(user.credit + payment.quantity)
    logger.info(
        f"[Cha-ching!!] "
        f"Payment({id}) success for user: {user.name}. "
        f"Updated user credit from: {old_credit} to {user.credit}."
    )
    return RedirectResponse(
        f"{DOMAIN}?event=success_pay&id={payment.id}"
    )


@router.get("/stripe/cancel")
async def cancel(
    id: str,
    _req: Request,
    user: User = Depends(access_token_scheme),
):
    payment = await get_payment_cached(id)
    pay_id = -1
    if payment:
        pay_id = payment.id
    logger.info(f"User: {user} attempt to pay and canceled.")
    return RedirectResponse(
        f"{DOMAIN}?event=success_failed&id={pay_id}"
    )


@router.get("/stripe/failed")
async def failed(
    id: str,
    _req: Request,
    user: User = Depends(access_token_scheme),
):
    payment = await get_payment_cached(id)
    pay_id = -1
    if payment:
        pay_id = payment.id
    logger.warning(f"User: {user} attempt to pay and failed.")
    return RedirectResponse(
        f"{DOMAIN}?event=success_failed&id={pay_id}"
    )
