"""
Contacts CRUD service for database operations.
"""

import json
import logging
from typing import List, Optional
from datetime import datetime, timezone
import uuid

import aiosqlite
from organizer_core.models.contacts import Contact

logger = logging.getLogger(__name__)


class ContactsService:
    """Service for contact database operations."""

    @staticmethod
    async def create_contact(db: aiosqlite.Connection, contact: Contact) -> Contact:
        """
        Create a new contact in the database.

        Args:
            db: Database connection
            contact: Contact to create

        Returns:
            Created contact with ID and timestamps
        """
        # Generate ID if not provided
        if not contact.id:
            contact.id = str(uuid.uuid4())

        # Set timestamps
        now = datetime.now(timezone.utc)
        contact.created_at = now
        contact.updated_at = now

        # Serialize JSON fields
        tags_json = json.dumps(contact.tags) if contact.tags else None
        social_profiles_json = json.dumps(contact.social_profiles) if contact.social_profiles else None

        # Convert datetime to ISO format string
        birthday_str = contact.birthday.isoformat() if contact.birthday else None

        query = """
            INSERT INTO contacts (
                id, name, email, phone, address, company, birthday,
                notes, tags, social_profiles, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        await db.execute(
            query,
            (
                contact.id,
                contact.name,
                contact.email,
                contact.phone,
                contact.address,
                contact.company,
                birthday_str,
                contact.notes,
                tags_json,
                social_profiles_json,
                contact.created_at.isoformat(),
                contact.updated_at.isoformat()
            )
        )
        await db.commit()

        logger.info(f"Created contact: {contact.id} - {contact.name}")
        return contact

    @staticmethod
    async def get_contact(db: aiosqlite.Connection, contact_id: str) -> Optional[Contact]:
        """
        Get a single contact by ID.

        Args:
            db: Database connection
            contact_id: Contact ID

        Returns:
            Contact if found, None otherwise
        """
        query = "SELECT * FROM contacts WHERE id = ?"

        async with db.execute(query, (contact_id,)) as cursor:
            row = await cursor.fetchone()

        if not row:
            return None

        return ContactsService._row_to_contact(row)

    @staticmethod
    async def get_contacts(
        db: aiosqlite.Connection,
        company: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100
    ) -> List[Contact]:
        """
        Get contacts with optional filtering.

        Args:
            db: Database connection
            company: Filter by company
            tag: Filter by tag (searches in tags JSON array)
            search: Search in name, email, or company
            limit: Maximum number of contacts to return

        Returns:
            List of contacts
        """
        query = "SELECT * FROM contacts WHERE 1=1"
        params = []

        if company:
            query += " AND company = ?"
            params.append(company)

        if search:
            query += " AND (name LIKE ? OR email LIKE ? OR company LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern, search_pattern])

        if tag:
            # SQLite JSON filtering
            query += " AND tags LIKE ?"
            params.append(f'%"{tag}"%')

        query += " ORDER BY name ASC LIMIT ?"
        params.append(limit)

        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        contacts = [ContactsService._row_to_contact(row) for row in rows]
        logger.info(f"Retrieved {len(contacts)} contacts")
        return contacts

    @staticmethod
    async def update_contact(
        db: aiosqlite.Connection,
        contact_id: str,
        contact: Contact
    ) -> Optional[Contact]:
        """
        Update an existing contact.

        Args:
            db: Database connection
            contact_id: Contact ID to update
            contact: Updated contact data

        Returns:
            Updated contact if found, None otherwise
        """
        # Check if contact exists
        existing = await ContactsService.get_contact(db, contact_id)
        if not existing:
            return None

        # Update timestamp
        contact.updated_at = datetime.now(timezone.utc)
        contact.id = contact_id  # Ensure ID doesn't change

        # Serialize JSON fields
        tags_json = json.dumps(contact.tags) if contact.tags else None
        social_profiles_json = json.dumps(contact.social_profiles) if contact.social_profiles else None

        # Convert datetime to ISO format
        birthday_str = contact.birthday.isoformat() if contact.birthday else None

        query = """
            UPDATE contacts SET
                name = ?,
                email = ?,
                phone = ?,
                address = ?,
                company = ?,
                birthday = ?,
                notes = ?,
                tags = ?,
                social_profiles = ?,
                updated_at = ?
            WHERE id = ?
        """

        await db.execute(
            query,
            (
                contact.name,
                contact.email,
                contact.phone,
                contact.address,
                contact.company,
                birthday_str,
                contact.notes,
                tags_json,
                social_profiles_json,
                contact.updated_at.isoformat(),
                contact_id
            )
        )
        await db.commit()

        logger.info(f"Updated contact: {contact_id}")
        return contact

    @staticmethod
    async def delete_contact(db: aiosqlite.Connection, contact_id: str) -> bool:
        """
        Delete a contact.

        Args:
            db: Database connection
            contact_id: Contact ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Check if contact exists
        existing = await ContactsService.get_contact(db, contact_id)
        if not existing:
            return False

        query = "DELETE FROM contacts WHERE id = ?"
        await db.execute(query, (contact_id,))
        await db.commit()

        logger.info(f"Deleted contact: {contact_id}")
        return True

    @staticmethod
    def _row_to_contact(row: tuple) -> Contact:
        """
        Convert database row to Contact.

        Args:
            row: Database row tuple

        Returns:
            Contact instance
        """
        # Parse JSON fields
        tags = json.loads(row[8]) if row[8] else []
        social_profiles = json.loads(row[9]) if row[9] else {}

        # Parse datetime fields
        from dateutil import parser

        birthday = parser.parse(row[6]) if row[6] else None
        created_at = parser.parse(row[10]) if row[10] else datetime.now(timezone.utc)
        updated_at = parser.parse(row[11]) if row[11] else datetime.now(timezone.utc)

        return Contact(
            id=row[0],
            name=row[1],
            email=row[2],
            phone=row[3],
            address=row[4],
            company=row[5],
            birthday=birthday,
            notes=row[7],
            tags=tags,
            social_profiles=social_profiles,
            created_at=created_at,
            updated_at=updated_at
        )
