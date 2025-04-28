from win32com.server import register
from dcom_server.services import RequestProcessor

if __name__ == "__main__":
    register.UseCommandLine(RequestProcessor)
