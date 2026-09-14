from __future__ import annotations

from fastapi import APIRouter, Response

from app.auth import service
from app.auth.deps import OptionalSessionDep, RequireSessionDep, StoreDep
from app.email.deps import EmailSenderDep
from app.models.auth import (
    AuthSuccess,
    RequestCodeRequest,
    RequestCodeResponse,
    Session,
    VerifyCodeRequest,
)

router = APIRouter(prefix="/auth")


@router.post("/code", response_model=RequestCodeResponse)
def request_code(
    body: RequestCodeRequest,
    store: StoreDep,
    email_sender: EmailSenderDep,
) -> RequestCodeResponse:
    return service.request_code(store, email_sender, body.email)


@router.post("/verify", response_model=AuthSuccess)
def verify_code(body: VerifyCodeRequest, store: StoreDep) -> AuthSuccess:
    return service.verify_code(store, body.email, body.code)


@router.get("/session", response_model=Session | None)
def current_session(session: OptionalSessionDep) -> Session | None:
    return session


@router.post("/sign-out", status_code=204, response_class=Response)
def sign_out(store: StoreDep, auth: RequireSessionDep) -> Response:
    _session, token = auth
    service.sign_out(store, token)
    return Response(status_code=204)
