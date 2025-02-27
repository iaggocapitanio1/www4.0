from utilities.functions import generate_urn_identifier, serialize_address, build_url
from utilities.geo import normalized_corners
from users.models import CustomerProfile, OrganizationProfile, WorkerProfile
from bucket.models import LeftOverImage
from operations import OrganizationPayload, OwnerPayload, WorkerPayload, LeftoverPayload


def customer_entity(customer: CustomerProfile) -> OwnerPayload:
    if customer.vat is None:
        vat = ''
    else:
        vat = customer.vat
    return OwnerPayload(
        id=generate_urn_identifier(_type='Owner', uid=customer.id),
        legalName=customer.user.first_name,
        givenName=customer.user.first_name,
        familyName=customer.user.last_name,
        vat=vat,
        isCompany=customer.isCompany,
        address=serialize_address(address_instance=customer.address),
        delivery_address=serialize_address(address_instance=customer.delivery_address),
        email=customer.user.email,
        active=customer.user.is_active,
        image=customer.user.picture.__str__(),
        tos=customer.tos
    )


def organization_entity(organization: OrganizationProfile) -> OrganizationPayload:
    return OrganizationPayload(
        id=generate_urn_identifier(_type='Organization', uid=organization.id),
        legalName=organization.user.first_name,
        vat=organization.vat,
        email=organization.user.email,
        active=organization.user.is_active,
    )


def worker_entity(worker: WorkerProfile) -> WorkerPayload:
    return WorkerPayload(
        id=generate_urn_identifier(_type='Worker', uid=worker.id),
        givenName=worker.user.first_name,
        familyName=worker.user.last_name,
        email=worker.user.email,
        active=worker.user.is_active,
        image=worker.user.picture.__str__(),
        hasOrganization=generate_urn_identifier(_type='Organization', uid=worker.hasOrganization.id),
    )


def leftover_entity(leftover: LeftOverImage) -> LeftoverPayload:
    return LeftoverPayload(
        id=generate_urn_identifier(_type='Leftover', uid=leftover.id),
        partName=leftover.id.__str__(),
        material=leftover.klass.__str__(),
        length=leftover.height,
        width=leftover.width,
        thickness=leftover.thickness,
        location_x=leftover.location_x,
        location_y=leftover.location_y,
        dimension=normalized_corners(leftover.corners),
        image=build_url(url=leftover.file.url),
    )
