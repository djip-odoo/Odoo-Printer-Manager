const { app, BrowserWindow, Tray, Menu, ipcMain } = require("electron");
const path = require("path");
const os = require("os");
const { spawn } = require("child_process");

let mainWindow;
let tray;
let serverProcess;

function startServer() {
    let serverPath;

    if (process.platform === "win32") {
        serverPath = path.join(__dirname, "../scripts/main.exe");
    } else {
        serverPath = path.join(__dirname, "../scripts/main");
    }

    serverProcess = spawn(serverPath, [], {
        detached: false
    });

    serverProcess.stdout.on("data", (data) => {
        console.log(`Server: ${data}`);
    });

    serverProcess.stderr.on("data", (data) => {
        console.error(`${data}`);
    });

    serverProcess.on("close", (code) => {
        console.log(`Server exited with code ${code}`);
    });
}

function stopServer() {
    if (serverProcess) {
        serverProcess.kill();
        serverProcess = null;
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 600,
        height: 650,
        show: true,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
        },
    });

    mainWindow.loadFile(path.join(__dirname, "renderer.html"));

    mainWindow.on("close", (event) => {
        if (!app.isQuiting) {
            event.preventDefault();
            mainWindow.hide();
        }
    });
}

app.whenReady().then(() => {

    // Auto start at login
    app.setLoginItemSettings({
        openAtLogin: true
    });

    startServer();

    createWindow();

    tray = new Tray(path.join(__dirname, "icon.jpg"));

    const contextMenu = Menu.buildFromTemplate([
        {
            label: "Open",
            click: () => mainWindow.show()
        },
        {
            label: "Stop Server",
            click: () => stopServer()
        },
        {
            label: "Quit",
            click: () => {
                app.isQuiting = true;
                stopServer();
                app.quit();
            }
        }
    ]);

    tray.setContextMenu(contextMenu);
});

ipcMain.handle("run:add_service", async () => {
    // const mainBin = getMainBinPath();
    // return runOSScript("add_service", true, [mainBin]);
});

ipcMain.handle("run:delete_service", () => {
    console.log("not implemented");
}
);

ipcMain.handle("run:restart_service", () => {
    console.log("not implemented");

}
);

ipcMain.handle("run:get_ip", () => getLocalIP() + ":8089");


app.on("window-all-closed", (e) => {
    e.preventDefault();
});



function getLocalIP() {
    const interfaces = os.networkInterfaces();

    for (const name of Object.keys(interfaces)) {
        for (const iface of interfaces[name]) {
            if (
                iface.family === "IPv4" &&
                !iface.internal
            ) {
                return iface.address;
            }
        }
    }

    return "127.0.0.1";
}
