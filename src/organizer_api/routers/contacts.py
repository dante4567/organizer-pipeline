"""
Contacts API router with full CRUD operations.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
import aiosqlite

from organizer_core.models.contacts import Contact
from ..database.connection import get_database
from ..database.contacts_service import ContactsService

router = APIRouter()


@router.get("/", response_model=List[Contact])
async def get_contacts(
    search: Optional[str] = Query(None, description="Search in name, email, or company"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    company: Optional[str] = Query(None, description="Filter by company"),
    db: aiosqlite.Connection = Depends(get_database)
) -> List[Contact]:
    """Get contacts with optional search and filtering."""
    contacts = await ContactsService.get_contacts(
        db,
        company=company,
        tag=tag,
        search=search
    )
    return contacts


@router.get("/{contact_id}", response_model=Contact)
async def get_contact(
    contact_id: str,
    db: aiosqlite.Connection = Depends(get_database)
) -> Contact:
    """Get a single contact by ID."""
    contact = await ContactsService.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    return contact


@router.post("/", response_model=Contact, status_code=201)
async def create_contact(
    contact: Contact,
    db: aiosqlite.Connection = Depends(get_database)
) -> Contact:
    """Create a new contact."""
    created_contact = await ContactsService.create_contact(db, contact)
    return created_contact


@router.put("/{contact_id}", response_model=Contact)
async def update_contact(
    contact_id: str,
    contact: Contact,
    db: aiosqlite.Connection = Depends(get_database)
) -> Contact:
    """Update an existing contact."""
    updated_contact = await ContactsService.update_contact(db, contact_id, contact)
    if not updated_contact:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    return updated_contact


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: str,
    db: aiosqlite.Connection = Depends(get_database)
) -> None:
    """Delete a contact."""
    deleted = await ContactsService.delete_contact(db, contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
