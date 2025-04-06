from pydantic import BaseModel
from django.core.exceptions import ValidationError
from fastapi import APIRouter, Depends, HTTPException, status
from apiv2.utils import verify_token
from common.models import Profile, User, Org, AuditLog
from django.contrib.contenttypes.models import ContentType

router = APIRouter()
# You can update tokenUrl to match an actual token endpoint if needed

class OrgCreate(BaseModel):
    org_name: str


@router.get("/", summary="List all orgs")
def list_products(token_payload: dict = Depends(verify_token)):
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )
    user = User.objects.get(id=user_id)
    profiles = Profile.objects.filter(user=user)
    profiles_serialized = list(profiles.values('org_id', 'role'))  # Convert queryset to list of dicts
    org = Org.objects.filter(id__in=[profile['org_id'] for profile in profiles_serialized])
    org_serialized = list(org.values('id', 'name'))
    print(org_serialized)
    return {
        "orgs": org_serialized,
    }


@router.post("/", summary="Create orgs")
def create_org(org_data: OrgCreate, token_payload: dict = Depends(verify_token)):
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID missing in token payload"
        )

    user = User.objects.get(id=user_id)
    org = Org(name=org_data.org_name, created_by=user, updated_by=user)
    
    try:
        org.full_clean()  
    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ve.message_dict
        )
    
    org.save()
    Profile.objects.create(user=user, org=org, role="ADMIN")
    
    # Create an audit log entry
    AuditLog.objects.create(
        user=user,
        content_type=ContentType.objects.get_for_model(Org),
        object_id=org.id,
        action="create",
        data={"org_name": org_data.org_name},
        ip_address=token_payload.get("ip_address"),
        user_agent=token_payload.get("user_agent"),
    )
    
    return {"org": org}
