#include <iostream>
#include <windows.h>
#include <filesystem>
#include <vector>

// idek what this is but i trust it
constexpr unsigned long hash(const char* str) {
	unsigned long h = 5381;
	while (*str)
		h = ((h << 5) + h) + *str++;
	return h;
}

bool isTerminalLaunch()
{
	HWND console = GetConsoleWindow();
	if (!console) return false;

	DWORD pid = 0;
	GetWindowThreadProcessId(console, &pid);

	return pid != 0;
}

void help() {
	std::cout <<
		"Usage: mariactl [options]\n" <<
		"Options: start, stop, status, install, uninstall\n" <<
		"Start: Start the MariaDB service\n" <<
		"Stop: Stop the MariaDB service\n" <<
		"Status: Check the status of the MariaDB service\n" <<
		"Install: Install the MariaDB service to SC\n" <<
		"Uninstall or Remove: Uninstall the MariaDB service from SC\n\n" <<
		"Example: mariactl start\n" << std::endl;
}

int start(SC_HANDLE handle) {
	SC_HANDLE  service = ::OpenServiceA(handle, "MySQL", SERVICE_START | SERVICE_QUERY_STATUS);

	if (!service) {
		return 1;
	}

	if (!::StartServiceA(service, 0, NULL)) {
		std::cerr << "Failed to start service: " << GetLastError() << std::endl;
		CloseServiceHandle(service);
		return 1;
	}
	else {
		std::cout << "Service started successfully." << std::endl;
	}

	CloseServiceHandle(service);
	return 0;
}

int waitForStop(SC_HANDLE service)
{
	SERVICE_STATUS status{};

	// send stop
	ControlService(service, SERVICE_CONTROL_STOP, &status);

	// poll until actually stopped
	while (true)
	{
		if (!QueryServiceStatus(service, &status))
			return 1;

		if (status.dwCurrentState == SERVICE_STOPPED)
			break;

		if (status.dwCurrentState == SERVICE_STOP_PENDING)
			Sleep(300);
		else
			Sleep(100);
	}

	return 0;
}

int stop(SC_HANDLE handle) {
	SC_HANDLE  service = ::OpenServiceA(handle, "MySQL", SERVICE_STOP);

	if (!service) {
		return 1;
	}

	SERVICE_STATUS status;

	if (!ControlService(service, SERVICE_CONTROL_STOP, &status)) {
		std::cout << "Failed to send stop signal" << std::endl;
		CloseServiceHandle(service);
		return false;
	}

	int res = waitForStop(service);

	CloseServiceHandle(service);
	return res;
}

int install() {
	std::string cwd = std::filesystem::current_path().string();

	STARTUPINFOA si{};
	PROCESS_INFORMATION pi{};

	// IMPORTANT: mutable command line + quoted exe path
	std::string cmdStr =
		"\".\\bin\\mariadbd.exe\" --install-manual MySQL";

	// CreateProcess requires mutable buffer
	std::vector<char> cmdLine(cmdStr.begin(), cmdStr.end());
	cmdLine.push_back('\0');

	BOOL success = CreateProcessA(
		NULL,
		cmdLine.data(),
		NULL,
		NULL,
		FALSE,
		CREATE_NO_WINDOW,
		NULL,
		cwd.c_str(),
		&si,
		&pi
	);

	if (!success) {
		std::cout << "CreateProcess failed: " << GetLastError() << std::endl;
		return 1;
	}

	// Wait for install to finish (optional but useful)
	WaitForSingleObject(pi.hProcess, INFINITE);

	CloseHandle(pi.hProcess);
	CloseHandle(pi.hThread);

	return 0;
}

int remove() {

	SC_HANDLE scm = OpenSCManagerA(
		NULL,
		NULL,
		SC_MANAGER_ALL_ACCESS
	);

	if (!scm) {
		std::cout << "OpenSCManager failed: " << GetLastError() << std::endl;
		return 1;
	}

	SC_HANDLE service = OpenServiceA(
		scm,
		"MySQL",
		DELETE | SERVICE_STOP | SERVICE_QUERY_STATUS
	);

	if (!service) {
		std::cout << "OpenService failed: " << GetLastError() << std::endl;
		return 1;
	}

	// Try stopping service first (important)
	SERVICE_STATUS status{};
	ControlService(service, SERVICE_CONTROL_STOP, &status);

	Sleep(1000);

	// Delete service
	if (!DeleteService(service)) {
		std::cout << "DeleteService failed: " << GetLastError() << std::endl;
		return 1;
	}

	std::cout << "Service deleted successfully.\n" << std::endl;

	CloseServiceHandle(service);
	return 0;
}

int main(int argc, char* argv[]) {
	
	if (!isTerminalLaunch()) {
		::ShowWindow(::GetConsoleWindow(), SW_HIDE);
	}

	if (argc != 2) {
		help();
		return 0;
	}

	std::string command = argv[1];
	SC_HANDLE mgr = OpenSCManagerA(NULL, NULL, SC_MANAGER_ALL_ACCESS);

	switch (hash(command.c_str())) {
	case hash("start"):
		std::cout << "Starting MariaDB service..." << std::endl;
		start(mgr);
		break;

	case hash("stop"):
		std::cout << "Stopping MariaDB service..." << std::endl;
		stop(mgr);
		break;

	case hash("install"):
		std::cout << "Installing MariaDB service..." << std::endl;
		install();
		break;

	case hash("uninstall"):
	case hash("remove"):
		std::cout << "Uninstalling MariaDB service..." << std::endl;
		remove();
		break;

	default:
		std::cerr << "Unknown command: " << command << std::endl;
		help();
		return 1;
	}

	if (mgr) CloseServiceHandle(mgr);

	return 0;
}