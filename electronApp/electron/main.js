const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");
const os = require("os");
const { execFile } = require("child_process");

/**
 * Get a safe path for a script.
 * Copies the script to /tmp to ensure it can be executed in AppImage.
 */
function getTempScriptPath(scriptName) {
    const original = app.isPackaged
        ? path.join(process.resourcesPath, "app.asar.unpacked", "scripts", scriptName)
        : path.join(__dirname, "..", "scripts", scriptName);

    if (!fs.existsSync(original)) {
        throw new Error(`Script not found: ${original}`);
    }

    const tempPath = path.join(os.tmpdir(), scriptName);

    // Copy script to temp folder (overwrite if exists)
    fs.copyFileSync(original, tempPath);

    // Make executable on Linux/macOS
    if (process.platform !== "win32") {
        fs.chmodSync(tempPath, 0o755);
    }

    return tempPath;
}

/**
 * Run a script safely and return stdout or reject with stderr.
 * If useRoot is true, tries pkexec on Linux/macOS.
 */
function runScript(scriptName, useRoot = false, args = []) {
    const scriptPath = getTempScriptPath(scriptName);

    return new Promise((resolve, reject) => {
        let command;
        let execArgs = [];

        // ---------- WINDOWS ----------
        if (process.platform === "win32") {
            const pwsh7 = "C:\\Program Files\\PowerShell\\7\\pwsh.exe";
            command = fs.existsSync(pwsh7) ? pwsh7 : "powershell.exe";

            if (useRoot) {
                // Run as admin
                execArgs = [
                    "-NoProfile",
                    "-Command",
                    `Start-Process '${command}' -Verb RunAs -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','${scriptPath}',${args.map(a => `'${a}'`).join(",")}`
                ];
            } else {
                execArgs = [
                    "-NoLogo",
                    "-NoProfile",
                    "-ExecutionPolicy", "Bypass",
                    "-File", scriptPath,
                    ...args
                ];
            }
        }

        // ---------- LINUX ----------
        else if (process.platform === "linux") {
            // Try pkexec
            if (useRoot) {
                command = "pkexec";
                execArgs = ["bash", scriptPath, ...args];
            } else {
                command = "bash";
                execArgs = [scriptPath, ...args];
            }
        }

        // ---------- MACOS ----------
        else if (process.platform === "darwin") {
            if (useRoot) {
                command = "osascript";
                execArgs = [
                    "-e",
                    `do shell script "bash '${scriptPath}' ${args.join(" ")}" with administrator privileges`
                ];
            } else {
                command = "bash";
                execArgs = [scriptPath, ...args];
            }
        }

        execFile(command, execArgs, { env: process.env }, (error, stdout, stderr) => {
            if (error) {
                console.error("Script error:", error);
                console.error("stderr:", stderr);
                return reject(stderr || error.message);
            }
            console.log("Script stdout:", stdout);
            resolve(stdout);
        });
    });
}


function getMainBinPath() {
    if (app.isPackaged) {
        // In AppImage or installer, use app.asar.unpacked
        if (process.platform === "win32") {
            return getTempScriptPath("main.exe");
        }
        return getTempScriptPath("main.bin");
    } else {
        // Development mode (npm start)
        if (process.platform === "win32")
            return path.join(__dirname, "..", "/scripts/main.exe");
        return path.join(__dirname, "..", "/scripts/main.bin");
    }
}


/**
 * Create the main Electron window
 */
function createWindow() {
    const win = new BrowserWindow({
        width: 600,
        height: 650,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
        },
    });

    win.loadFile(path.join(__dirname, "renderer.html"));
}

function scriptForOS(baseName) {
    const platform = process.platform;

    if (platform === "win32") {
        return `${baseName}.ps1`;
    } else {
        return `${baseName}.sh`;
    }
}

// Global OS-specific run
function runOSScript(baseName, useRoot = false, args = []) {
    const scriptName = scriptForOS(baseName);
    return runScript(scriptName, useRoot, args);
}

// IPC handlers
ipcMain.handle("run:add_service", async () => {
    const mainBin = getMainBinPath();
    return runOSScript("add_service", true, [mainBin]);
});

ipcMain.handle("run:delete_service", () => runOSScript("delete_service", true));

ipcMain.handle("run:restart_service", () => runOSScript("restart_service", true));

ipcMain.handle("run:get_ip", () => runOSScript("get_ip"));


// App ready
app.whenReady().then(createWindow);
