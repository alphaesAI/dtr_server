"""PAS IG 2.2.1 canonicals and extension URLs used by $submit."""

PAS_VERSION = "2.2.1"
_PAS = "http://hl7.org/fhir/us/davinci-pas/StructureDefinition"

PROFILE_REQUEST_BUNDLE = f"{_PAS}/profile-pas-request-bundle|{PAS_VERSION}"
PROFILE_RESPONSE_BUNDLE = f"{_PAS}/profile-pas-response-bundle|{PAS_VERSION}"
PROFILE_CLAIM_RESPONSE = f"{_PAS}/profile-claimresponse|{PAS_VERSION}"

EXT_ITEM_REQUESTED_SERVICE_DATE = f"{_PAS}/extension-itemRequestedServiceDate"
EXT_ITEM_PREAUTH_ISSUE_DATE = f"{_PAS}/extension-itemPreAuthIssueDate"
EXT_ITEM_PREAUTH_PERIOD = f"{_PAS}/extension-itemPreAuthPeriod"
EXT_ITEM_AUTHORIZED_PROVIDER = f"{_PAS}/extension-itemAuthorizedProvider"
EXT_ITEM_AUTHORIZED_DETAIL = f"{_PAS}/extension-itemAuthorizedDetail"
EXT_REVIEW_ACTION = f"{_PAS}/extension-reviewAction"
EXT_REVIEW_ACTION_CODE = f"{_PAS}/extension-reviewActionCode"

X12_REVIEW_ACTION_SYSTEM = "https://codesystem.x12.org/005010/306"
REVIEW_ACTION_APPROVED = "A1"
REVIEW_ACTION_APPROVED_DISPLAY = "Certified in total"

ADJUDICATION_CATEGORY_SYSTEM = "http://terminology.hl7.org/CodeSystem/adjudication"
ADJUDICATION_SUBMITTED = "submitted"
