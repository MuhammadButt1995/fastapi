# Talos Application Windows/DaaS Packaging

This guide will walk you through the steps to package the Talos application for Windows physical and DaaS devices.

1. **Stop the FMInfo Executable**: Ensure that the `FMInfo.exe` executable isn't running. Close it if it is currently active. The executable lives in this directory:

   ```
   [Your FilePath Here]
   ```

2. **Remove FMInfo Shortcut**: The FMInfo.exe is launched automatically on user login via a shortcut in the startup folder. Navigate to the following file path and delete the `fminfo` shortcut:

   ```
   [Your FilePath Here]
   ```

3. **Delete FMInfo Directory**: Navigate back to the directory that the Fminfo.exe resides in (from step 1) delete the 4 following files: `FMinfo.exe`, `FMInfo.exe.config`, `FMInfoNew8.txt`, and `record.ico`

4. **Create New Directories**: Create the following directories under the `path` path:

   - `Talos/app`
   - `Talos/server`

5. **Copy Talos Executable**: Transfer the `Talos` executable into the `Talos/app` directory.

6. **Copy Python Server**: Move the python server files into the `Talos/server` directory.

7. **Setup the Python Environment**:
   - Open PowerShell.
   - Change directory to the server folder:
     ```powershell
     cd Talos/Server
     ```
   - Execute the following commands in sequence:
     ```powershell
     py -3 -m venv venv
     .\venv\Scripts\Activate.ps1
     pip install -r requirements.txt
     ```

## Daily Usage

Upon every user login, perform these steps to launch the Talos services:

1. **Launch the Talos Server**:

   - Change directory to the server folder:
     ```powershell
     cd Talos/Server
     ```
   - Start the server with the command:
     ```powershell
     uvicorn main:app
     ```

2. **Launch the Talos Executable**:
   - Navigate to the app folder:
     ```powershell
     cd Talos/App
     ```
   - Run the executable:
     ```powershell
     ./talos.exe
     ```

Follow these instructions diligently for smooth operation of the Talos application. If you encounter any issues, refer to the troubleshooting section or contact the support team.
