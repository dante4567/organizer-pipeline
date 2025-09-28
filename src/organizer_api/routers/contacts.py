"""
Contacts API router.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from organizer_core.models.contacts import Contact

router = APIRouter()


@router.get("/", response_model=List[Contact])
async def get_contacts(
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None)
) -> List[Contact]:
    """Get contacts with optional search and filtering."""
    # TODO: Implement with database service
    return []


@router.post("/", response_model=Contact)
async def create_contact(contact: Contact) -> Contact:
    """Create a new contact."""
    # TODO: Implement with database service
    return contact


@router.put("/{contact_id}", response_model=Contact)
async def update_contact(contact_id: str, contact: Contact) -> Contact:
    """Update an existing contact."""
    # TODO: Implement with database service
    return contact


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str) -> dict:
    """Delete a contact."""
    # TODO: Implement with database service
    return {"message": "Contact deleted successfully"}