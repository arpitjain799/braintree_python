import braintree
import re
from braintree.dispute import Dispute
from braintree.dispute_details import DisputeEvidence
from braintree.error_result import ErrorResult
from braintree.successful_result import SuccessfulResult
from braintree.exceptions.not_found_error import NotFoundError
from braintree.paginated_result import PaginatedResult
from braintree.paginated_collection import PaginatedCollection
from braintree.resource_collection import ResourceCollection

class DisputeGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def accept(self, dispute_id):
        try:
            if dispute_id is None or dispute_id.strip() == "":
                raise NotFoundError()

            response = self.config.http().put(self.config.base_merchant_path() + "/disputes/" + dispute_id + "/accept")

            if "api_error_response" in response:
                return ErrorResult(self.gateway, response["api_error_response"])
            else:
                return SuccessfulResult()
        except NotFoundError:
            raise NotFoundError("dispute with id " + repr(dispute_id) + " not found")

    def add_file_evidence(self, dispute_id, document_upload_id):
        try:
            if dispute_id is None or dispute_id.strip() == "":
                raise NotFoundError()
            if document_upload_id is None or document_upload_id.strip() == "":
                raise ValueError("document_id cannot be blank")

            response = self.config.http().post(self.config.base_merchant_path() + "/disputes/" + dispute_id + "/evidence", {
                "document_upload_id": document_upload_id
            })

            if "evidence" in response:
                return SuccessfulResult({
                    "evidence": DisputeEvidence(response["evidence"])
                })
            elif "api_error_response" in response:
                return ErrorResult(self.gateway, response["api_error_response"])

        except NotFoundError:
            raise NotFoundError("dispute with id " + repr(dispute_id) + " not found")

    def add_text_evidence(self, dispute_id, content_or_request):
        request = content_or_request if isinstance(content_or_request, dict) else { "content": content_or_request }

        if dispute_id is None or dispute_id.strip() == "":
            raise NotFoundError("dispute_id cannot be blank")
        if request.get("content") is None or request["content"].strip() == "":
            raise ValueError("content cannot be blank")

        try:
            if request.get("sequence_number") is not None:
                request["sequence_number"] = int(request["sequence_number"])
        except ValueError:
            raise ValueError("sequence_number must be an integer")

        if request.get("tag") is not None and not isinstance(request["tag"], str):
            raise ValueError("tag must be a string")

        try:
            response = self.config.http().post(self.config.base_merchant_path() + "/disputes/" + dispute_id + "/evidence", {
                "evidence": {
                    "comments": request.get("content"),
                    "category": request.get("tag"),
                    "sequence_number": request.get("sequence_number")
                }
            })

            if "evidence" in response:
                return SuccessfulResult({
                    "evidence": DisputeEvidence(response["evidence"])
                })
            elif "api_error_response" in response:
                return ErrorResult(self.gateway, response["api_error_response"])
        except NotFoundError:
            raise NotFoundError("Dispute with ID " + repr(dispute_id) + " not found")

    def finalize(self, dispute_id):
        try:
            if dispute_id is None or dispute_id.strip() == "":
                raise NotFoundError()

            response = self.config.http().put(self.config.base_merchant_path() + "/disputes/" + dispute_id + "/finalize")

            if "api_error_response" in response:
                return ErrorResult(self.gateway, response["api_error_response"])
            else:
                return SuccessfulResult()
        except NotFoundError:
            raise NotFoundError("dispute with id " + repr(dispute_id) + " not found")

    def find(self, dispute_id):
        try:
            if dispute_id is None or dispute_id.strip() == "":
                raise NotFoundError()

            response = self.config.http().get(self.config.base_merchant_path() + "/disputes/" + dispute_id)
            return Dispute(response["dispute"])
        except NotFoundError:
            raise NotFoundError("dispute with id " + repr(dispute_id) + " not found")

    def remove_evidence(self, dispute_id, evidence_id):
        try:
            if dispute_id is None or dispute_id.strip() == "":
                raise NotFoundError()
            if evidence_id is None or evidence_id.strip() == "":
                raise NotFoundError()

            response = self.config.http().delete(self.config.base_merchant_path() + "/disputes/" + dispute_id + "/evidence/" + evidence_id)

            if "api_error_response" in response:
                return ErrorResult(self.gateway, response["api_error_response"])
            else:
                return SuccessfulResult()
        except NotFoundError:
            raise NotFoundError("evidence with id " + repr(evidence_id) + " for dispute with id " + repr(dispute_id) + " not found")

    def search(self, *query):
        if isinstance(query[0], list):
            query = query[0]

        self.search_criteria = self.__criteria(query)

        pc = PaginatedCollection(self.__fetch_disputes)
        return SuccessfulResult({"disputes": pc})

    def __fetch_disputes(self, page):
        response = self.config.http().post(self.config.base_merchant_path() + "/disputes/advanced_search?page=" + str(page), {"search": self.search_criteria})
        body = response["disputes"]

        disputes = [Dispute(item) for item in ResourceCollection._extract_as_array(response["disputes"], "dispute")]
        return PaginatedResult(body["total_items"], body["page_size"], disputes)

    def __criteria(self, query):
        criteria = {}

        for term in query:
            if criteria.get(term.name):
                criteria[term.name] = dict(list(criteria[term.name].items()) + list(term.to_param().items()))
            else:
                criteria[term.name] = term.to_param()
        return criteria
