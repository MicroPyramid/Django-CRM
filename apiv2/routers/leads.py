from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form, status, Path, Request
from pydantic import BaseModel
import os
from datetime import datetime
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q  # Added missing Q import

from apiv2.utils import verify_token
from common.models import Attachments, Comment, Org, Profile, Tag, User, AuditLog
from leads.models import Lead, Company
from teams.models import Teams
from contacts.models import Contact
from common.utils import COUNTRIES, INDCHOICES, LEAD_SOURCE, LEAD_STATUS
from leads.tasks import create_lead_from_file, send_email_to_assigned_user

# Pydantic models for request/response validation
class TagResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes =True

class CommentCreate(BaseModel):
    comment: str

class CommentUpdate(BaseModel):
    comment: str

class CommentResponse(BaseModel):
    id: int
    comment: str
    commented_by: Optional[int] = None
    commented_on: datetime
    
    class Config:
        from_attributes =True

class AttachmentResponse(BaseModel):
    id: int
    file_name: str
    attachment: str
    created_on: datetime
    
    class Config:
        from_attributes =True

class LeadCreate(BaseModel):
    title: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    status: str = "open"
    source: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    address_line: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    skype_ID: Optional[str] = None
    probability: Optional[int] = None
    opportunity_amount: Optional[int] = None
    assigned_to: Optional[List[int]] = None
    tags: Optional[List[int]] = None
    contacts: Optional[List[int]] = None
    teams: Optional[List[int]] = None

class LeadUpdate(LeadCreate):
    pass

class LeadResponse(BaseModel):
    id: int
    title: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    status: str
    created_on: datetime
    
    class Config:
        from_attributes =True

class CompanyCreate(BaseModel):
    name: str
    website: Optional[str] = None
    address: Optional[str] = None

class CompanyUpdate(CompanyCreate):
    pass

class CompanyResponse(BaseModel):
    id: int
    name: str
    website: Optional[str] = None
    created_on: datetime
    
    class Config:
        from_attributes =True

class SuccessResponse(BaseModel):
    error: bool = False
    message: str

router = APIRouter(tags=["Leads"])

def force_strings(choices):
    return [(key, str(value)) for key, value in choices]


@router.get("/meta/", response_model=Dict[str, Any])
def get_leads(
    request: Request,
    token_payload: dict = Depends(verify_token)
):
    
    return {
        "status": force_strings(LEAD_STATUS),
        "source": force_strings(LEAD_SOURCE),
        "countries": force_strings(COUNTRIES),
        "industries": force_strings(INDCHOICES),
    }

@router.get("/", response_model=Dict[str, Any])
def get_leads(
    request: Request,
    name: Optional[str] = None,
    title: Optional[str] = None,
    source: Optional[str] = None,
    assigned_to: Optional[List[int]] = Query(None),
    lead_status: Optional[str] = Query(None),
    tags: Optional[List[int]] = Query(None),
    city: Optional[str] = None,
    email: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    token_payload: dict = Depends(verify_token)
):
    # ... (initial authentication and profile retrieval)

    # Main queryset
    queryset = Lead.objects.filter(org=request.state.org).exclude(status="converted").order_by("-id")
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user, org=request.state.org)
    # Check permissions
    if profile.role != "ADMIN" and not user.is_superuser:
        queryset = queryset.filter(Q(assigned_to=profile) | Q(created_by=user))
    
    # Apply filters using query parameters
    if name:
        queryset = queryset.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
    if title:
        queryset = queryset.filter(title__icontains=title)
    if source:
        queryset = queryset.filter(source=source)
    if assigned_to:
        queryset = queryset.filter(assigned_to__in=assigned_to)
    if lead_status:
        queryset = queryset.filter(status=lead_status)
    if tags:
        queryset = queryset.filter(tags__in=tags)
    if city:
        queryset = queryset.filter(city__icontains=city)
    if email:
        queryset = queryset.filter(email__icontains=email)
    
    # Pagination: open and closed leads
    queryset_open = queryset.exclude(status="closed")
    open_leads_count = queryset_open.count()
    open_leads = list(queryset_open[offset:offset+limit].values())
    
    queryset_closed = queryset.filter(status="closed")
    closed_leads_count = queryset_closed.count()
    closed_leads = list(queryset_closed[offset:offset+limit].values())
    
    # Retrieve additional context
    contacts = Contact.objects.filter(org=profile.org).values('id', 'first_name')
    companies = Company.objects.filter(org=profile.org)
    # Rename the variable to avoid conflict with the query parameter "tags"
    available_tags = Tag.objects.all()
    users = Profile.objects.filter(is_active=True, org=profile.org).values('id', 'user__email')
    
    # Log the view action using the original query parameter values
    AuditLog.objects.create(
        user=user,
        content_type=ContentType.objects.get_for_model(Lead),
        object_id="list",
        action="view",
        data={
            "filters": {
                "name": name,
                "title": title,
                "source": source,
                "assigned_to": assigned_to,
                "status": lead_status,
                "tags": tags,  # use the query parameter here, not the QuerySet
                "city": city,
                "email": email,
                "limit": limit,
                "offset": offset
            }
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")
    )
    
    return {
        "per_page": limit,
        "page_number": (offset // limit) + 1,
        "open_leads": {
            "leads_count": open_leads_count,
            "open_leads": open_leads,
            "offset": offset + min(limit, len(open_leads)),
        },
        # "close_leads": {
        #     "leads_count": closed_leads_count,
        #     "close_leads": closed_leads,
        #     "offset": offset + min(limit, len(closed_leads)),
        # },
        "contacts": list(contacts),
        # "status": LEAD_STATUS,
        # "source": LEAD_SOURCE,
        # "companies": list(companies.values('id', 'name')),
        "tags": list(available_tags.values('id', 'name')),
        "users": list(users),
        # "countries": COUNTRIES,
        # "industries": INDCHOICES,
    }

@router.post("/", response_model=SuccessResponse)
def create_lead(
    request: Request,
    lead_data: LeadCreate,
    token_payload: dict = Depends(verify_token)
):
    org = request.state.org
    print("org:", org)
    org = Org.objects.get(id=org)
    """
    Create a new lead
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user, org=org)
    
    # Create lead
    lead_obj = Lead(
        title=lead_data.title,
        first_name=lead_data.first_name,
        last_name=lead_data.last_name,
        email=lead_data.email,
        phone=lead_data.phone,
        status=lead_data.status,
        source=lead_data.source,
        website=lead_data.website,
        description=lead_data.description,
        address_line=lead_data.address_line,
        street=lead_data.street,
        city=lead_data.city,
        state=lead_data.state,
        postcode=lead_data.postcode,
        country=lead_data.country,
        industry=lead_data.industry,
        skype_ID=lead_data.skype_ID,
        probability=lead_data.probability,
        opportunity_amount=lead_data.opportunity_amount,
        org=profile.org,
        created_by=user
    )
    lead_obj.save()
    
    # Handle tags
    if lead_data.tags:
        tag_objs = Tag.objects.filter(id__in=lead_data.tags)
        lead_obj.tags.add(*tag_objs)
    
    # Handle contacts
    if lead_data.contacts:
        contact_objs = Contact.objects.filter(id__in=lead_data.contacts)
        lead_obj.contacts.add(*contact_objs)
    
    # Send email notification
    if lead_data.assigned_to:
        send_email_to_assigned_user.delay(lead_data.assigned_to, lead_obj.id)
    
    # Handle teams
    if lead_data.teams:
        team_objs = Teams.objects.filter(id__in=lead_data.teams)
        lead_obj.teams.add(*team_objs)
    
    # Handle assigned_to
    if lead_data.assigned_to:
        assigned_profiles = Profile.objects.filter(id__in=lead_data.assigned_to)
        lead_obj.assigned_to.add(*assigned_profiles)
    
    # Handle converted status
    if lead_data.status == "converted":
        # Conversion logic would go here
        pass
    
    # Log the lead creation
    AuditLog.objects.create(
        user=user,
        content_type=ContentType.objects.get_for_model(Lead),
        object_id=str(lead_obj.id),
        action="create",
        data={
            "title": lead_obj.title,
            "email": lead_obj.email,
            "source": lead_obj.source,
            "status": lead_obj.status,
            "assigned_to": list(lead_obj.assigned_to.values_list('id', flat=True)) if lead_data.assigned_to else [],
            "teams": list(lead_obj.teams.values_list('id', flat=True)) if lead_data.teams else [],
            "has_attachment": False  # removed file attachment
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")
    )
    
    return {"error": False, "message": "Lead Created Successfully"}

@router.get("/{lead_id}", response_model=Dict[str, Any])
def get_lead_detail(
    request: Request,
    lead_id: int = Path(...),
    token_payload: dict = Depends(verify_token)
):
    """
    Get lead details by ID
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    try:
        lead_obj = Lead.objects.get(id=lead_id)
    except Lead.DoesNotExist:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Permission check
    if lead_obj.org != profile.org:
        raise HTTPException(status_code=403, detail="You don't have permission to view this lead")
    
    user_assigned_list = [assigned.id for assigned in lead_obj.assigned_to.all()]
    if user.id == lead_obj.created_by.id:
        user_assigned_list.append(profile.id)
    
    if profile.role != "ADMIN" and not user.is_superuser:
        if profile.id not in user_assigned_list:
            raise HTTPException(
                status_code=403, 
                detail="You do not have Permission to perform this action"
            )
    
    # Get comments and attachments
    comments = Comment.objects.filter(lead=lead_obj).order_by("-id")
    attachments = Attachments.objects.filter(lead=lead_obj).order_by("-id")
    
    # Assigned data
    assigned_data = []
    for assigned in lead_obj.assigned_to.all():
        assigned_data.append({
            "id": assigned.id,
            "name": assigned.user.email
        })
    
    # Users mention
    if user.is_superuser or profile.role == "ADMIN":
        users_mention = User.objects.filter(
            profile__is_active=True, 
            profile__org=profile.org
        ).values_list('email', flat=True)
    elif user.id != lead_obj.created_by.id:
        users_mention = [{"username": lead_obj.created_by.username}]
    else:
        users_mention = [assigned.user.email for assigned in lead_obj.assigned_to.all()]
    
    # Get users for assignment
    if profile.role == "ADMIN" or user.is_superuser:
        users = Profile.objects.filter(
            is_active=True, 
            org=profile.org
        ).order_by('user__email')
    else:
        users = Profile.objects.filter(
            role="ADMIN", 
            org=profile.org
        ).order_by('user__email')
    
    # Team users logic
    team_ids = [user.id for user in lead_obj.get_team_users()]
    all_user_ids = [user.id for user in users]
    users_excluding_team_id = set(all_user_ids) - set(team_ids)
    users_excluding_team = Profile.objects.filter(id__in=users_excluding_team_id)
    
    # Teams
    teams = Teams.objects.filter(org=profile.org)
    
    # Log the lead view
    AuditLog.objects.create(
        user=user,
        content_type=ContentType.objects.get_for_model(Lead),
        object_id=str(lead_id),
        action="view",
        data=None,  # No specific data needed for view action
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")
    )
    
    return {
        "lead_obj": {
            "id": lead_obj.id,
            "title": lead_obj.title,
            "first_name": lead_obj.first_name,
            "last_name": lead_obj.last_name,
            "email": lead_obj.email,
            "phone": lead_obj.phone,
            "status": lead_obj.status,
            "source": lead_obj.source,
            "website": lead_obj.website,
            "description": lead_obj.description,
            # Add other fields as needed
        },
        "attachments": list(attachments.values()),
        "comments": list(comments.values()),
        "users_mention": list(users_mention),
        "assigned_data": assigned_data,
        "users": list(users.values('id', 'user__email')),
        "users_excluding_team": list(users_excluding_team.values('id', 'user__email')),
        "source": LEAD_SOURCE,
        "status": LEAD_STATUS,
        "teams": list(teams.values('id', 'name')),
        "countries": COUNTRIES
    }

@router.post("/{lead_id}/comment", response_model=Dict[str, Any])
def add_lead_comment(
    request: Request,
    lead_id: int,
    comment_data: CommentCreate,
    token_payload: dict = Depends(verify_token),
    attachment: Optional[UploadFile] = File(None)
):
    """
    Add comment to a lead
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    try:
        lead_obj = Lead.objects.get(id=lead_id)
    except Lead.DoesNotExist:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead_obj.org != profile.org:
        raise HTTPException(
            status_code=403, 
            detail="User company does not match with header"
        )
    
    # Permission check
    if profile.role != "ADMIN" and not user.is_superuser:
        if not ((user.id == lead_obj.created_by.id) or 
                (profile in lead_obj.assigned_to.all())):
            raise HTTPException(
                status_code=403, 
                detail="You don't have permission to perform this action"
            )
    
    # Add comment
    if comment_data.comment:
        comment_obj = Comment(
            comment=comment_data.comment,
            lead=lead_obj,
            commented_by=profile,
            org=profile.org
        )
        comment_obj.save()
        
        # Log the comment action
        AuditLog.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=str(comment_obj.id),
            action="create",
            data={
                "lead_id": lead_id,
                "comment": comment_data.comment,
                "has_attachment": bool(attachment)
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")
        )
    
    # Add attachment
    if attachment:
        attachment_obj = Attachments(
            attachment=attachment.filename,
            lead=lead_obj,
            created_by=user,
            file_name=attachment.filename,
            org=profile.org
        )
        attachment_obj.save()
        
        # Save file
        file_content = attachment.file.read()
        file_path = f"media/leads/{lead_obj.id}/{attachment.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_content)
    
    # Get updated comments and attachments
    comments = Comment.objects.filter(lead=lead_obj).order_by("-id")
    attachments = Attachments.objects.filter(lead=lead_obj).order_by("-id")
    
    return {
        "lead_obj": {
            "id": lead_obj.id,
            "title": lead_obj.title,
            # Add other fields as needed
        },
        "attachments": list(attachments.values()),
        "comments": list(comments.values())
    }

@router.put("/{lead_id}", response_model=SuccessResponse)
def update_lead(
    request: Request,
    lead_id: int,
    lead_data: LeadUpdate,
    token_payload: dict = Depends(verify_token),
    lead_attachment: Optional[UploadFile] = File(None)
):
    """
    Update a lead
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    try:
        lead_obj = Lead.objects.get(id=lead_id)
    except Lead.DoesNotExist:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead_obj.org != profile.org:
        raise HTTPException(
            status_code=403, 
            detail="User company does not match with header"
        )
    
    # Track changes for audit log
    original_data = {
        "title": lead_obj.title,
        "first_name": lead_obj.first_name,
        "last_name": lead_obj.last_name,
        "email": lead_obj.email,
        "phone": lead_obj.phone,
        "status": lead_obj.status,
        "source": lead_obj.source,
        "website": lead_obj.website,
        "description": lead_obj.description,
        "assigned_to": list(lead_obj.assigned_to.values_list('id', flat=True)),
        "tags": list(lead_obj.tags.values_list('id', flat=True))
    }
    
    # Update lead attributes
    previous_assigned_to = list(lead_obj.assigned_to.all().values_list('id', flat=True))
    
    # Update basic fields
    lead_obj.title = lead_data.title if lead_data.title else lead_obj.title
    lead_obj.first_name = lead_data.first_name if lead_data.first_name is not None else lead_obj.first_name
    lead_obj.last_name = lead_data.last_name if lead_data.last_name is not None else lead_obj.last_name
    lead_obj.email = lead_data.email if lead_data.email else lead_obj.email
    lead_obj.phone = lead_data.phone if lead_data.phone is not None else lead_obj.phone
    lead_obj.status = lead_data.status if lead_data.status else lead_obj.status
    lead_obj.source = lead_data.source if lead_data.source is not None else lead_obj.source
    lead_obj.website = lead_data.website if lead_data.website is not None else lead_obj.website
    lead_obj.description = lead_data.description if lead_data.description is not None else lead_obj.description
    lead_obj.address_line = lead_data.address_line if lead_data.address_line is not None else lead_obj.address_line
    lead_obj.street = lead_data.street if lead_data.street is not None else lead_obj.street
    lead_obj.city = lead_data.city if lead_data.city is not None else lead_obj.city
    lead_obj.state = lead_data.state if lead_data.state is not None else lead_obj.state
    lead_obj.postcode = lead_data.postcode if lead_data.postcode is not None else lead_obj.postcode
    lead_obj.country = lead_data.country if lead_data.country is not None else lead_obj.country
    lead_obj.industry = lead_data.industry if lead_data.industry is not None else lead_obj.industry
    lead_obj.opportunity_amount = lead_data.opportunity_amount if lead_data.opportunity_amount is not None else lead_obj.opportunity_amount
    
    lead_obj.save()
    
    # Handle tags
    if lead_data.tags is not None:
        lead_obj.tags.clear()
        if lead_data.tags:
            tag_objs = Tag.objects.filter(id__in=lead_data.tags)
            lead_obj.tags.add(*tag_objs)
    
    # Handle assigned_to
    if lead_data.assigned_to is not None:
        lead_obj.assigned_to.clear()
        if lead_data.assigned_to:
            assigned_profiles = Profile.objects.filter(id__in=lead_data.assigned_to)
            lead_obj.assigned_to.add(*assigned_profiles)
            
            # Send notification emails
            new_assigned_to = list(lead_obj.assigned_to.all().values_list('id', flat=True))
            recipients = list(set(new_assigned_to) - set(previous_assigned_to))
            if recipients:
                send_email_to_assigned_user.delay(recipients, lead_obj.id)
    
    # Handle attachment
    if lead_attachment:
        attachment_obj = Attachments(
            attachment=lead_attachment.filename,
            lead=lead_obj,
            created_by=user,
            file_name=lead_attachment.filename,
            org=profile.org
        )
        attachment_obj.save()
        
        # Save file
        file_content = lead_attachment.file.read()
        file_path = f"media/leads/{lead_obj.id}/{lead_attachment.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_content)
    
    # Handle contacts
    if lead_data.contacts is not None:
        lead_obj.contacts.clear()
        if lead_data.contacts:
            contact_objs = Contact.objects.filter(id__in=lead_data.contacts)
            lead_obj.contacts.add(*contact_objs)
    
    # Handle teams
    if lead_data.teams is not None:
        lead_obj.teams.clear()
        if lead_data.teams:
            team_objs = Teams.objects.filter(id__in=lead_data.teams)
            lead_obj.teams.add(*team_objs)
    
    # Handle conversion
    if lead_data.status == "converted":
        # Conversion logic would go here
        pass
    
    # Prepare changed data for audit log
    changed_data = {}
    for field, original_value in original_data.items():
        if field == "assigned_to" and lead_data.assigned_to is not None:
            changed_data[field] = lead_data.assigned_to
        elif field == "tags" and lead_data.tags is not None:
            changed_data[field] = lead_data.tags
        elif hasattr(lead_data, field) and getattr(lead_data, field) is not None and getattr(lead_data, field) != original_value:
            changed_data[field] = getattr(lead_data, field)
    
    # Log the lead update
    AuditLog.objects.create(
        user=user,
        content_type=ContentType.objects.get_for_model(Lead),
        object_id=str(lead_id),
        action="update",
        data={
            "changed_fields": changed_data,
            "has_attachment": bool(lead_attachment)
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")
    )
    
    return {"error": False, "message": "Lead updated Successfully"}

@router.delete("/{lead_id}", response_model=SuccessResponse)
def delete_lead(
    request: Request,
    lead_id: int,
    token_payload: dict = Depends(verify_token)
):
    """
    Delete a lead
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    try:
        lead_obj = Lead.objects.get(id=lead_id)
    except Lead.DoesNotExist:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead_obj.org != profile.org:
        raise HTTPException(
            status_code=403, 
            detail="User company does not match with header"
        )
    
    # Capture lead data before deletion for audit log
    lead_data = {
        "id": lead_obj.id,
        "title": lead_obj.title,
        "email": lead_obj.email,
        "status": lead_obj.status,
        "created_on": str(lead_obj.created_on)
    }
    
    # Permission check
    if profile.role == "ADMIN" or user.is_superuser or user.id == lead_obj.created_by.id:
        lead_obj.delete()
        
        # Log the lead deletion
        AuditLog.objects.create(
            user=user,
            content_type=ContentType.objects.get_for_model(Lead),
            object_id=str(lead_id),
            action="delete",
            data=lead_data,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")
        )
        
        return {"error": False, "message": "Lead deleted Successfully"}
    
    raise HTTPException(
        status_code=403, 
        detail="You don't have permission to delete this lead"
    )

@router.post("/upload", response_model=SuccessResponse)
def upload_leads(
    request: Request,
    file: UploadFile = File(...),
    token_payload: dict = Depends(verify_token)
):
    """
    Upload leads from a file
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    # Validate file
    if not file.filename.endswith(('.xls', '.xlsx', '.csv')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload .xls, .xlsx or .csv file"
        )
    
    # Process file
    file_content = file.read()
    file_path = f"/tmp/{file.filename}"
    
    # Save file temporarily
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Create leads from file (process asynchronously)
    create_lead_from_file.delay(file_path, user.id, profile.org.id)
    
    # Log the bulk upload action
    AuditLog.objects.create(
        user=user,
        content_type=ContentType.objects.get_for_model(Lead),
        object_id="bulk_upload",
        action="create",
        data={
            "filename": file.filename,
            "file_size": file.size
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")
    )
    
    return {"error": False, "message": "Leads uploaded successfully. Processing..."}

@router.put("/comment/{comment_id}", response_model=SuccessResponse)
def update_lead_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    token_payload: dict = Depends(verify_token)
):
    """
    Update a lead comment
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    try:
        comment_obj = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Permission check
    if profile.role == "ADMIN" or user.is_superuser or profile.id == comment_obj.commented_by.id:
        comment_obj.comment = comment_data.comment
        comment_obj.save()
        return {"error": False, "message": "Comment updated successfully"}
    
    raise HTTPException(
        status_code=403, 
        detail="You don't have permission to perform this action"
    )

@router.delete("/comment/{comment_id}", response_model=SuccessResponse)
def delete_lead_comment(
    comment_id: int,
    token_payload: dict = Depends(verify_token)
):
    """
    Delete a lead comment
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    try:
        comment_obj = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Permission check
    if profile.role == "ADMIN" or user.is_superuser or profile.id == comment_obj.commented_by.id:
        comment_obj.delete()
        return {"error": False, "message": "Comment deleted successfully"}
    
    raise HTTPException(
        status_code=403, 
        detail="You don't have permission to perform this action"
    )

@router.delete("/attachment/{attachment_id}", response_model=SuccessResponse)
def delete_lead_attachment(
    attachment_id: int,
    token_payload: dict = Depends(verify_token)
):
    """
    Delete a lead attachment
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    try:
        attachment_obj = Attachments.objects.get(id=attachment_id)
    except Attachments.DoesNotExist:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    # Permission check
    if profile.role == "ADMIN" or user.is_superuser or user.id == attachment_obj.created_by.id:
        # Delete the file if exists
        file_path = f"media/{attachment_obj.attachment}"
        if os.path.exists(file_path):
            os.remove(file_path)
        
        attachment_obj.delete()
        return {"error": False, "message": "Attachment deleted successfully"}
    
    raise HTTPException(
        status_code=403, 
        detail="You don't have permission to perform this action"
    )

@router.post("/site-api", response_model=SuccessResponse)
def create_lead_from_site(
    lead_data: LeadCreate,
    apikey: str
):
    """
    Create a lead from external site
    """
    # Validate API key
    from common.models import APISettings
    try:
        api_setting = APISettings.objects.get(apikey=apikey)
    except APISettings.DoesNotExist:
        raise HTTPException(
            status_code=400,
            detail="Invalid API key"
        )
    
    # Validate required fields
    if not lead_data.email or not lead_data.title:
        raise HTTPException(
            status_code=400,
            detail="Email and title are required fields"
        )
    
    # Create lead
    lead_obj = Lead(
        title=lead_data.title,
        first_name=lead_data.first_name,
        last_name=lead_data.last_name,
        email=lead_data.email,
        phone=lead_data.phone,
        description=lead_data.description,
        status="open",
        source="website",
        org=api_setting.org,
        created_by=api_setting.created_by
    )
    lead_obj.save()
    
    return {"error": False, "message": "Lead created successfully"}

# Company related endpoints

@router.get("/companies", response_model=List[dict])
def get_companies(
    token_payload: dict = Depends(verify_token)
):
    """
    Get list of companies
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    companies = Company.objects.filter(org=profile.org)
    return list(companies.values('id', 'name', 'website', 'created_on'))

@router.post("/companies", response_model=Dict[str, Any])
def create_company(
    company_data: CompanyCreate,
    token_payload: dict = Depends(verify_token)
):
    """
    Create a new company
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    # Check if company already exists
    if Company.objects.filter(name=company_data.name, org=profile.org).exists():
        return {
            "error": True,
            "message": "Company with this name already exists"
        }
    
    # Create company
    company_obj = Company(
        name=company_data.name,
        website=company_data.website,
        address=company_data.address,
        org=profile.org,
        created_by=user
    )
    company_obj.save()
    
    return {
        "error": False,
        "message": "Company created successfully",
        "company_id": company_obj.id
    }

@router.get("/companies/{company_id}", response_model=Dict[str, Any])
def get_company_detail(
    company_id: int,
    token_payload: dict = Depends(verify_token)
):
    """
    Get company details
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {
        "error": False, 
        "data": {
            "id": company.id,
            "name": company.name,
            "website": company.website,
            "address": company.address,
            "created_on": company.created_on
        }
    }

@router.put("/companies/{company_id}", response_model=SuccessResponse)
def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    token_payload: dict = Depends(verify_token)
):
    """
    Update a company
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update company fields
    company.name = company_data.name if company_data.name else company.name
    company.website = company_data.website if company_data.website is not None else company.website
    company.address = company_data.address if company_data.address is not None else company.address
    
    company.save()
    
    return {"error": False, "message": "Company updated successfully"}

@router.delete("/companies/{company_id}", response_model=SuccessResponse)
def delete_company(
    company_id: int,
    token_payload: dict = Depends(verify_token)
):
    """
    Delete a company
    """
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    
    user = User.objects.get(id=user_id)
    profile = Profile.objects.get(user=user)
    
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.delete()
    
    return {"error": False, "message": "Company deleted successfully"}