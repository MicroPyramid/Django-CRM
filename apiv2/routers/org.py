# fastapi_app/routers/products.py
from fastapi import APIRouter, Depends, HTTPException, status
from apiv2.utils import verify_token
from common.models import Profile, User, Org

router = APIRouter()
# You can update tokenUrl to match an actual token endpoint if needed
from pydantic import BaseModel

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
    
    # Use the org_name from the posted data to create the org
    org = Org.objects.create(name=org_data.org_name)
    Profile.objects.create(user=user, org=org, role="ADMIN")
    
    return {"org": org}
