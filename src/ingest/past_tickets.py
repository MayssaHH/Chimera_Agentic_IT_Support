"""Historical tickets ingestion for anonymized data with outcome tracking."""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

from .pipeline import DocumentChunker, VectorStore

# Configure logging
logger = logging.getLogger(__name__)

# Ticket outcome categories
TICKET_OUTCOMES = {
    "allowed": ["approved", "granted", "permitted", "authorized", "cleared"],
    "denied": ["rejected", "declined", "refused", "blocked", "prohibited"],
    "requires_approval": ["pending", "awaiting", "needs approval", "under review", "escalated"]
}

# Common approver roles
APPROVER_ROLES = [
    "manager", "supervisor", "admin", "administrator", "lead", "director",
    "head", "chief", "vp", "vice president", "cto", "cio", "it manager",
    "security officer", "compliance officer", "hr manager", "department head"
]


class TicketData:
    """Represents a single ticket with all its metadata."""
    
    def __init__(
        self,
        ticket_id: str,
        description: str,
        outcome: str,
        resolution: str,
        approver_role: Optional[str] = None,
        created_date: Optional[str] = None,
        resolved_date: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        self.ticket_id = ticket_id
        self.description = description
        self.outcome = outcome
        self.resolution = resolution
        self.approver_role = approver_role
        self.created_date = created_date
        self.resolved_date = resolved_date
        self.category = category
        self.priority = priority
        self.tags = tags or []
    
    def to_document(self) -> Document:
        """Convert ticket to LangChain Document."""
        # Combine description and resolution for content
        content = f"Ticket: {self.description}\n\nResolution: {self.resolution}"
        
        # Create metadata with source="tickets" for routing
        metadata = {
            "source": "tickets",
            "ticket_id": self.ticket_id,
            "outcome": self.outcome,
            "approver_role": self.approver_role,
            "created_date": self.created_date,
            "resolved_date": self.resolved_date,
            "category": self.category,
            "priority": self.priority,
            "tags": self.tags,
            "content_type": "ticket",
            "has_resolution": bool(self.resolution.strip()),
            "has_approver": bool(self.approver_role)
        }
        
        return Document(page_content=content, metadata=metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ticket to dictionary."""
        return {
            "ticket_id": self.ticket_id,
            "description": self.description,
            "outcome": self.outcome,
            "resolution": self.resolution,
            "approver_role": self.approver_role,
            "created_date": self.created_date,
            "resolved_date": self.resolved_date,
            "category": self.category,
            "priority": self.priority,
            "tags": self.tags
        }


class TicketProcessor:
    """Processes and analyzes ticket data for ingestion."""
    
    def detect_outcome(self, text: str) -> str:
        """Detect the outcome from text content."""
        text_lower = text.lower()
        
        for outcome, keywords in TICKET_OUTCOMES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return outcome
        
        # Default to requires_approval if no clear outcome detected
        return "requires_approval"
    
    def detect_approver_role(self, text: str) -> Optional[str]:
        """Detect approver role from text content."""
        text_lower = text.lower()
        
        for role in APPROVER_ROLES:
            if role in text_lower:
                return role.title()
        
        return None
    
    def extract_dates(self, text: str) -> Dict[str, Optional[str]]:
        """Extract dates from text content."""
        # Common date patterns
        date_patterns = [
            r"(\d{4}-\d{2}-\d{2})",  # YYYY-MM-DD
            r"(\d{2}/\d{2}/\d{4})",  # MM/DD/YYYY
            r"(\d{2}-\d{2}-\d{4})",  # MM-DD-YYYY
            r"(\w+ \d{1,2},? \d{4})",  # Month DD, YYYY
        ]
        
        dates = {}
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if not dates.get("created_date"):
                    dates["created_date"] = matches[0]
                elif not dates.get("resolved_date"):
                    dates["resolved_date"] = matches[1] if len(matches) > 1 else matches[0]
        
        return dates
    
    def extract_category(self, text: str) -> Optional[str]:
        """Extract ticket category from text."""
        categories = [
            "access", "software", "hardware", "network", "security", "email",
            "printer", "phone", "mobile", "vpn", "database", "server",
            "backup", "maintenance", "training", "compliance", "policy"
        ]
        
        text_lower = text.lower()
        for category in categories:
            if category in text_lower:
                return category.title()
        
        return None
    
    def extract_priority(self, text: str) -> Optional[str]:
        """Extract priority level from text."""
        priority_patterns = [
            (r"\b(high|urgent|critical|emergency)\b", "High"),
            (r"\b(medium|normal|standard)\b", "Medium"),
            (r"\b(low|minor|non-urgent)\b", "Low")
        ]
        
        text_lower = text.lower()
        for pattern, priority in priority_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return priority
        
        return None
    
    def extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text."""
        tags = []
        
        # Common IT support tags
        common_tags = [
            "password reset", "account lockout", "software installation",
            "hardware replacement", "network access", "vpn setup",
            "email configuration", "printer setup", "mobile device",
            "security incident", "compliance issue", "training request"
        ]
        
        text_lower = text.lower()
        for tag in common_tags:
            if tag in text_lower:
                tags.append(tag)
        
        return tags


class TicketIngestionPipeline:
    """Specialized pipeline for ingesting historical ticket data."""
    
    def __init__(
        self,
        storage_path: str = "./storage/vectorstore",
        store_type: str = "chromadb",
        max_tokens: int = 800,
        overlap_tokens: int = 120
    ):
        self.processor = TicketProcessor()
        self.chunker = DocumentChunker(max_tokens, overlap_tokens)
        self.vector_store = VectorStore(storage_path, store_type)
    
    def process_ticket_file(self, file_path: Path) -> List[TicketData]:
        """Process a single ticket file (JSON, CSV, or TXT)."""
        if file_path.suffix.lower() == ".json":
            return self._process_json_tickets(file_path)
        elif file_path.suffix.lower() == ".csv":
            return self._process_csv_tickets(file_path)
        elif file_path.suffix.lower() == ".txt":
            return self._process_text_tickets(file_path)
        else:
            logger.warning(f"Unsupported ticket file format: {file_path.suffix}")
            return []
    
    def _process_json_tickets(self, file_path: Path) -> List[TicketData]:
        """Process JSON ticket file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            tickets = []
            if isinstance(data, list):
                for item in data:
                    ticket = self._create_ticket_from_dict(item)
                    if ticket:
                        tickets.append(ticket)
            elif isinstance(data, dict):
                ticket = self._create_ticket_from_dict(data)
                if ticket:
                    tickets.append(ticket)
            
            logger.info(f"Processed {len(tickets)} tickets from JSON file")
            return tickets
            
        except Exception as e:
            logger.error(f"Error processing JSON file {file_path}: {e}")
            return []
    
    def _process_csv_tickets(self, file_path: Path) -> List[TicketData]:
        """Process CSV ticket file."""
        try:
            import csv
            
            tickets = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ticket = self._create_ticket_from_dict(row)
                    if ticket:
                        tickets.append(ticket)
            
            logger.info(f"Processed {len(tickets)} tickets from CSV file")
            return tickets
            
        except Exception as e:
            logger.error(f"Error processing CSV file {file_path}: {e}")
            return []
    
    def _process_text_tickets(self, file_path: Path) -> List[TicketData]:
        """Process text file with ticket information."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content into ticket sections
            ticket_sections = self._split_text_into_tickets(content)
            
            tickets = []
            for section in ticket_sections:
                ticket = self._create_ticket_from_text(section)
                if ticket:
                    tickets.append(ticket)
            
            logger.info(f"Processed {len(tickets)} tickets from text file")
            return tickets
            
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {e}")
            return []
    
    def _split_text_into_tickets(self, content: str) -> List[str]:
        """Split text content into individual ticket sections."""
        # Look for common ticket separators
        separators = [
            r"\n\s*Ticket\s*ID:",
            r"\n\s*Case\s*#:",
            r"\n\s*Request\s*#:",
            r"\n\s*Incident\s*#:"
        ]
        
        # Find all separator positions
        positions = []
        for pattern in separators:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                positions.append(match.start())
        
        positions.sort()
        
        # Split content at separator positions
        sections = []
        start = 0
        for pos in positions:
            if pos > start:
                section = content[start:pos].strip()
                if section:
                    sections.append(section)
            start = pos
        
        # Add the last section
        if start < len(content):
            section = content[start:].strip()
            if section:
                sections.append(section)
        
        return sections if sections else [content]
    
    def _create_ticket_from_dict(self, data: Dict[str, Any]) -> Optional[TicketData]:
        """Create TicketData from dictionary."""
        try:
            # Extract required fields
            ticket_id = str(data.get("ticket_id", data.get("id", data.get("case_number", ""))))
            description = str(data.get("description", data.get("summary", data.get("issue", ""))))
            outcome = str(data.get("outcome", data.get("status", data.get("resolution_status", ""))))
            resolution = str(data.get("resolution", data.get("notes", data.get("solution", ""))))
            
            # Validate required fields
            if not all([ticket_id, description, outcome, resolution]):
                logger.warning(f"Incomplete ticket data: {data}")
                return None
            
            # Extract optional fields
            approver_role = data.get("approver_role", data.get("approver", data.get("assigned_to")))
            created_date = data.get("created_date", data.get("opened_date", data.get("date")))
            resolved_date = data.get("resolved_date", data.get("closed_date", data.get("completion_date")))
            category = data.get("category", data.get("type", data.get("classification")))
            priority = data.get("priority", data.get("severity", data.get("level")))
            tags = data.get("tags", data.get("labels", []))
            
            # Convert tags to list if it's a string
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            elif not isinstance(tags, list):
                tags = []
            
            return TicketData(
                ticket_id=ticket_id,
                description=description,
                outcome=outcome,
                resolution=resolution,
                approver_role=approver_role,
                created_date=created_date,
                resolved_date=resolved_date,
                category=category,
                priority=priority,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Error creating ticket from dict: {e}")
            return None
    
    def _create_ticket_from_text(self, text: str) -> Optional[TicketData]:
        """Create TicketData from text content."""
        try:
            # Extract ticket ID
            ticket_id_match = re.search(r"(?:Ticket\s*ID|Case\s*#|Request\s*#|Incident\s*#):\s*([^\n]+)", text, re.IGNORECASE)
            ticket_id = ticket_id_match.group(1).strip() if ticket_id_match else f"TEXT_{hash(text) % 10000}"
            
            # Extract description (first paragraph or line)
            lines = text.split('\n')
            description = ""
            for line in lines:
                line = line.strip()
                if line and not line.startswith(('Ticket', 'Case', 'Request', 'Incident', 'Outcome', 'Resolution')):
                    description = line
                    break
            
            if not description:
                description = text[:200] + "..." if len(text) > 200 else text
            
            # Detect outcome
            outcome = self.processor.detect_outcome(text)
            
            # Extract resolution (look for resolution-related text)
            resolution_match = re.search(r"(?:Resolution|Solution|Notes|Comments?):\s*(.+?)(?:\n|$)", text, re.IGNORECASE | re.DOTALL)
            resolution = resolution_match.group(1).strip() if resolution_match else text[-300:] if len(text) > 300 else text
            
            # Extract other metadata
            approver_role = self.processor.detect_approver_role(text)
            
            return TicketData(
                ticket_id=ticket_id,
                description=description,
                outcome=outcome,
                resolution=resolution,
                approver_role=approver_role
            )
            
        except Exception as e:
            logger.error(f"Error creating ticket from text: {e}")
            return None
    
    def process_directory(self, input_dir: str) -> None:
        """Process all ticket files in a directory."""
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")
        
        if not input_path.is_dir():
            raise ValueError(f"Input path is not a directory: {input_dir}")
        
        # Find all ticket files
        ticket_files = []
        for ext in [".json", ".csv", ".txt"]:
            ticket_files.extend(input_path.glob(f"**/*{ext}"))
        
        if not ticket_files:
            logger.warning(f"No ticket files found in {input_dir}")
            return
        
        logger.info(f"Found {len(ticket_files)} ticket files to process")
        
        # Process all tickets
        all_tickets = []
        for file_path in ticket_files:
            logger.info(f"Processing ticket file: {file_path}")
            tickets = self.process_ticket_file(file_path)
            all_tickets.extend(tickets)
        
        if not all_tickets:
            logger.warning("No tickets were processed")
            return
        
        # Convert tickets to documents
        documents = []
        for ticket in all_tickets:
            doc = ticket.to_document()
            documents.append(doc)
        
        # Chunk documents if needed
        all_chunks = []
        for doc in documents:
            chunks = self.chunker.chunk_document(doc)
            all_chunks.extend(chunks)
        
        # Add to vector store
        if all_chunks:
            self.vector_store.add_documents(all_chunks)
            self.vector_store.save()
            logger.info(f"Successfully processed {len(all_chunks)} ticket chunks from {len(all_tickets)} tickets")
        else:
            logger.warning("No chunks were created from the tickets")


def main():
    """CLI entry point for ticket ingestion."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Historical tickets ingestion pipeline")
    parser.add_argument(
        "input_dir",
        help="Directory containing ticket files to ingest"
    )
    parser.add_argument(
        "--storage-path",
        default="./storage/vectorstore",
        help="Path for vector store storage (default: ./storage/vectorstore)"
    )
    parser.add_argument(
        "--store-type",
        choices=["chromadb", "faiss"],
        default="chromadb",
        help="Vector store type (default: chromadb)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=800,
        help="Maximum tokens per chunk (default: 800)"
    )
    parser.add_argument(
        "--overlap-tokens",
        type=int,
        default=120,
        help="Overlap tokens between chunks (default: 120)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize pipeline
        pipeline = TicketIngestionPipeline(
            storage_path=args.storage_path,
            store_type=args.store_type,
            max_tokens=args.max_tokens,
            overlap_tokens=args.overlap_tokens
        )
        
        # Process tickets
        pipeline.process_directory(args.input_dir)
        
        logger.info("Ticket ingestion pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
