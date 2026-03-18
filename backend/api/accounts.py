"""
API Endpoints for MT5 Account Management.
"""
from typing import List
from fastapi import APIRouter, HTTPException

from backend.app.core.account_manager import account_manager, AccountCreate, AccountResponse

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("/", response_model=List[AccountResponse])
async def list_accounts():
    """List all saved MT5 accounts (without passwords)."""
    return account_manager.get_accounts()


@router.post("/", response_model=AccountResponse)
async def create_account(acc: AccountCreate):
    """Save a new MT5 account with encrypted password."""
    try:
        acc_id = account_manager.add_account(acc)
        return AccountResponse(
            id=acc_id, 
            name=acc.name, 
            server=acc.server, 
            login=acc.login, 
            is_live=acc.is_live
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{account_id}")
async def delete_account(account_id: int):
    """Delete an MT5 account."""
    success = account_manager.delete_account(account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found.")
    return {"status": "success", "message": "Account deleted."}
    
