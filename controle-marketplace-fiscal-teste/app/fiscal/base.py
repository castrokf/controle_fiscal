from abc import ABC, abstractmethod


class FiscalProvider(ABC):
    @abstractmethod
    def issue_invoice(self, order):
        raise NotImplementedError

    @abstractmethod
    def get_invoice_status(self, invoice):
        raise NotImplementedError

    @abstractmethod
    def download_xml(self, invoice):
        raise NotImplementedError

    @abstractmethod
    def download_pdf(self, invoice):
        raise NotImplementedError
