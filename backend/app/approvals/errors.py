class ApprovalError(RuntimeError):
    status_code = 400

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class ApprovalNotFound(ApprovalError):
    status_code = 404


class ApprovalConflict(ApprovalError):
    status_code = 409
